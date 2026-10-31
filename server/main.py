"""Private LAN zero-shot Arabic voice cloning server."""
import os, io, tempfile
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool
model=None
@asynccontextmanager
async def lifespan(app):
 global model
 import torch
 from chatterbox.mtl_tts import ChatterboxMultilingualTTS
 model=ChatterboxMultilingualTTS.from_pretrained(device='cuda' if torch.cuda.is_available() else 'cpu',t3_model='v3')
 yield
 model=None
app=FastAPI(lifespan=lifespan)
@app.get('/health')
def health(): return {'ready':model is not None}
@app.post('/synthesize')
async def synthesize(text:str=Form(...),language:str=Form('ar'),exaggeration:float=Form(.5),audio:UploadFile=File(...)):
 if not 0<len(text)<=1500 or language not in ('ar','en','fr') or not .2<=exaggeration<=.9: raise HTTPException(400,'Invalid parameters')
 raw=await audio.read(5000001)
 if len(raw)>5000000 or not raw.startswith(b'RIFF') or raw[8:12]!=b'WAVE':raise HTTPException(400,'Need WAV under 5MB')
 def work():
  import torchaudio
  with tempfile.NamedTemporaryFile(delete=False,suffix='.wav') as f:
   f.write(raw); path=f.name
  try:
   wav=model.generate(text,language_id=language,audio_prompt_path=path,exaggeration=exaggeration)
   result=io.BytesIO()
   torchaudio.save(result,wav.cpu(),model.sr,format='wav')
   result.seek(0)
   return result
  finally:os.unlink(path)
 try: data=await run_in_threadpool(work)
 except Exception as e:raise HTTPException(500,type(e).__name__)
 return StreamingResponse(data,media_type='audio/wav')