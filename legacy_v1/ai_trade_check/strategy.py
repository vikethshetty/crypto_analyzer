from dataclasses import dataclass
from typing import Optional

@dataclass
class Signal:
    side: str
    stop: float

def signal(prev, prev2, buffer_pct=0.001):
    # OHLCV rows: timestamp, open, high, low, close, volume
    _,o,h,l,c,_=prev
    _,o2,h2,l2,c2,_=prev2
    if min(o,h,l,c,h2,l2)<=0 or h<l or h2<l2:
        return None
    if c>h2 and c>o:
        return Signal("long", float(l*(1-buffer_pct)))
    if c<l2 and c<o:
        return Signal("short", float(h*(1+buffer_pct)))
    return None

def levels(side, entry, stop, rr=2.0):
    risk=entry-stop if side=="long" else stop-entry
    if risk<=0: return None
    target=entry+rr*risk if side=="long" else entry-rr*risk
    return {"entry":float(entry),"stop":float(stop),"target":float(target),"risk":float(risk)}

def quantity(equity, entry, stop, risk_pct, max_notional, fee=0.0005):
    d=abs(entry-stop)
    if min(equity,entry,d)<=0: return 0.0
    q_risk=(equity*risk_pct)/(d+entry*fee*2)
    q_cap=max_notional/entry
    return max(0.0,min(q_risk,q_cap))
