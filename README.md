# JARVIS — Voice-first desktop assistant

A black PySide6 window containing only an animated orbital core and a Settings button. Windows 10/11 x64; Edge TTS male Arabic speech without a speech-output API key; OpenRouter free models; optional continuous Deepgram microphone streaming.

## Install

Download **JARVIS-Windows-x64** from the latest successful GitHub Actions run. Extract the entire ZIP and run `JARVIS.exe` beside its `_internal` directory. No Python installation is required.

## Setup

Open the gear at the top, or press Ctrl+,.

- **Intelligence and vision:** enter OpenRouter key, choose `openrouter/free` or a `:free` model. Enable vision to allow screenshots to be sent to OpenRouter and its model provider. With vision off, text conversation works without screenshots or desktop tools.
- **Voice and listening:** enter Deepgram key and explicitly enable continuous listening. Choose microphone, voice, language, tone and conversation timeout. Edge TTS output needs internet, but no key. Deepgram listening consumes quota/credit and is not guaranteed free.
- **Interface and controls:** startup greeting, reduced motion, always-on-top, resume or stop listening.
- **Conversation and log:** type commands, see responses and errors, clear conversation.

## Voice flow

Say **جارفيس** / **Jarvis**. It answers **نعم سيدي** and listens for your next command. You can continue talking after its reply until the configured inactivity timeout. Say **شكرا جارفيس** or **انتهينا** to return to wake-word waiting. Startup plays the requested greeting if voice credentials/listening are configured, otherwise asks you to complete setup. The greeting is not a remote service health check.

The wake word is detected in Deepgram transcripts, not by an offline wake-word model. While listening is enabled, microphone audio is sent to Deepgram even before the wake word. The microphone stream is closed during speech playback, agent execution and settings. This prevents self-triggering but means voice interruption is unavailable while busy. Ctrl+Alt+Esc always requests stop; use tray/settings to resume. Recognition quality depends on the microphone, language and service; live wake-word accuracy has not been verified on the owner's PC.

## Vision and control

When vision is enabled, the assistant captures the primary display before reasoning and after approved actions. JARVIS hides briefly so it sees your applications rather than its own window. This is request-driven screen vision, not a continuous video stream. Only visible primary-monitor content is available. Free route vision/tool availability can vary.

Click, double-click, pointer movement, scrolling, Unicode paste, hotkeys and web URLs are supported. Each mutation requires confirmation. The assistant cannot bypass UAC, operate locked desktops or guarantee correct interpretation of every application. Stop does not undo completed actions. Screenshot/page text is treated as untrusted content. Keys are stored in the OS keyring; transcripts and images are not persisted as files. Logs and short conversation history live in memory. Generated speech uses temporary MP3 files.

F11 toggles fullscreen. Closing hides to the system tray. Ctrl+Alt+Esc stops listening, pending commands, speech and the agent. Tray includes Show, Settings, Resume, Stop and Quit.

## Development

```powershell
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt pytest pyinstaller
python -m pytest -q
python -m tests.smoke_ui
python main.py
```

CI runs policy/vision/wake parser tests and a native Qt smoke test, then packages the portable Windows app. API calls, microphone hardware, live voice accuracy and automation of the owner's applications still need on-device testing.
