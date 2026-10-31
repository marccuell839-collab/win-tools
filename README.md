# VoiceForge — Android voice studio

Android client for voice recording, prompted reading, Arabic/French/English text, and synthesized WAV playback. The app does **not** need a personal computer, but the included Chatterbox backend requires GPU/CPU compute **somewhere**. To use voice cloning from your phone only, deploy the backend to a hosted GPU environment, configure an HTTPS endpoint in the Android app, and keep it private with authentication. A fully on-device voice-cloning model has **not** been integrated yet.

Build APK from GitHub Actions on the voiceforge-app branch. Download the voiceforge-debug artifact when the run succeeds. Python server is optional deployment source for a hosted service. The current server is a prototype; do not expose it publicly without TLS, authorization, rate limits, and resource quotas. Voice samples and generated files are sensitive personal data. Use only your own voice or voices with informed consent.

Current limitations: no verified APK build yet; backend inference untested; basic expressive slider does not guarantee specific emotions; server upload endpoint is not production-hardened.
