# SPY 0DTE Performance Benchmarks
## Memory File for QThink – Assistant ID: asst_cgNdVhlPA9P1IdPBlQTlJM0U

---

## 🧠 Purpose

This file defines benchmark-level expectations for SPY 0DTE trade performance.  
QThink must use these metrics to detect drift, decay, underperformance, and to calibrate confidence in trade scoring.

All scoring outputs, journaling logs, and reinforcement updates must be cross-referenced against these benchmarks.

---

## 📈 Strategy Performance Benchmarks

| Metric                | Optimal Range     | Strategy Response |
|-----------------------|------------------|--------------------|
| Win Rate              | 66–72%           | Below 60% → pause scaling |
| Avg Hold Time         | 9–18 min         | >25 min = alpha decay risk |
| Entry Regret Score    | <0.3             | >0.5 = overconfidence or misfire |
| Exit Regret Score     | <0.35            | >0.5 = missed exit or trap |
| Alignment Score       | >0.7             | <0.5 = mesh confusion |
| Net Mesh Polarity     | >0.2             | ≈ 0 = no edge or signal conflict |
| Max Drawdown (per trade) | <2%          | >3% = abort strategy loop |
| Optimal IV Rank       | 40–60%           | >65% = IV crush zone |
| GEX Behavior          | Neutral to positive | Negative = fade entries |
| PnL per Trade         | 1.5x SL          | <1.2 RR = risk inflation |

---

## ⏱ Setup-Specific Duration Benchmarks

QThink must track expected vs actual hold time by setup:

| Setup Type            | Expected Duration | Exit Signal |
|-----------------------|-------------------|-------------|
| Gamma Flip Surge      | 9–15 min          | VWAP break or decay start |
| Trap Reversal         | 5–10 min          | Trailing stop or failed retest |
| Pin Fade              | 15–25 min         | VWAP magnet or GEX reversal |
| VWAP Trend Stack      | 12–30 min         | Exit on volume stall |
| Morning Fake Breakout | 3–6 min           | Scalped or stopped early |

> If hold time exceeds expected duration by 2x → flag `alpha_drift_alert = true`

---

## 🎯 Risk:Reward Performance Guidance

| Score Range | Expected RR | Interpretation |
|-------------|--------------|----------------|
| 0–50        | <1.2         | Trade not worth risk |
| 51–70       | 1.5x         | Valid opportunity |
| 71–85       | 1.8–2.0x     | High-quality setup |
| 86–100      | >2.0x        | Premium risk-adjusted alpha |

QThink must flag `risk_efficiency = poor` if realized RR < 1.0 in backtest-confirmed setup.

---

## 🔄 Rolling Strategy Health Metrics

QThink must maintain rolling stats over 20-trade windows:

| Metric | Trigger |
|--------|---------|
| Win rate <60% | `underperformance_warning = true` |
| Avg entry regret >0.45 | `entry_timing_drift = true` |
| Avg exit regret >0.5 | `exit_model_drift = true` |
| Net alpha drift >1.5 std dev | `alpha_drift_alert = true` |

> These flags are written to `qthink_journal_summary.json` and `runtime_state.json`.

---

## 📊 Confidence Calibration Thresholds

QThink must not:

- Trust any setup-specific win rate unless `N ≥ 25`
- Use high RR values for new setup archetypes without confirmation
- Scale capital tier above Tier 3 without:
  - 3+ clean wins (PnL > 1.5x SL)
  - Regret score avg < 0.3
  - No active decay or drawdown flags

---

## 🚨 Journal Flag Tags

QThink must label trades in real-time with the following tags:

| Tag | Meaning |
|-----|---------|
| `underperformance_warning` | Trade violated >1 benchmark rule |
| `alpha_drift_alert` | Strategy no longer showing edge |
| `risk_efficiency_poor` | Trade took excess capital for poor RR |
| `mesh_overconfidence_flag` | Score high but regret >0.5 |
| `setup_held_too_long` | Time exceeded 2x optimal duration |
| `entry_lag_vs_pattern` | Entry did not match ideal time for pattern |
| `exit_missed_window` | Exit occurred after decay started |

All tags are recorded to `sync_log.jsonl` and used by `reinforcement_learning_flow.md`.

---

## 🔁 Benchmark Refresh Policy

- Live: compare all scoring cycles against benchmarks  
- End-of-Day: update reinforcement weights based on trade deviation  
- Weekly: sync performance insights to `reinforcement_profile.json`  
- Monthly: use `qthink_backtest.py` to regenerate updated benchmark reference

---

## 🧠 Final Directive

Benchmarks are not boundaries — they are **realized constraints of edge**.

QThink must not exceed or disregard these unless:
- Statistical sample is strong
- Justification is logged
- Reinforcement supports the deviation

**Good trades may lose. Bad trades must never be repeated.**
