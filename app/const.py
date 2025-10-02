import os

# API VERSION
API_VERSION =  os.getenv("API_VERSION", "0.0.0")
# 서버 설정
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

# NCTTS 모델 경로
MODEL_PATH = os.getenv("MODEL_PATH", "model/tts")

MAX_TTS_TEXT_LEN = int(os.getenv("MAX_TTS_TEXT_LEN",400))
