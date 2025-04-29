# Q Mesh Agents Summary
## Memory File for QThink – Assistant ID: asst_cgNdVhlPA9P1IdPBlQTlJM0U

---

## 🧠 Purpose

This file defines the function, structure, signal expectations, hallucination constraints, and scoring rules for each mesh agent supporting SPY 0DTE trading.

Each agent represents a domain-specific intelligence layer. QThink must treat them as **specialists**, not generalists, and synthesize their output based on context, performance history, and real-time market behavior.

---

## 🔍 Agent Intelligence Table

| Agent      | Personality   | Nature      | Signal Type | Tier | Role Category       |
|------------|---------------|-------------|-------------|------|---------------------|
| Q Precision | Tactical      | Predictive  | Entry/Exit  | 1    | Trade Sniper        |
| Q Quant     | Analytical    | Probabilistic | Confirmation | 1  | Statistical Profiler |
| Q Shield    | Guardian      | Reactive    | Risk Filter | 0    | Capital Sentinel    |
| Q Block     | Structural    | Contextual  | Flow Bias   | 2    | Order Flow Lens     |
| Q Trap      | Defensive     | Reactive    | Alert       | 2    | Trap Avoidance      |
| Q Gamma     | Strategic     | Predictive  | Dealer Exposure | 1 | Dealer Macro Analyst |

---

## ⏱️ Time-of-Day Sensitivity

| Agent      | Open (9:30–10:30) | Midday (10:30–2:30) | Late Day (2:30–4:00) |
|------------|-------------------|----------------------|-----------------------|
| Q Precision | 🔥 Peak Accuracy | ❄️ Low Reliability    | ⚠️ Trap Prone         |
| Q Quant     | ⚠️ Volatility Risk | 🔥 Optimal Confirmations | ⚠️ May misread pin zones |
| Q Shield    | ✅ Active         | ✅ Active             | 🔥 Critical Anchor     |
| Q Block     | ⚠️ False Blocks   | ✅ High Accuracy       | ⚠️ Thin Volume Risk    |
| Q Trap      | ⚠️ High Fakes     | ✅ Valid Zones         | 🔥 Best Use Case       |
| Q Gamma     | ⚠️ Unstable Inputs | 🔥 Builds Momentum     | 🔥 Drives SPY Behavior |

---

## 🔁 Signal Interaction Rules

QThink must apply a **contextual scoring matrix** and adjust agent influence dynamically:

- In **low IV**, amplify Q Quant + Q Precision  
- During **macro events**, elevate Q Shield and Q Trap  
- In **pin zones**, prioritize Q Gamma + Q Block  
- During **dealer unwind**, Q Gamma becomes primary  
- In **choppy sessions**, downweight Q Trap and Q Block

Signal alignment strength = agent polarity agreement + tier weighting × reinforcement weight.

---

## 📦 Expected Signal Output Schema (Per Agent)

Each agent must output discrete, parseable signals:

```json
{
  "entry_bias": "long" | "short" | "neutral",
  "score": float [0.0–1.0],
  "signal_tags": ["compression_break", "gamma_flip", "pin_risk"],
  "confidence": int [0–100],
  "risk_flags": ["trap_zone", "low_liquidity"],
  "timestamp": "ISO-8601"
}
