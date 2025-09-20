from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import akshare as ak
import pandas as pd

app = FastAPI()

# 允许跨域（ChatGPT 调用需要）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def calc_ma(df, n):
    return df["收盘"].rolling(n).mean()

def calc_boll(df, n=20):
    mid = df["收盘"].rolling(n).mean()
    std = df["收盘"].rolling(n).std()
    up = mid + 2 * std
    low = mid - 2 * std
    return mid, up, low

def calc_macd(df, fast=12, slow=26, signal=9):
    ema_fast = df["收盘"].ewm(span=fast).mean()
    ema_slow = df["收盘"].ewm(span=slow).mean()
    diff = ema_fast - ema_slow
    dea = diff.ewm(span=signal).mean()
    bar = (diff - dea) * 2
    dir = "up" if bar.iloc[-1] > bar.iloc[-2] else "down"
    return diff, dea, bar, dir

@app.get("/tech")
def get_tech(code: str = "510300"):
    try:
        df = ak.stock_zh_a_hist(symbol=code, period="daily")
        df = df.tail(60)  # 最近60根K线
        df["日期"] = df["日期"].astype(str)

        # 主图指标
        ma10 = calc_ma(df, 10)
        ma20 = calc_ma(df, 20)
        ma60 = calc_ma(df, 60)
        boll_mid, boll_up, boll_low = calc_boll(df)

        # 成交量
        vol_ma10 = df["成交量"].rolling(10).mean()
        vol_last = df["成交量"].iloc[-1]
        vol_vs = f"{(vol_last / vol_ma10.iloc[-1] - 1) * 100:+.0f}%"

        # MACD
        diff, dea, bar, dir = calc_macd(df)

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
                "data": df["成交量"].tolist(),
                "ma10": vol_ma10.round(0).tolist(),
                "vs_ma10": vol_vs,
            },
            "macd": {
                "diff": diff.round(3).tolist(),
                "dea": dea.round(3).tolist(),
                "bar": bar.round(3).tolist(),
                "dir": dir,
            }
        }
    except Exception as e:
        return {"error": str(e)}
