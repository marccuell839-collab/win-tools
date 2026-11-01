import io
import wave
import httpx
import numpy as np


def transcribe(key, pcm, language='ar'):
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(pcm)
    r = httpx.post('https://api.deepgram.com/v1/listen',
        params={'model': 'nova-3', 'language': language, 'smart_format': 'true'},
        headers={'Authorization': f'Token {key}', 'Content-Type': 'audio/wav'},
        content=buf.getvalue(), timeout=45)
    if r.is_error: raise RuntimeError(f'Deepgram transcription HTTP {r.status_code}; check key and quota.')
    return r.json()['results']['channels'][0]['alternatives'][0]['transcript']


def speak(key, text, voice, stopped):
    import sounddevice as sd
    if stopped.is_set(): return
    r = httpx.post('https://api.deepgram.com/v1/speak',
        params={'model': voice, 'encoding': 'linear16', 'container': 'none', 'sample_rate': 24000},
        headers={'Authorization': f'Token {key}'}, json={'text': text[:1800]}, timeout=45)
    if r.is_error: raise RuntimeError(f'Deepgram voice HTTP {r.status_code}; check key and quota.')
    if stopped.is_set(): return
    sd.play(np.frombuffer(r.content, dtype=np.int16), 24000)
    sd.wait()


def edge_synthesize(text, voice, tone):
    import asyncio
    import tempfile
    from pathlib import Path
    import edge_tts
    presets = {'serious': ('-8%', '-8Hz'), 'calm': ('-15%', '-4Hz'), 'energetic': ('+8%', '+2Hz')}
    rate, pitch = presets.get(tone, presets['serious'])
    async def generate():
        voices = await edge_tts.list_voices()
        names = {v['ShortName'] for v in voices}
        selected = voice if voice in names else 'ar-SA-HamedNeural'
        if selected not in names:
            raise RuntimeError('Selected Edge voice unavailable; select a different voice.')
        fd, path = tempfile.mkstemp(prefix='jarvis-', suffix='.mp3')
        import os
        os.close(fd)
        try:
            await edge_tts.Communicate(text[:1800], selected, rate=rate, pitch=pitch).save(path)
            return path
        except Exception:
            Path(path).unlink(missing_ok=True)
            raise
    return asyncio.run(asyncio.wait_for(generate(), timeout=45))
