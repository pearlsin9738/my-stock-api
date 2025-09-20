from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import akshare as ak

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/tech")
def get_tech(code: str = "000001"):
    try:
        df = ak.stock_zh_a_hist(symbol=code, period="daily").tail(30)
        if df.empty:
            return {"error": "market closed or invalid code"}
        # 统一用第一列做日期，第3列做收盘价
        date = df.iloc[-1, 0]
        close = df.iloc[-1, 3]
        return {"code": code, "update": str(date), "close": float(close)}
    except Exception as e:
        return {"error": str(e)}
