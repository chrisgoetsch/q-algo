# Memory Refresh Behavior — Q-ALGO v2

---

## Reinforcement Memory (`reinforcement_profile.json`)

- **Updated After**: Each successful trade exit (live and backtest)
- **Structure**: Stores aggregated outcomes by setup archetype ID
- **Retention**: Append-only during live trading, daily archival recommended

---

## Refresh Cadence

| Context         | Action                         |
|-----------------|--------------------------------|
| Live Trading    | Update reinforcement after every exit |
| Daily Maintenance | Archive reinforcement_profile.json with timestamp |
| Backtesting     | Update reinforcement after every simulated exit |

---

## Naming Conventions

- All memory files use **snake_case** (e.g., `reinforcement_profile.json`)
- Memory-related scripts and logs should use the `/assistants/` folder.

---

**Note**: Full schema validation for memory files to be introduced in v2.2.

