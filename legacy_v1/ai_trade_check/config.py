import os
from dataclasses import dataclass
from dotenv import load_dotenv
load_dotenv()

@dataclass(frozen=True)
class Config:
    exchange_id: str = os.getenv("EXCHANGE_ID","binanceusdm")
    api_key: str = os.getenv("API_KEY","")
    api_secret: str = os.getenv("API_SECRET","")
    symbol: str = os.getenv("SYMBOL","BTC/USDT:USDT")
    starting_capital_inr: float = float(os.getenv("STARTING_CAPITAL_INR","100000"))
    inr_per_usdt: float = float(os.getenv("INR_PER_USDT","87"))
    risk_pct: float = float(os.getenv("RISK_PER_TRADE","0.005"))
    max_notional_inr: float = float(os.getenv("MAX_NOTIONAL_INR","100000"))
    stop_buffer_pct: float = float(os.getenv("STOP_BUFFER_PCT","0.001"))
    rr: float = float(os.getenv("REWARD_RISK","2"))
    fee: float = float(os.getenv("FEE_RATE_PER_SIDE","0.0005"))
    slippage_bps: float = float(os.getenv("SLIPPAGE_BPS","5"))
    live_enabled: bool = os.getenv("LIVE_TRADING_ENABLED","false").lower()=="true"
    confirmation: str = os.getenv("LIVE_CONFIRMATION","")
    paper_capital_usdt: float = float(os.getenv("PAPER_STARTING_CAPITAL_USDT","1149.43"))
    poll_seconds: int = int(os.getenv("POLL_SECONDS","60"))
CFG=Config()
