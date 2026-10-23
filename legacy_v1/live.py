import argparse,time
from datetime import datetime,timezone
import ccxt
from ai_trade_check.config import CFG
from ai_trade_check.strategy import signal,levels,quantity

CONFIRM="I_UNDERSTAND_REAL_MONEY_RISK"

def main(mode):
    live=mode=="live"
    if live and (not CFG.live_enabled or CFG.confirmation!=CONFIRM):
        raise SystemExit("Live locked. Set LIVE_TRADING_ENABLED=true and exact confirmation in .env.")
    if live and (not CFG.api_key or not CFG.api_secret):
        raise SystemExit("API_KEY and API_SECRET required.")
    if live and CFG.exchange_id!="binanceusdm":
        raise SystemExit("Live adapter restricted to binanceusdm; use paper mode otherwise.")
    klass=getattr(ccxt,CFG.exchange_id)
    args={"enableRateLimit":True}
    if live: args.update(apiKey=CFG.api_key,secret=CFG.api_secret)
    ex=klass(args); ex.load_markets()
    equity=CFG.paper_capital_usdt
    last_sig=None; last_trade_day=None; streak=0; cooldown_until=0
    print(f"{mode.upper()} monitor started for {CFG.symbol}; Ctrl+C to stop.")
    while True:
        try:
            now=ex.milliseconds()
            candles=ex.fetch_ohlcv(CFG.symbol,"1d",limit=4)
            candles=[x for x in candles if x[0]+86400000<=now]
            if len(candles)>=2:
                prev,prev2=candles[-1],candles[-2]
                s=signal(prev,prev2,CFG.stop_buffer_pct)
                day=datetime.fromtimestamp(now/1000,timezone.utc).date().isoformat()
                if s and prev[0]!=last_sig and day!=last_trade_day and now>=cooldown_until:
                    ticker=ex.fetch_ticker(CFG.symbol); entry=float(ticker["last"])
                    lv=levels(s.side,entry,s.stop,CFG.rr)
                    if lv:
                        cap=min(CFG.max_notional_inr,equity*CFG.inr_per_usdt)/CFG.inr_per_usdt
                        q=quantity(equity,entry,lv["stop"],CFG.risk_pct,cap,CFG.fee)
                        if q>0:
                            print("SIGNAL",s.side,"qty",q,"levels",lv)
                            if live: submit(ex,s.side,q,lv)
                            else: print("PAPER ONLY: no order sent.")
                            last_sig=prev[0]; last_trade_day=day
            time.sleep(max(10,CFG.poll_seconds))
        except KeyboardInterrupt: break
        except Exception as e:
            print("ERROR:",repr(e)); time.sleep(max(10,CFG.poll_seconds))

def submit(ex,side,q,lv):
    entry_side="buy" if side=="long" else "sell"
    exit_side="sell" if side=="long" else "buy"
    submitted=False
    try:
        order=ex.create_order(CFG.symbol,"market",entry_side,q)
        submitted=True
        print("ENTRY SUBMITTED",order)
        ex.create_order(CFG.symbol,"STOP_MARKET",exit_side,q,None,{"stopPrice":ex.price_to_precision(CFG.symbol,lv["stop"]),"reduceOnly":True,"workingType":"MARK_PRICE"})
        ex.create_order(CFG.symbol,"TAKE_PROFIT_MARKET",exit_side,q,None,{"stopPrice":ex.price_to_precision(CFG.symbol,lv["target"]),"reduceOnly":True,"workingType":"MARK_PRICE"})
        print("Stop/target submitted; verify both immediately in exchange UI.")
    except Exception as e:
        print("CRITICAL protective order failure:",repr(e))
        if submitted:
            try: ex.create_order(CFG.symbol,"market",exit_side,q,None,{"reduceOnly":True})
            except Exception as ce: print("EMERGENCY CLOSE FAILED; MANUAL INTERVENTION REQUIRED",repr(ce))
        raise

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--mode",choices=["paper","live"],default="paper"); main(p.parse_args().mode)
