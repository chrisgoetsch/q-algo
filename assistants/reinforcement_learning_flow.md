# QThink Reinforcement Learning Flow
## Memory File for Assistant ID: asst_cgNdVhlPA9P1IdPBlQTlJM0U

---

## 🧠 Purpose

This file defines how QThink processes completed trades into regret scores, mesh agent reinforcement signals, timing insights, and behavioral improvements.

The system is designed to evolve QThink’s intelligence with every trade by learning from past outcomes — not just PnL, but **contextual failure and pattern misalignment**.

---

## 🔁 Core Learning Cycle

Every completed SPY 0DTE trade flows through this loop:

1. **Outcome Assessment**  
2. **Regret Scoring** (0DTE-enhanced)  
3. **Time Block Tagging**  
4. **Agent Attribution**  
5. **Setup Archetype Classification**  
6. **Reinforcement Adjustment**  
7. **Memory & Pattern Logging**

---

## 1️⃣ Outcome Assessment

Logged for every trade:

- Realized PnL  
- Duration held  
- Entry & exit timestamps  
- Entry/exit trade scores  
- Active mesh agent contributions  
- Regime/environment tags (e.g. GEX flip, macro event, low IV)

---

## 2️⃣ 0DTE-Specific Regret Scoring

Each trade is scored `0.0–1.0` for these regret dimensions:

| Regret Type        | Description |
|--------------------|-------------|
| `entry_regret`     | Premature or late entry relative to better setups |
| `exit_regret`      | Missed continuation or overstayed into reversal |
| `timing_regret`    | Entered during low-alignment or mid-day chop |
| `decay_regret`     | Entered after theta decay was dominant |
| `pin_regret`       | Entered near max pain or dealer pin zone |
| `trap_entry_regret`| Walked into a dealer-induced trap or false breakout |
| `late_exit_regret` | Held too long into VWAP magnet or expiry crush |

High regret scores are flagged for reinforcement review.

> If `entry_regret + exit_regret + decay_regret > 2.0`, classify trade as a `model_failure`.

---

## 3️⃣ Time-of-Day Tagging

Each trade is tagged with its **time block**, used for regret and success pattern detection:

| Time Tag       | Session |
|----------------|---------|
| `early_open`   | 9:30–10:30 (high-momentum)  
| `chop_mid`     | 10:30–12:30 (high regret zone)  
| `setup_mid`    | 12:30–2:30 (re-entry, gamma builds)  
| `decay_close`  | 2:30–4:00 (alpha decay, pin risk)

Logged in `sync_log.jsonl` and `qthink_journal_summary.json`.

---

## 4️⃣ Mesh Agent Attribution

QThink must log:

- Agents involved in entry and exit  
- Agent scores and weights  
- Signal polarity (bullish/bearish)  
- Alignment with outcome  
- If agent conflicted with final direction  
- If trade occurred during **mesh confusion** (alignment < 0.6)

Trades with misaligned signals that lead to regret are flagged as `conflict_failure`.

---

## 5️⃣ Setup Archetype Classification

Each trade is assigned a `setup_archetype` for pattern learning:

| Archetype        | Description |
|------------------|-------------|
| `momentum_break` | Entered on breakout with agent alignment |
| `fade_reversal`  | Entered on rejection of key level |
| `gamma_flip`     | Triggered by dealer GEX/DEX shift |
| `trap_avoidance` | High-confidence avoidance of trap entry |
| `pin_fade`       | Faded SPY near max pain with confirmation |

These tags power clustering in `journal/trade_clusters.json` and improve reinforcement loop quality.

---

## 6️⃣ Reinforcement Adjustment

### 🔸 Agent Weight Update

Each trade updates `reinforcement_weight` for each agent:

- High alignment + positive PnL → weight increased (up to +20%)  
- High regret or signal failure → weight decreased (up to -30%)  

Reinforcement profile is stored in:
- `mesh_config.json`  
- `reinforcement_profile.json`

### 🔸 Penalty Factor Injection

Trades with significant regret trigger `penalty_factor` flags:

| Condition | Penalty |
|-----------|---------|
| Regret sum > 2.5 | +10 |
| Exit_regret + late_exit_regret > 1.5 | +15 |
| Conflict failure | +20 |

Penalties are passed to `signal_scoring_logic.md` for use in future scoring.

---

## 7️⃣ Memory & Pattern Logging

### 🔹 Key Logs:

| File | Purpose |
|------|---------|
| `sync_log.jsonl` | Chronological trade + regret summary |
| `qthink_journal_summary.json` | Meta pattern journaling |
| `mesh_logger.jsonl` | Agent-level signal analysis |
| `journal/trade_clusters.json` | Archetype grouping |
| `mesh_confusion_log.jsonl` | Agent conflict archives |

### 🔹 Optional Memory Triggers:

QThink may commit patterns to Assistant memory if:

- A specific archetype is producing repeat losses or wins  
- A regret score consistently correlates with time-of-day  
- A particular agent repeatedly leads to alpha or decay

---

## 📊 Logged Data Schema

| Field | Description |
|-------|-------------|
| `timestamp`         | Time of trade exit |
| `pnl`               | Realized profit/loss |
| `entry_score`       | Score at entry |
| `exit_score`        | Score at exit |
| `entry_regret`      | 0–1 |
| `exit_regret`       | 0–1 |
| `timing_regret`     | 0–1 |
| `decay_regret`      | 0–1 |
| `pin_regret`        | 0–1 |
| `trap_entry_regret` | 0–1 |
| `late_exit_regret`  | 0–1 |
| `agents_involved`   | List of mesh agents |
| `agent_weights`     | Score contributions |
| `mesh_conflict`     | Boolean |
| `setup_archetype`   | Trade type label |
| `time_block`        | Entry time segment |
| `final_label`       | `good_trade`, `conflict_failure`, `model_failure`, etc. |

---

## 🧠 Final Directive

QThink’s growth comes from the **compound intelligence of experience**.

Every regret must translate into a sharper decision.  
Every failure into a future signal filter.  
Every win into an understood edge — not luck.

QThink must use reinforcement not just to optimize trades, but to **optimize itself**.

