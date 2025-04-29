# QThink Signal Scoring Logic
## Memory File for Assistant ID: asst_cgNdVhlPA9P1IdPBlQTlJM0U

---

## 🧠 Purpose

This file defines how QThink processes mesh agent signals, macro overlays, volatility context, alignment, and learned reinforcement weights to generate a final trade score.

The score is used to determine the confidence of SPY 0DTE entry or exit and is recorded for learning, journaling, and model refinement.

---

## 🧮 Core Signal Equation (V2 – Production Grade)

QThink computes its `adjusted_score` for any trade opportunity using the following multi-factor model:

```text
raw_score = ∑ (agent_score × agent_weight × context_multiplier × reinforcement_weight)

adjusted_score = raw_score × alignment_coefficient × conviction_multiplier - penalty_factor

