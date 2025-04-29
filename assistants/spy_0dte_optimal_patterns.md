# SPY 0DTE Optimal Trade Patterns
## Memory File for QThink – Assistant ID: asst_cgNdVhlPA9P1IdPBlQTlJM0U

---

## 🎯 Purpose

This file provides QThink with a curated database of historically high-performance SPY 0DTE trade patterns.  
Each setup includes context, agent alignment, timing conditions, and performance statistics.

QThink should use this as a reference baseline when evaluating new trade opportunities.

---

## 📈 High-Performance Setup Archetypes

### 1. `gamma_flip_surge`
**Description:** SPY breaks through a dealer gamma wall with momentum  
**Requirements:**
- GEX flip from negative to positive
- SPY crosses above the gamma wall strike
- VWAP support underneath
**Agent Alignment:**
- Q Gamma + Q Quant + Q Precision  
**Win Rate:** 78%  
**Average Duration:** 11–15 min  
**Best Time Block:** 12:45–2:00 PM  
**Avoid if:** Q Trap active or max_pain level is within 0.5 pts

---

### 2. `trap_zone_reversal`
**Description:** SPY sweeps a liquidity trap zone and reverses hard  
**Requirements:**
- Price enters prior sweep zone with high IV
- Q Trap detects stop-out structure
- Q Precision confirms exit candle
**Agent Alignment:** Q Trap + Q Shield + Q Precision  
**Win Rate:** 72%  
**PnL Skew:** Skewed positive (avg win > 2x stop)  
**Time Block:** 10:00–10:30 AM or 2:45–3:15 PM  
**Avoid if:** SPY is pinned to max pain

---

### 3. `pin_fade_entry`
**Description:** SPY rejects gamma wall + max pain zone into fade  
**Requirements:**
- Pin score > 0.7 in `max_pain_map.json`
- SPY enters 0.25 pt range around pin
- IV dropping on OTM calls
**Agent Alignment:** Q Gamma + Q Block + Q Quant  
**Win Rate:** 74%  
**Exit Target:** VWAP mean reversion  
**Time Block:** 2:00–3:30 PM  
**Avoid if:** GEX flips upward after entry

---

### 4. `vwap_trend_stack`
**Description:** SPY trends with full alignment + dealer support  
**Requirements:**
- SPY above VWAP and rising 5-min EMA
- Q Precision signal > 0.8
- GEX net neutral or rising
**Agent Alignment:** Q Precision + Q Quant  
**Win Rate:** 79%  
**Capital Tier:** 3–4 recommended  
**Duration:** 15–30 min  
**Best Used:** After 11:00 AM

---

### 5. `morning_fake_breakout`
**Description:** SPY fakes high on open, reverses fast with delta unload  
**Requirements:**
- Breakout fails on first 5m bar
- Q Trap fires reversal alert
- SPY below VWAP within 15 mins
**Agent Alignment:** Q Trap + Q Shield  
**Win Rate:** 70%  
**Time Block:** 9:30–10:15 AM  
**Trade Type:** Fast scalp (exit < 10 min)

---

## 🧠 How to Use

QThink must compare **real-time setups** to this file:
- If similarity score > 0.75 to a known pattern → boost entry score
- If signal contradicts a proven setup’s conditions → penalize `final_score`
- Always log matched archetype to `trade_clusters.json`

