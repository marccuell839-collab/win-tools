# JARVIS — Yacine's personal desktop agent

Windows desktop assistant in Python / PySide6, with an animated cyan orbital interface, concise Arabic replies, screenshot-aware computer control and a system tray background mode.

## Download and run

Open **Actions → Build JARVIS Windows → latest successful run → Artifacts → JARVIS-Windows-x64**. Extract the ZIP completely and run `JARVIS/JARVIS.exe`. Python is not needed for the built app. The executable is unsigned; verify its source before running. Windows 10/11 x64 is the intended platform. Windows permissions/UAC and lock screens cannot be bypassed.

1. Open Settings and enter your OpenRouter API key. The default `openrouter/free` route uses free models; availability and rate limits still apply. Paid model routes are rejected.
2. Edge TTS reads replies without an API key. Default male voice: `ar-DZ-IsmaelNeural`; Saudi, Egyptian and English male alternatives are available. Voice availability is checked at synthesis, with an Arabic Hamed fallback.
3. Optional microphone: add a Deepgram key, click Record, speak, then Stop recording. Review the transcript and press Execute. Deepgram STT can consume credit; Edge TTS does not transcribe speech.
4. Enable the session screenshot permission before submitting commands. Review every proposed click, typing operation, hotkey or URL before it runs. The UI hides after approval to return focus to the target. Avoid moving windows while an action is pending.
5. Close hides to the tray. The tray has Show / Stop / Quit. **Ctrl+Alt+Esc** interrupts the agent; moving the pointer to the top-left triggers PyAutoGUI's fail-safe. Stop does not undo an already completed click or cancel a request already sent to a cloud service.

## What works

- Multi-step model tool calling, screenshots after each approved action, up to 12 steps per request.
- Primary-monitor click, double click, pointer move, bounded scroll, Unicode paste, key combinations, HTTP(S) URL opening.
- Three voice prosody presets: serious, calm, energetic (speed and pitch, not full emotional synthesis).
- Background tray, explicit microphone recording up to 30 seconds, concise conversation, bounded in-memory history.
- Keys in OS keyring / Windows Credential Manager; settings contain no API secrets. No persisted conversations or screenshots. Temporary speech files are cleaned on next playback / exit.
- No local LLM, browser runtime or heavyweight model download. Qt itself still has a meaningful installation size. Portable directory packaging avoids repeated single-file unpacking.

## Limits and privacy

This is a first implementation, not unrestricted autonomous control. Each mutation requires confirmation. It cannot operate locked desktops, UAC prompts, or reliably automate every application. Primary monitor only. Free models vary in vision/tool reliability. There is no always-listening wake word and no automatic startup installation in this version.

Enabling screen access sends screenshots to OpenRouter and its selected model provider. Microphone recordings go to Deepgram only when you request transcription. Spoken reply text goes to Microsoft's online Edge speech service. Cloud services require internet. The `edge-tts` project does not require a key, but its service can change or be unavailable. Text interaction remains available if voice fails. Never show private material while permitting screenshots.

## Development

```powershell
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Tests and packaging:

```powershell
pip install pytest pyinstaller
python -m pytest -q
python -m tests.smoke_ui
pyinstaller --noconfirm --windowed --onedir --name JARVIS --collect-all edge_tts --hidden-import keyring.backends.Windows --hidden-import pynput.keyboard._win32 --hidden-import pynput.mouse._win32 main.py
```

API keys are supplied by the user after installation, never included in builds. Live OpenRouter / Deepgram calls and full Windows desktop behavior require testing on the owner's PC. CI tests policy validation and mocked agent execution, renders the interface, then packages Windows binaries.

References: https://github.com/rany2/edge-tts · https://openrouter.ai/openrouter/free · https://developers.deepgram.com/docs/models-languages-overview
