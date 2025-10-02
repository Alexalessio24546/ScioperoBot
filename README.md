# ScioperoBot

Bot Telegram per monitorare scioperi (Adriabus, PA, UniUrb).

## Deploy su Render

1. Forka o carica questo repo su GitHub
2. Su [Render](https://render.com) → "New Web Service"
3. Collega il repo
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `python main.py`
6. Environment Variables:
   - `BOT_TOKEN` = il token del tuo bot
   - `CHAT_ID` = il tuo chat_id (opzionale)
7. Dopo il deploy, registra il webhook:

