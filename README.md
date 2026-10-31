# VoiceForge — Arabic-first AI Voice Clone Studio
Android app + private self-hosted Chatterbox Multilingual V3 Python backend. Read prompted scripts, record a WAV sample, type new text and generate WAV speech in your own voice. Tone slider maps to exaggeration; voice fidelity varies.

Run backend with Python 3.11: cd server && pip install -r requirements.txt && python -m uvicorn main:app --host 0.0.0.0 --port 8000

In app set http://PC-LAN-IP:8000 (emulator: http://10.0.2.2:8000). Keep LAN private: endpoint is HTTP only for development. Model weights downloaded on first launch. Do not deploy publicly without TLS/authentication/rate limits. Only clone voices with explicit consent.

Build: gradle :app:assembleDebug or GitHub Actions on branch voiceforge-app. Full enhanced source with WAV playback and sharing available as a ZIP in the associated ChatGPT conversation.