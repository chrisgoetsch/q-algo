# File: utils/gpt_resilient_call.py

import time
import random
import openai

MAX_GPT_RETRIES = 5
BASE_SLEEP_SECONDS = 1

def safe_chat_completion_request(messages, model="gpt-4o", temperature=0.2, max_tokens=500):
    """
    Safe GPT call with retry and exponential backoff.
    """
    retries = 0

    while retries < MAX_GPT_RETRIES:
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                n=1
            )
            return response['choices'][0]['message']['content'].strip()

        except openai.error.OpenAIError as e:
            print(f"[GPT Resilience] OpenAI API error: {e}. Retrying...")
        except Exception as e:
            print(f"[GPT Resilience] General error: {e}. Retrying...")

        retries += 1
        sleep_time = BASE_SLEEP_SECONDS * (2 ** retries) + random.uniform(0, 1)
        time.sleep(sleep_time)

    print("[GPT Resilience] Failed after max retries.")
    return "Reasoning unavailable due to GPT failure."
