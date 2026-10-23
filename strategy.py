from dataclasses import dataclass
import pandas as pd

@dataclass
class StrategyConfig:
    initial_equity: float = 1000.0
    risk_pct: float = 0.5
    reward_risk: float = 2.0
    fee_rate: float = 0.0005
    slippage_bps: float = 5.0
    stop_buffer_pct: float = 0.1
    notional_cap_multiple: float = 1.0
    cooldown_after_losses: int = 3
    cooldown_days: int = 3

def normalize_ohlcv(df):
    x=df.copy()
    x.columns=[str(c).strip().lower() for c in x.columns]
    for a in ("date","datetime","time"):
        if a in x.columns and "timestamp" not in x.columns:
            x=x.rename(columns={a:"timestamp"}); break
    required=["timestamp","open","high","low","close"]
    missing=[c for c in required if c not in x.columns]
    if missing: raise ValueError("Missing CSV columns: "+", ".join(missing))
    x["timestamp"]=pd.to_datetime(x["timestamp"],utc=True,errors="coerce")
    for c in ["open","high","low","close"]: x[c]=pd.to_numeric(x[c],errors="coerce")
    if "volume" not in x.columns: x["volume"]=0.0
    x["volume"]=pd.to_numeric(x["volume"],errors="coerce").fillna(0)
    x=x.dropna(subset=required).sort_values("timestamp").drop_duplicates("timestamp").reset_index(drop=True)
    if len(x)<5: raise ValueError("At least five valid candles are required.")
    if (x[["open","high","low","close"]]<=0).any().any(): raise ValueError("Prices must be positive.")
    if (x["high"]<x[["open","close","low"]].max(axis=1)).any() or (x["low"]>x[["open","close","high"]].min(axis=1)).any():
        raise ValueError("Invalid OHLC row: high/low inconsistent with open/close.")
    return x

def signal_for_row(prev, sig):
    if sig["close"]>sig["open"] and sig["close"]>prev["high"]: return "long"
    if sig["close"]<sig["open"] and sig["close"]<prev["low"]: return "short"
    return None

def run_backtest(raw, cfg):
    df=normalize_ohlcv(raw); equity=float(cfg.initial_equity); peak=equity; maxdd=0
    trades=[]; losses=0; cooldown_until=None
    for i in range(2,len(df)):
        entry_bar=df.iloc[i]; sig=df.iloc[i-1]; prev=df.iloc[i-2]; ts=entry_bar["timestamp"]
        if cooldown_until is not None and ts<cooldown_until: continue
        side=signal_for_row(prev,sig)
        if not side: continue
        raw_entry=float(entry_bar["open"]); buf=cfg.stop_buffer_pct/100
        stop=float(sig["low"])*(1-buf) if side=="long" else float(sig["high"])*(1+buf)
        risk_unit=raw_entry-stop if side=="long" else stop-raw_entry
        if risk_unit<=0: continue
        risk_cash=equity*cfg.risk_pct/100
        qty=min(risk_cash/risk_unit, max(0,equity*cfg.notional_cap_multiple/raw_entry))
        if qty<=0: continue
        target=raw_entry+cfg.reward_risk*risk_unit if side=="long" else raw_entry-cfg.reward_risk*risk_unit
        exit_raw=None; reason=None; exit_ts=None
        for j in range(i,len(df)):
            bar=df.iloc[j]
            if side=="long":
                # Stop-first if both stop and target touched in same candle.
                if float(bar["low"])<=stop: exit_raw,reason=stop,"stop"
                elif float(bar["high"])>=target: exit_raw,reason=target,"target"
            else:
                if float(bar["high"])>=stop: exit_raw,reason=stop,"stop"
                elif float(bar["low"])<=target: exit_raw,reason=target,"target"
            if exit_raw is not None: exit_ts=bar["timestamp"]; break
        if exit_raw is None:
            exit_raw=float(df.iloc[-1]["close"]); reason="data_end"; exit_ts=df.iloc[-1]["timestamp"]
        slip=cfg.slippage_bps/10000
        entry_fill=raw_entry*(1+slip if side=="long" else 1-slip)
        exit_fill=exit_raw*(1-slip if side=="long" else 1+slip)
        gross=(exit_fill-entry_fill)*qty if side=="long" else (entry_fill-exit_fill)*qty
        fees=(abs(entry_fill*qty)+abs(exit_fill*qty))*cfg.fee_rate
        net=gross-fees; before=equity; equity+=net; peak=max(peak,equity)
        maxdd=max(maxdd,(peak-equity)/peak*100 if peak else 0)
        trades.append(dict(entry_time=ts,exit_time=exit_ts,side=side,entry_price=entry_fill,stop=stop,target=target,exit_price=exit_fill,exit_reason=reason,qty_btc=qty,risk_budget_usdt=risk_cash,gross_pnl_usdt=gross,fees_usdt=fees,net_pnl_usdt=net,equity_before=before,equity_after=equity))
        losses=losses+1 if net<0 else 0
        if losses>=cfg.cooldown_after_losses:
            cooldown_until=pd.Timestamp(exit_ts)+pd.Timedelta(days=cfg.cooldown_days); losses=0
    import pandas as pd
    t=pd.DataFrame(trades)
    wins=t.loc[t.net_pnl_usdt>0,"net_pnl_usdt"].sum() if len(t) else 0
    neg=t.loc[t.net_pnl_usdt<0,"net_pnl_usdt"].sum() if len(t) else 0
    stats={"trades":len(t),"net_pnl_usdt":round(equity-cfg.initial_equity,4),"ending_equity_usdt":round(equity,4),
      "return_pct":round((equity/cfg.initial_equity-1)*100,3) if cfg.initial_equity else 0,
      "win_rate_pct":round((t.net_pnl_usdt>0).mean()*100,2) if len(t) else 0,
      "profit_factor":round(wins/abs(neg),3) if neg<0 else None,"max_drawdown_pct":round(maxdd,3),
      "fees_usdt":round(float(t.fees_usdt.sum()),4) if len(t) else 0.0,
      "note":"Estimate only; funding, liquidation, spread, partial fills and exchange-specific execution are not fully modeled."}
    return stats,t,df
