import argparse,json,pandas as pd
from strategy import StrategyConfig,run_backtest
from data_source import fetch_ohlcv
def main():
 p=argparse.ArgumentParser(); p.add_argument("--days",type=int,default=1095); p.add_argument("--exchange",default="binanceusdm"); p.add_argument("--symbol",default="BTC/USDT:USDT"); p.add_argument("--csv"); p.add_argument("--initial-equity",type=float,default=1000); p.add_argument("--risk-pct",type=float,default=.5); p.add_argument("--rr",type=float,default=2); p.add_argument("--fee-rate",type=float,default=.0005); p.add_argument("--slippage-bps",type=float,default=5); a=p.parse_args()
 df=pd.read_csv(a.csv) if a.csv else fetch_ohlcv(a.exchange,a.symbol,"1d",a.days)
 stats,trades,_=run_backtest(df,StrategyConfig(initial_equity=a.initial_equity,risk_pct=a.risk_pct,reward_risk=a.rr,fee_rate=a.fee_rate,slippage_bps=a.slippage_bps))
 print(json.dumps(stats,indent=2,default=str))
 if not trades.empty: trades.to_csv("backtest_trades.csv",index=False); print("Trades saved to backtest_trades.csv")
if __name__=="__main__": main()
