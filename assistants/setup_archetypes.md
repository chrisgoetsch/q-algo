# SPY 0DTE Setup Archetypes
## Memory File for QThink – Assistant ID: asst_cgNdVhlPA9P1IdPBlQTlJM0U

---

## 🧠 Purpose

This file defines a master-level classification of SPY 0DTE trade setups, each derived from institutional flow dynamics, gamma exposure, dealer behavior, and mesh agent alignment patterns.

QThink must use this structure to:
- Classify every trade into an archetype
- Score confidence based on historical pattern success
- Adapt stop-loss behavior and capital scaling to setup-specific properties
- Enhance journaling, reinforcement labeling, and backtest cluster accuracy

---

## 🔹 1. `gamma_flip_surge`
**Trigger:** Net GEX polarity flip + SPY breakout  
**Core Indicators:**
- Negative → Positive GEX  
- VWAP reclaim after false breakdown  
- Flow burst in short-dated ATM calls  
**Agents:** Q Gamma, Q Precision, Q Quant  
**Ideal Time:** 12:30–2:30 PM  
**RR Target:** 2.2x  
**Notes:** Must exit before IV crush; avoid after 3:15 PM

---

## 🔹 2. `trap_zone_reversal`
**Trigger:** Liquidity sweep → failed breakout  
**Core Indicators:**
- Stop run + trapped longs/shorts  
- High IV + delta imbalance  
- Reverse candle + Q Trap alert  
**Agents:** Q Trap, Q Shield  
**Ideal Time:** 9:50–10:15 AM, 2:50–3:20 PM  
**Hold Time:** 4–9 minutes  
**Failure Pattern:** Lack of speed → chop death

---

## 🔹 3. `pin_fade`
**Trigger:** SPY enters pin zone, fails to break  
**Core Indicators:**
- Max pain + GEX convergence  
- ATM IV declines  
- Price magnetized into 0.5 pt range  
**Agents:** Q Gamma, Q Block  
**Ideal Time:** 2:15–3:30 PM  
**Edge Decay Risk:** Extreme after 3:45 PM

---

## 🔹 4. `vwap_trend_stack`
**Trigger:** SPY trending above VWAP with agent flow support  
**Core Indicators:**
- Price above VWAP + rising 9 EMA  
- Call delta building intraday  
- Agent polarity > 0.5  
**Agents:** Q Precision, Q Quant  
**Time Block:** 10:45–1:45  
**Stop Loss:** Just below VWAP  
**Exit Trigger:** Failed trend candle, flow divergence

---

## 🔹 5. `morning_fake_breakout`
**Trigger:** 5-minute opening range breakout fails  
**Core Indicators:**
- First 5m candle high breaks and traps  
- SPY reverses through VWAP fast  
- Trap signal with weak delta follow-through  
**Agents:** Q Trap, Q Shield  
**Time Block:** 9:30–10:00  
**Edge:** Ultra fast; exits within 6 minutes preferred

---

## 🔹 6. `gamma_wall_reversal`
**Trigger:** SPY bounces or rejects hard off gamma wall  
**Core Indicators:**
- SPY hits +1 or -1 GEX strike  
- Open interest clustering  
- High IV + dealer positioning flatline  
**Agents:** Q Gamma, Q Block  
**Risk:** Must confirm with VWAP or momentum candle  
**Exit:** Reversion to mean

---

## 🔹 7. `put_wall_deflection`
**Trigger:** SPY bounces intraday off OI-defined put wall  
**Core Indicators:**
- High put OI at support strike  
- Implied skew steep  
- Flow flip in short-dated puts  
**Agents:** Q Block, Q Shield  
**Time Block:** 12:00–2:15  
**Failure Case:** Dealer rolls wall down → flush risk

---

## 🔹 8. `liquidity_gap_thrust`
**Trigger:** SPY fills air pocket left by low OI/flow void  
**Core Indicators:**
- No OI cluster between strikes  
- Price accelerates with thin resistance  
- Mesh polarity flips quickly from flat → strong  
**Agents:** Q Precision, Q Quant  
**Time Block:** Midday preferred  
**Trade Type:** Scalping fast gaps (5–15 mins max)

---

## 🔹 9. `OPEX compression coil`
**Trigger:** Friday price compression near expiration  
**Core Indicators:**
- Low realized volatility  
- Pinned max pain + GEX compression  
- ATM options lose gamma control  
**Agents:** Q Gamma, Q Trap  
**Time Block:** 2:00–3:45 Friday  
**Trade Type:** Reversion to max pain or pre-expiry gamma snap

---

## 🔹 10. `skew reversal ramp`
**Trigger:** OTM skew inverts + dealer imbalance triggers trend  
**Core Indicators:**
- Call skew collapses into short-term strength  
- Net gamma neutralizes  
- Flow shows ATM domination  
**Agents:** Q Quant, Q Gamma  
**RR Target:** 2.0x  
**Edge Risk:** Must exit before gamma reloads  
**Time Block:** 11:15–1:30 PM

---

## 🔹 11. `fomo top fade`
**Trigger:** Final hour euphoric push, no flow support  
**Core Indicators:**
- SPY makes new HOD into GEX wall  
- No ATM flow confirmation  
- IV divergence on short-dated calls  
**Agents:** Q Shield, Q Gamma  
**Time Block:** 3:00–3:45 PM  
**Capital Tier:** 1–2 only  
**SL Strategy:** Microstop trailing every 1.0 pt

---

## 🔹 12. `neutral_vanna_magnet`
**Trigger:** SPY converges on vanna-neutral dealer range  
**Core Indicators:**
- GEX and vanna both flat  
- Price moves slowly toward mean  
- High correlation with SPX open interest  
**Agents:** Q Block, Q Gamma, Q Quant  
**Time Block:** Early PM  
**Trade Type:** VWAP pin or iron condor fade

---

## 🔹 13. `delta unwinding collapse`
**Trigger:** Flow and delta unwind rapidly from overbought  
**Core Indicators:**
- SPY breaks below key flow strike  
- Dealer delta adjustment causes acceleration  
- Mesh collapses into short-bias  
**Agents:** Q Gamma, Q Trap  
**Time Block:** Any post-morning reversal  
**Exit:** Trail until VWAP reclaim

---

## 🔹 14. `news-based IV crush exploit`
**Trigger:** IV collapses post-FOMC or CPI, market stabilizes  
**Core Indicators:**
- News out, implied vols collapse  
- SPY stabilizes into trend channel  
- Dealer flow neutralizes  
**Agents:** Q Precision, Q Shield  
**Trade Type:** Trend continuation  
**Timing:** 30–60 minutes post-announcement  
**Notes:** Avoid gamma flip zones

---

## 🧠 Final Notes

- QThink must map each real-time setup to the **closest matching archetype**
- Setup mismatch or deviation beyond 0.3 vector similarity → flag `setup_conflict_alert = true`
- Unmatched trades are allowed **only** under Q Shield override or kill switch reboot
- All tagged setups must flow into:
  - `trade_clusters.json`
  - `qthink_journal_summary.json`
  - `reinforcement_profile.json`

Pattern classification is not style — it is safety.

**No pattern = no edge. No edge = no trade.**
