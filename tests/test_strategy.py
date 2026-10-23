import pandas as pd
from strategy import StrategyConfig,run_backtest,signal_for_row
def test_long_signal(): assert signal_for_row({"high":100,"low":90},{"open":99,"close":101})=="long"
def test_short_signal(): assert signal_for_row({"high":110,"low":100},{"open":101,"close":99})=="short"
def test_pnl_reconciles():
 d=pd.DataFrame({"timestamp":pd.date_range("2024-01-01",periods=8,freq="D",tz="UTC"),"open":[100,100,100,105,106,107,108,109],"high":[102,103,106,108,109,110,111,112],"low":[98,97,99,103,104,105,106,107],"close":[101,102,105,107,108,109,110,111]})
 s,t,_=run_backtest(d,StrategyConfig(initial_equity=1000,fee_rate=0,slippage_bps=0))
 assert abs(s["net_pnl_usdt"]-(s["ending_equity_usdt"]-1000))<1e-6
 assert s["trades"]==len(t)
