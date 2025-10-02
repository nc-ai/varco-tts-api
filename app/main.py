from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
from logger import setup_logger  # setup_logger가 있는 모듈
from const import API_VERSION, MODEL_PATH
from schema import Reqinvocations
from scipy.io.wavfile import write
from datetime import datetime
import asyncio
import time
import io
# from .routers import inference

# 로거 생성
Logger = setup_logger()



async def lifespan(app: FastAPI):
    Logger.info(f"server initializing....")
    # 모델 로드를 백그라운드로 실행
    asyncio.create_task(init_model(app))
    Logger.info("server started.")
    yield
    Logger.info(f"server stopped.")
    
def load_model_sync(model_path):
    from nctts_onnx import synthesizer
    return synthesizer.Syntheseizer(model_path=model_path)
    
async def init_model(app: FastAPI):
    Logger.info("model loading in background...")
    try:
        app.synthesizer = await asyncio.to_thread(load_model_sync, MODEL_PATH)
        Logger.info("model loaded successfully!")
    except Exception as e:
        Logger.error("model load failed.")
    
        
app = FastAPI(
    lifespan=lifespan,
    title="NCAI TTS API For AWS Marketplace",
    version=API_VERSION)


@app.get("/ping")
async def ping():
    """
    Health check endpoint.
    """
    return {"status": "OK"}

@app.post("/invocations")
async def invocations(req:Reqinvocations):
    if not hasattr(app, "synthesizer"):
        # 503 code: Service Unavailable
        raise HTTPException(status_code=503, detail="Model is still loading. Try again later.")
    try:
        start_time = time.time()
        wav, sr = app.synthesizer.infer(req.voice_id, req.language, req.text, req.emotion)
        buf = io.BytesIO()
        write(buf, sr, wav)
        buf.seek(0)
        latency = round(time.time() - start_time, 3)  # 초 단위, 소수 3자리
        Logger.info(f"/invocations - Completed.")
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return StreamingResponse(
                    buf,
                    media_type="audio/wav",
                    headers={"Content-Disposition": f'attachment; filename="{timestamp}.wav"'}
                )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        e_msg = str(e)
        Logger.error(f"/invocations - Internal Server Error")
        raise HTTPException(status_code=500, detail="Internal Server Error")