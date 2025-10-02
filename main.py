import os, re, json, requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from flask import Flask, request

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")  # opzionale

def send_telegram(msg, chat_id=CHAT_ID):
    if not chat_id:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": msg}
    requests.post(url, data=payload)

def parse_dates(text):
    matches = re.findall(r"\d{1,2} ottobre", text.lower())
    return sorted(set(int(d.split()[0]) for d in matches))

def check_adriabus():
    url = "https://www.adriabus.eu/10015-2/"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    content = soup.find("div", class_="entry-content")
    if content:
        text = content.text.strip()
        dates = parse_dates(text)
        return f"🚌 Adriabus:\n{', '.join(str(d)+' ottobre' for d in dates)}\n🔗 {url}", dates
    return "🚌 Nessun sciopero Adriabus rilevato.", []

def check_cruscotto():
    url = "https://quifinanza.it/info-utili/scioperi/scioperi-ottobre-2025-calendario/930702/"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    text = soup.get_text()
    dates = parse_dates(text)
    return f"📅 Scioperi PA:\n{', '.join(str(d)+' ottobre' for d in dates)}\n🔗 {url}", dates

def check_uniurb():
    url = "https://blog.uniurb.it"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    posts = soup.find_all("article")
    for post in posts:
        title = post.find("h2")
        if title and "sciopero" in title.text.lower():
            link = title.find("a")["href"]
            return f"🎓 UniUrb:\n{title.text.strip()}\n🔗 {link}"
    return "🎓 Nessun avviso di sciopero universitario rilevato."

def full_report():
    a, _ = check_adriabus()
    c, _ = check_cruscotto()
    u = check_uniurb()
    return f"{a}\n\n{c}\n\n{u}"

def next_strike():
    a, da = check_adriabus()
    c, dc = check_cruscotto()
    all_dates = sorted(set(da + dc))
    today = datetime.now().day
    future = [d for d in all_dates if d >= today]
    if future:
        return f"🔔 Prossimo sciopero: {future[0]} ottobre"
    return "✅ Nessun sciopero imminente rilevato."

def strikes_on_day(day):
    _, da = check_adriabus()
    _, dc = check_cruscotto()
    hits = [d for d in da + dc if d == day]
    if hits:
        return f"📆 Scioperi il {day} ottobre: {len(hits)} fonte/i"
    return f"✅ Nessun sciopero rilevato il {day} ottobre."

def strikes_today():
    return strikes_on_day(datetime.now().day)

def strikes_tomorrow():
    return strikes_on_day((datetime.now() + timedelta(days=1)).day)

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot attivo su Render!"

@app.route('/ping')
def ping():
    return "✅ Bot sveglio"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print("📩 Webhook ricevuto:", json.dumps(data, indent=2))

    if 'message' in data and 'text' in data['message']:
        msg = data['message']
        chat_id = msg['chat']['id']
        text = msg['text'].strip().lower()

        if text == '/status':
            send_telegram(full_report(), chat_id)
        elif text == '/next':
            send_telegram(next_strike(), chat_id)
        elif text == '/oggi':
            send_telegram(strikes_today(), chat_id)
        elif text == '/domani':
            send_telegram(strikes_tomorrow(), chat_id)
        elif text == '/universita':
            send_telegram(check_uniurb(), chat_id)
        elif text == '/trasporti':
            a, _ = check_adriabus()
            send_telegram(a, chat_id)
        elif text.startswith('/scioperi '):
            try:
                giorno = int(text.split()[1])
                send_telegram(strikes_on_day(giorno), chat_id)
            except:
                send_telegram("❌ Usa il formato: /scioperi <numero giorno>", chat_id)
        elif text == '/help':
            send_telegram(
                "📘 Comandi disponibili:\n"
                "/status → Report completo\n"
                "/next → Prossimo sciopero\n"
                "/oggi → Scioperi in corso oggi\n"
                "/domani → Scioperi previsti domani\n"
                "/universita → Avvisi UniUrb\n"
                "/trasporti → Scioperi Adriabus\n"
                "/scioperi <giorno> → Scioperi in una data\n"
                "/debug → Ultimo messaggio ricevuto\n"
                "/help → Elenco comandi\n",
                chat_id
            )
        elif text == '/debug':
            info = {
                "chat_id": chat_id,
                "username": msg['from'].get('username', 'N/A'),
                "text": msg.get('text', 'N/A'),
                "timestamp": msg['date']
            }
            send_telegram(f"🧪 DEBUG:\n{json.dumps(info, indent=2)}", chat_id)
        else:
            send_telegram("❓ Comando non riconosciuto. Usa /help per vedere i comandi disponibili.", chat_id)

    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
