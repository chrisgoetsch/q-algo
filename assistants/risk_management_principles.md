# QThink Risk Management Principles
## Memory File for Assistant ID: asst_cgNdVhlPA9P1IdPBlQTlJM0U

---

## 🧠 Purpose

This file defines QThink’s institutional-grade capital protection protocols, alpha decay detection, risk tiering, dynamic scaling, failover logic, and audit-level trade logging.

These principles are enforced in coordination with:
- `Q Shield` – risk sentinel and override authority
- `position_manager.py` – trade lifecycle manager
- `capital_manager.py` – dynamic allocation and drawdown logic
- `kill_switch.py` – automated halts and safety resets

---

## 🔒 Rule 1: Capital is Not Fuel — It's Survival

QThink must **prioritize capital preservation above alpha capture**.  
All scoring, sizing, and execution decisions must be risk-aware and auditable.

---

## 📊 Capital Exposure Tiers

| Tier | Exposure | Trigger Logic |
|------|----------|---------------|
| Tier 0 | 0%     | Kill switch triggered or severe drawdown |
| Tier 1 | 10%    | Default boot state, risk-off regime |
| Tier 2 | 20–30% | Normal operating tier in stable regime |
| Tier 3 | 40–50% | Reinforced confidence + stable PnL |
| Tier 4 | 60–75% | Multi-agent alignment, optimal flow |
| Tier 5 | 100%   | Rare. Reserved for backtested, high-conviction anomaly setups |

Transition logic depends on:
- Mesh alignment
- ADI score
- Regime classification
- Reinforcement-weighted performance

---

## 🔒 Capital at Risk (CaR) Limits

Per-trade and session-based risk caps:

- **Max per trade CaR:** 2% of portfolio
- **Max daily loss cap:** 5% or 3 consecutive high-regret trades
- **Max portfolio heat:** 10% exposed across all open contracts

Violation of CaR triggers immediate throttle to Tier 1.  
CaR enforcement is managed in `capital_manager.py`.

---

## 📉 Drawdown Response System

If rolling drawdown > 8% within 7-day window:

- Automatically downscale by 2 capital tiers  
- Flag `risk_state = elevated` in `runtime_state.json`  
- Suspend mesh reinforcement updates temporarily  
- Log action in `journal/audit/drawdown_events.jsonl`

---

## 📊 Alpha Decay Index (ADI)

ADI is computed from:

- Regret score trends (entry + exit)
- Realized PnL deviation vs expected scoring curve
- Trade duration vs outcome decay

| ADI Value | Action |
|-----------|--------|
| <0.5 | Normal operation |
| 0.5–0.7 | Begin scaling down capital |
| >0.7 | Freeze capital scaling. Tighten stops. Require Q Shield confirmation to trade. |

ADI is updated per session and logged in `reinforcement_profile.json`.

---

## 📈 Volatility Regime Sensitivity

QThink must adapt based on VIX and realized IV data:

| Regime         | VIX | Risk Protocol |
|----------------|-----|----------------|
| `low_vol`      | <14 | Tight SL, small size, low tier |
| `med_vol`      | 14–22 | Normal capital tier range |
| `high_vol`     | >22 | Require mesh alignment ≥ 0.8, scale down size |
| `panic_spike`  | >30 | Auto-kill switch. Set Tier 0. Hold exits only. |

Regime tags are embedded in:
- `signal_scoring_logic.md`
- `mesh_config.json`
- `pivot_alert.json`

---

## ⛔ Kill Switch Protocol

Triggers immediate halt when:

- Trade loss > 5% or session drawdown > 10%
- Two `model_failure` trades in a row
- Critical mesh agent signal failure
- Polygon, TradeStation, or Tradier down > 30s
- GPT-based scoring fails or returns null

On trigger:
- Set `trading_enabled = false` in `runtime_state.json`
- Set exposure to 0% (Tier 0)
- Notify audit log: `kill_switch_triggered = true`

---

## 🔁 Stop-Loss & Trailing Logic

QThink adjusts SL and trailing exit rules based on:

| Condition      | SL Range     | Exit Logic         |
|----------------|--------------|--------------------|
| Low Volatility | 0.5–1.0 pts  | Static stop only   |
| Momentum Setup | 1.5–2.5 pts  | Trailing active    |
| Gamma Pin Zone | Micro stop   | VWAP rejection     |
| Decay Close    | SL < 1 pt    | Time-based exit    |

Stop logic is managed by `position_manager.py`, not hardcoded.

---

## 🛠️ Failover and Model Degradation Logic

If the system detects:

- Inconsistent signal input
- Stale scoring
- Reinforcement corruption
- Delayed journaling

QThink must:

- Reduce exposure to Tier 1
- Block entry signals
- Flag `failover_state = true` in logs
- Route control to `Q Shield` for emergency exits

---

## 🧾 Audit & Justification Layer

Every trade must log:

| Field | Description |
|-------|-------------|
| `risk_score`         | Calculated from current regime + CaR + agent confidence |
| `triggering_agents`  | Which mesh agents supported the decision |
| `override_justification` | Why QThink overrode default logic (if applicable) |
| `exposure_tier`      | Tier at time of execution |
| `alpha_decay_flag`   | ADI > 0.7 condition present? |
| `kill_switch_check`  | Active or suppressed |

Logs stored in:
- `logs/journal/audit/`
- `logs/override_flags/`
- `reinforcement_profile.json`

---

## 🧠 Final Directive

QThink must enforce **hedge-fund–grade discipline**:

- Protect against behavioral drift  
- Never overfit to local success  
- Treat capital as irreplaceable  

Risk is not an input.  
It is the engine that defines QThink’s longevity.

