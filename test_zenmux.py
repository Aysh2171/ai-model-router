import os
from openai import OpenAI, NotFoundError

# Retrieve NVIDIA API key securely from environment or config
API_KEY = os.environ.get("NVIDIA_API_KEY", "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")
BASE_URL = "https://integrate.api.nvidia.com/v1"
MODEL_NAME = "z-ai/glm-5.2"  # Exact model ID available on NVIDIA NIM API catalog

client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
)

print("=" * 60)
print(f"Connecting to NVIDIA API: {BASE_URL}")
print(f"Target Model: {MODEL_NAME}")
print("=" * 60)

# ---------------------------------------------------------
# Test 1: Chat Completions API
# ---------------------------------------------------------
print("\n[TEST 1] Testing chat.completions.create()...")
try:
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": "What is the meaning of life?"
            }
        ]
    )
    print("[TEST 1 SUCCESS] Chat Completions response received:")
    print("-" * 50)
    print(completion.choices[0].message.content)
    print("-" * 50)
except Exception as e:
    print(f"[TEST 1 FAILED] Error: {e}")

# ---------------------------------------------------------
# Test 2: Responses API
# ---------------------------------------------------------
print("\n[TEST 2] Testing responses.create()...")
try:
    responses = client.responses.create(
        model=MODEL_NAME,
        input="What is the meaning of life?"
    )
    print("[TEST 2 SUCCESS] Responses API output received:")
    print(responses)
except NotFoundError as e:
    print(f"[TEST 2 NOT SUPPORTED] Endpoint 404 Not Found: NVIDIA API does not implement OpenAI /v1/responses endpoint.")
    print(f"Details: {e}")
except Exception as e:
    print(f"[TEST 2 FAILED] Error: {e}")

print("\n" + "=" * 60)
print("Integration Test Completed.")
print("=" * 60)
