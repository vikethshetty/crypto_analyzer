import ccxt, pandas as pd
def fetch_ohlcv(exchange_id="binanceusdm",symbol="BTC/USDT:USDT",timeframe="1d",days=1095):
    if not hasattr(ccxt,exchange_id): raise ValueError(f"Unknown CCXT exchange: {exchange_id}")
    ex=getattr(ccxt,exchange_id)({"enableRateLimit":True})
    if not ex.has.get("fetchOHLCV"): raise ValueError(f"{exchange_id} has no OHLCV support in CCXT.")
    since=ex.milliseconds()-int(days)*86400000; rows=[]
    while since<ex.milliseconds():
        batch=ex.fetch_ohlcv(symbol,timeframe=timeframe,since=since,limit=1000)
        if not batch: break
        rows.extend(batch); nxt=batch[-1][0]+1
        if nxt<=since or len(batch)<2: break
        since=nxt
    if not rows: raise ValueError("No candles returned. Check symbol, exchange and internet.")
    df=pd.DataFrame(rows,columns=["timestamp","open","high","low","close","volume"])
    df["timestamp"]=pd.to_datetime(df.timestamp,unit="ms",utc=True)
    cutoff=pd.Timestamp.now(tz="UTC")-pd.Timedelta(days=days)
    return df[df.timestamp>=cutoff].drop_duplicates("timestamp").sort_values("timestamp").reset_index(drop=True)
