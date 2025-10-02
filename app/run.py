# app/main.py
from const import HOST, PORT
import uvicorn
import warnings


# ignore torch.utils._pytree._register_pytree_node, torch.nn.utils.weight_norm deprecated warning
warnings.filterwarnings("ignore", category=UserWarning)
# ignore transformer warning. upgrade transformer version to 4.42.3
warnings.filterwarnings("ignore", category=FutureWarning) 


# 라우터 등록
# app.include_router(inference.router, prefix="/api", tags=["inference"])

if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=False, log_level="critical")