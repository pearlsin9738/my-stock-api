from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import akshare as ak
import pandas as pd

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def calc_ma(series, n):
    return series.rolling(n).mean()

def calc_boll(close, n=20):
    mid = close.rolling(n).mean()
    std = close.rolling(n).std()
    return mid, mid + 2 * std, mid - 2 * std

def calc_macd(close, fast=12, slow=26, signal=9):
    ema_f = close.ewm(span=fast).mean()
    ema_s = close.ewm(span=slow).mean()
    diff = ema_f - ema_s
    dea  = diff.ewm(span=signal).mean()
    bar  = (diff - dea) * 2
    return diff, dea, bar, "up" if bar.iloc[-1] > bar.iloc[-2] else "down"

@app.get("/tech")
def get_tech(code: str = "000001"):
    try:
        df = ak.stock_zh_a_hist(symbol=code, period="daily")
        if df.empty:
            return {"error": "akshare returned empty dataframe (likely non-trading day)"}
        df = df.tail(60)                       # 最近60根日K
        df["日期"] = df["日期"].astype(str)    # 转字符串

        close  = df["收盘"]
        volume = df["成交量"]

        ma10 = calc_ma(close, 10)
        ma20 = calc_ma(close, 20)
        ma60 = calc_ma(close, 60)
        boll_mid, boll_up, boll_low = calc_boll(close)

        vol_ma10 = calc_ma(volume, 10)
        vol_vs   = f"{(volume.iloc[-1] / vol_ma10.iloc[-1] - 1) * 100:+.0f}%"

        diff, dea, bar, dir_macd = calc_macd(close)

        return {
            "code": code,
            "update": df["日期"].iloc[-1],
            "main": {
                "kline": df[["日期", "开盘", "收盘", "最高", "最低"]].to_dict(orient="records"),
                "ma10": ma10.round(2).tolist(),
                "ma20": ma20.round(2).tolist(),
                "ma60": ma60.round(2).tolist(),
                "boll_mid": boll_mid.round(2).tolist(),
                "boll_up": boll_up.round(2).tolist(),
                "boll_low": boll_low.round(2).tolist(),
            },
            "volume": {
                "data": volume.tolist(),
                "ma10": vol_ma10.round(0).tolist(),
                "vs_ma10": vol_vs,
            },
            "macd": {
                "diff": diff.round(3).tolist(),
                "dea": dea.round(3).tolist(),
                "bar": bar.round(3).tolist(),
                "dir": dir_macd,
            },
        }
    except Exception as e:
        return {"error": str(e)}
