import os
import json
import datetime
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Configure OpenAI client
openai.api_key = OPENAI_API_KEY

# Define file paths
LOG_DIR = "logs"
SYNC_LOG = os.path.join(LOG_DIR, "sync_log.jsonl")
MESH_LOG = os.path.join(LOG_DIR, "mesh_logger.jsonl")
REINFORCEMENT_PROFILE = os.path.join(LOG_DIR, "reinforcement_profile.json")
ALPHA_LOG_DIR = os.path.join(LOG_DIR, "daily_alpha_logs")

# Ensure necessary folders exist
os.makedirs(ALPHA_LOG_DIR, exist_ok=True)

# Helper to read JSONL
def read_jsonl(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r") as f:
        return [json.loads(line.strip()) for line in f if line.strip()]

# Helper to write JSON
def write_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

# Pull recent memory
def gather_recent_memory():
    sync_data = read_jsonl(SYNC_LOG)
    mesh_data = read_jsonl(MESH_LOG)
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    daily_alpha_file = os.path.join(ALPHA_LOG_DIR, f"daily_alpha_log_{today_str}.json")
    daily_alpha = {}
    if os.path.exists(daily_alpha_file):
        with open(daily_alpha_file, "r") as f:
            daily_alpha = json.load(f)
    return sync_data, mesh_data, daily_alpha

# Call GPT to compress memory
def compress_memory(sync_data, mesh_data, daily_alpha):
    prompt = f"""
You are QThink, a quantitative trading memory optimizer.
Given today's trading memory below:

- Trades executed (sync_log): {sync_data}
- Agent signals (mesh_logger): {mesh_data}
- Daily alpha notes: {daily_alpha}

Summarize the key lessons, trade types that worked, agent strengths/weaknesses, and areas to improve.
Output JSON format:
{{
  "lessons_learned": [],
  "successful_trade_patterns": [],
  "mesh_agent_strengths": {{}},
  "mesh_agent_weaknesses": {{}},
  "recommended_reinforcements": []
}}
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a quant trading optimizer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        result = response['choices'][0]['message']['content']
        return json.loads(result)
    except Exception as e:
        print("Error during GPT compression:", e)
        return None

# Update reinforcement_profile.json
def update_reinforcement_profile(new_memory):
    if not os.path.exists(REINFORCEMENT_PROFILE):
        current_profile = {}
    else:
        with open(REINFORCEMENT_PROFILE, "r") as f:
            current_profile = json.load(f)

    timestamp = datetime.datetime.now().isoformat()
    current_profile[timestamp] = new_memory
    write_json(REINFORCEMENT_PROFILE, current_profile)

# Main runner
if __name__ == "__main__":
    sync_data, mesh_data, daily_alpha = gather_recent_memory()
    if not sync_data and not mesh_data:
        print("No new memory to compress today.")
        exit()

    new_memory = compress_memory(sync_data, mesh_data, daily_alpha)
    if new_memory:
        update_reinforcement_profile(new_memory)
        print("Memory compression and reinforcement update complete.")
    else:
        print("Compression failed.")
