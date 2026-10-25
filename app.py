import os
import pandas as pd
import streamlit as st
import plotly.express as px
from dotenv import load_dotenv
from strategy import StrategyConfig, run_backtest, normalize_ohlcv
from data_source import fetch_ohlcv
load_dotenv()
st.set_page_config(page_title="AI Trade Check", page_icon="₿", layout="wide")
st.markdown('<div style="padding:22px;border-radius:14px;background:linear-gradient(110deg,#111827,#31516e);color:white"><h1>₿ AI Trade Check</h1><p>Bitcoin futures research · Backtest · Signal Lab</p></div>', unsafe_allow_html=True)
st.warning("Research prototype only. Live order execution is not implemented. Do not use as an unattended real-money bot.", icon="🛡️")
with st.sidebar:
    page=st.radio("Workspace",["Dashboard","Backtest","Signal Lab","Guide & Safety"])
    st.divider()
    initial=st.number_input("Starting equity (USDT)",min_value=10.0,value=1000.0,step=100.0)
    risk=st.slider("Risk budget (%)",0.1,2.0,0.5,0.1)
    rr=st.selectbox("Target multiple (R)",[1.0,1.5,2.0,2.5,3.0],index=2)
    fee=st.number_input("Fee per side (decimal)",min_value=0.0,max_value=.01,value=.0005,step=.0001,format="%.4f")
    slip=st.number_input("Slippage per side (bps)",min_value=0.0,max_value=100.0,value=5.0,step=1.0)
    buf=st.number_input("Stop buffer (%)",min_value=0.0,max_value=2.0,value=.1,step=.05)
    cap=st.number_input("Max notional / equity",min_value=.1,max_value=5.0,value=1.0,step=.1)
cfg=StrategyConfig(initial_equity=initial,risk_pct=risk,reward_risk=rr,fee_rate=fee,slippage_bps=slip,stop_buffer_pct=buf,notional_cap_multiple=cap)

def get_data(key):
    source=st.radio("Data source",["Public exchange candles","Upload CSV"],horizontal=True,key="source_"+key)
    if source=="Upload CSV":
        f=st.file_uploader("CSV: timestamp, open, high, low, close (volume optional)",type=["csv"],key="file_"+key)
        if f:
            try: return normalize_ohlcv(pd.read_csv(f)),"Uploaded CSV"
            except Exception as e: st.error(str(e))
        return None,None
    a,b,c=st.columns(3)
    with a: ex=st.selectbox("Exchange",["binanceusdm","binance","bybit","okx"],key="ex_"+key)
    with b: sym=st.text_input("Market symbol", "BTC/USDT:USDT" if ex=="binanceusdm" else "BTC/USDT",key="sym_"+key)
    with c: days=st.selectbox("History (days)",[90,180,365,730,1095,1825],index=4,key="days_"+key)
    if st.button("Fetch daily candles",type="primary",key="fetch_"+key):
        try:
            with st.spinner("Fetching public OHLCV..."): st.session_state["ohlcv"]=fetch_ohlcv(ex,sym,"1d",days)
            st.session_state["ohlcv_label"]=f"{ex} · {sym} · {days} days"
        except Exception as e: st.error(f"Fetch failed: {e}")
    return st.session_state.get("ohlcv"),st.session_state.get("ohlcv_label","Fetched candles")

if page=="Dashboard":
    st.subheader("Strategy dashboard")
    a,b,c,d=st.columns(4); a.metric("Market","BTC futures"); b.metric("Timeframe","1D"); c.metric("Target",f"{rr:g}R"); d.metric("Risk",f"{risk:.1f}%")
elif page=="Backtest":
    st.subheader("Historical backtest")
    data,label=get_data("backtest")
    if data is not None:
        st.success(f"{len(data):,} candles loaded · {label}")
        with st.expander("Preview data"): st.dataframe(data.tail(20),use_container_width=True,hide_index=True)
        if st.button("Run backtest",type="primary"):
            try:
                stats,trades,_=run_backtest(data,cfg)
                st.session_state["stats"]=stats; st.session_state["trades"]=trades
            except Exception as e: st.error(f"Backtest failed: {e}")
    if "stats" in st.session_state:
        s=st.session_state["stats"]; t=st.session_state["trades"]
        st.markdown("### Results")
        a,b,c,d=st.columns(4); a.metric("Trades",s["trades"]); b.metric("Net P&L (USDT)",f'{s["net_pnl_usdt"]:+,.2f}'); c.metric("Ending equity",f'{s["ending_equity_usdt"]:,.2f}'); d.metric("Return",f'{s["return_pct"]:+.2f}%')
        a,b,c=st.columns(3); a.metric("Win rate",f'{s["win_rate_pct"]:.1f}%'); b.metric("Max drawdown",f'{s["max_drawdown_pct"]:.2f}%'); c.metric("Estimated fees",f'{s["fees_usdt"]:,.2f}')
        st.caption(f'Profit factor: {s["profit_factor"] if s["profit_factor"] is not None else "N/A"} · {s["note"]}')
        if len(t):
            st.plotly_chart(px.line(t,x="exit_time",y="equity_after",title="Equity curve"),use_container_width=True)
            st.plotly_chart(px.bar(t,x="exit_time",y="net_pnl_usdt",color="side",title="Trade-by-trade P&L"),use_container_width=True)
            st.dataframe(t,use_container_width=True,hide_index=True)
            st.download_button("Download trade ledger CSV",t.to_csv(index=False).encode(),file_name="btc_futures_backtest_trades.csv",mime="text/csv")
        else: st.info("No qualifying trades in this data window.")
elif page=="Signal Lab":
    st.subheader("Signal Lab")
    st.write("Review the latest two candles. Make sure the final candle is fully closed.")
    data=st.session_state.get("ohlcv")
    f=st.file_uploader("Optional CSV",type=["csv"],key="signal_file")
    if f:
        try: data=normalize_ohlcv(pd.read_csv(f))
        except Exception as e: st.error(str(e)); data=None
    if data is not None and len(data)>=2:
        p,q=data.iloc[-2],data.iloc[-1]
        sig="LONG" if q.close>q.open and q.close>p.high else "SHORT" if q.close<q.open and q.close<p.low else "NO SIGNAL"
        st.metric("Rule result",sig); st.write(f"Latest candle UTC: {q.timestamp}")
        st.write(f"Previous high/low: {p.high:,.2f} / {p.low:,.2f}")
        st.write(f"Latest O/H/L/C: {q.open:,.2f} / {q.high:,.2f} / {q.low:,.2f} / {q.close:,.2f}")
    else: st.info("Fetch candles from Backtest or upload a CSV.")
else:
    st.subheader("Guide & safety")
    st.markdown("**Windows setup**\n1. Install Python 3.10+.\n2. Extract ZIP and open terminal in folder.\n3. `py -m venv .venv`\n4. Activate: PowerShell ` .venv\\Scripts\\Activate.ps1 ` or CMD `.venv\\Scripts\\activate.bat`.\n5. `python -m pip install -r requirements.txt`\n6. `python -m streamlit run app.py`\n7. Open `http://localhost:8501`.\n\n**CSV format:** `timestamp,open,high,low,close,volume`; volume optional.\n\n**Prior output discrepancy:** screenshot reports net P&L -67.9769 USDT and ending equity 1081.4484 USDT. If initial equity was 1000 USDT, ending equity implies +81.4484, so those two metrics cannot both be correct. Treat old output as inconsistent. This version derives P&L from ending equity minus starting equity and has a reconciliation test.\n\n**Currency:** calculations are in USDT, not INR. ₹100,000 is not 100,000 USDT.\n\n**Limitations:** funding, liquidation, spread, partial fills, margin rules, exchange precision, outages and exact intraday price path are not fully modeled. If stop and target are both touched in a daily candle, stop is assumed first.\n\n**Live trading:** intentionally not implemented. Production requires exchange-specific execution, testnet validation, persistent state, position/order reconciliation, duplicate-order prevention, monitoring, alerts, kill switch and secure API-key handling.")
