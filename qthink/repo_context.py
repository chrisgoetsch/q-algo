import os
from pathlib import Path

def get_context_snippets():
    files = [
        "core/trade_engine.py",
        "core/entry_learner.py",
        "mesh/q_0dte.py",
        "analytics/q_backtest.py",
        "run_q_algo_live_async.py",
        "runtime_state.json"
    ]
    base = Path(__file__).parent.parent / "q-algo-v2"
    snippets = []
    for file in files:
        path = base / file
        if path.exists():
            content = path.read_text(encoding='utf-8')[:1500]  # Truncate
            snippets.append(f"# {file}\n{content}")
    return "\n\n".join(snippets)
