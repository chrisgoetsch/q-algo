import core.entry_learner

print("✅ Module loaded from:", core.entry_learner.__file__)
print("🔍 Available symbols:\n", dir(core.entry_learner))

try:
    from core.entry_learner import evaluate_entry
    print("✅ 'evaluate_entry' successfully imported")
except ImportError as e:
    print("❌ ImportError:", e)
