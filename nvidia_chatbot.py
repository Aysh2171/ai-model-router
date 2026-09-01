"""
Standalone NVIDIA NIM / API Chatbot Proof-of-Concept
Connects to https://integrate.api.nvidia.com/v1 using OpenAI-compatible SDK.
"""

import os
import sys
import time
from typing import List, Dict, Optional
from openai import OpenAI, RateLimitError, APIError

# Default Configuration
BASE_URL = "https://integrate.api.nvidia.com/v1"
API_KEY = os.environ.get(
    "NVIDIA_API_KEY", 
    "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"
)

# Known embedding / non-chat models to filter out from default chat list
NON_CHAT_KEYWORDS = [
    "embed", "reward", "parse", "detector", "clip", "fuyu", "deplot", 
    "kosmos", "neva", "synthetic", "calibration"
]

def get_client() -> OpenAI:
    """Initialize OpenAI client configured for NVIDIA NIM endpoint."""
    return OpenAI(base_url=BASE_URL, api_key=API_KEY)

def fetch_available_models(client: OpenAI) -> List[str]:
    """Query the NVIDIA /v1/models endpoint and return sorted model IDs."""
    try:
        models_data = client.models.list()
        all_models = [m.id for m in models_data.data]
        return sorted(all_models)
    except Exception as e:
        print(f"[Error fetching models]: {e}")
        # Fallback list of known verified chat models
        return [
            "z-ai/glm-5.2",
            "meta/llama-3.3-70b-instruct",
            "mistralai/mistral-large-2-instruct",
            "deepseek-ai/deepseek-v4-flash-0731",
            "nvidia/llama-3.1-nemotron-70b-instruct",
            "google/gemma-3-12b-it",
            "minimaxai/minimax-m3"
        ]

def filter_chat_models(models: List[str]) -> List[str]:
    """Filter models to only include conversational/chat-capable models."""
    chat_models = []
    for model_id in models:
        lower_id = model_id.lower()
        if not any(kw in lower_id for kw in NON_CHAT_KEYWORDS):
            chat_models.append(model_id)
    return chat_models

def display_model_selection(models: List[str]) -> str:
    """Display numbered list of models and prompt user for selection."""
    print("\n" + "=" * 60)
    print("AVAILABLE NVIDIA CHAT MODELS:")
    print("=" * 60)
    
    # Highlight verified popular models first
    featured = [
        "z-ai/glm-5.2",
        "meta/llama-3.3-70b-instruct",
        "mistralai/mistral-large-2-instruct",
        "deepseek-ai/deepseek-v4-flash-0731",
        "nvidia/llama-3.1-nemotron-70b-instruct",
        "google/gemma-3-12b-it",
        "minimaxai/minimax-m3",
    ]
    
    top_models = [m for m in featured if m in models]
    other_models = [m for m in models if m not in top_models]
    ordered_models = top_models + other_models

    for idx, model_id in enumerate(ordered_models, 1):
        tag = " [Featured / Verified]" if model_id in top_models else ""
        print(f"  {idx:2d}. {model_id}{tag}")
    
    print("=" * 60)
    
    while True:
        try:
            choice = input(f"\nSelect a model number (1-{len(ordered_models)}) [Default: 1]: ").strip()
            if not choice:
                return ordered_models[0]
            choice_num = int(choice)
            if 1 <= choice_num <= len(ordered_models):
                return ordered_models[choice_num - 1]
            print(f"Please enter a number between 1 and {len(ordered_models)}.")
        except (ValueError, EOFError):
            return ordered_models[0]

def send_chat_completion(client: OpenAI, model: str, history: List[Dict[str, str]], max_retries: int = 3) -> str:
    """Send chat request with automatic exponential backoff on 429 rate limits."""
    delay = 2.0
    for attempt in range(1, max_retries + 1):
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=history,
                temperature=0.7,
                max_tokens=1024,
            )
            return completion.choices[0].message.content or ""
        except (RateLimitError, APIError) as e:
            error_msg = str(e)
            if "429" in error_msg or isinstance(e, RateLimitError):
                if attempt < max_retries:
                    print(f"  [Rate limit 429 encountered. Retrying in {delay:.1f}s (attempt {attempt}/{max_retries})...]")
                    time.sleep(delay)
                    delay *= 2
                    continue
            raise e

def run_chatbot(selected_model: Optional[str] = None):
    """Run interactive or scripted chatbot session with conversation memory."""
    print("=" * 60)
    print("NVIDIA NIM / API Proof-of-Concept Chatbot")
    print("Endpoint: https://integrate.api.nvidia.com/v1")
    print("=" * 60)
    
    client = get_client()
    
    all_models = fetch_available_models(client)
    chat_models = filter_chat_models(all_models)
    
    if not selected_model:
        selected_model = display_model_selection(chat_models)
    
    print(f"\n[Active Model]: {selected_model}")
    print("Type your message and press Enter.")
    print("Type 'exit', 'quit', or press Ctrl+C to terminate session.\n")
    print("-" * 60)
    
    history: List[Dict[str, str]] = [
        {
            "role": "system", 
            "content": "You are a helpful, knowledgeable, and concise AI assistant."
        }
    ]
    
    while True:
        try:
            user_prompt = input("\nYou > ").strip()
            if not user_prompt:
                continue
            if user_prompt.lower() in ("exit", "quit", "q"):
                print("\nExiting chatbot. Goodbye!")
                break
                
            history.append({"role": "user", "content": user_prompt})
            
            print(f"\nAssistant ({selected_model}) is thinking...\n")
            
            assistant_reply = send_chat_completion(client, selected_model, history)
            print(f"Assistant > {assistant_reply.strip()}\n")
            
            history.append({"role": "assistant", "content": assistant_reply})
            
        except KeyboardInterrupt:
            print("\nSession interrupted by user. Goodbye!")
            break
        except EOFError:
            print("\nEOF received. Exiting session.")
            break
        except Exception as e:
            print(f"\n[Error during generation]: {e}")
            print("You can try another message, or enter 'exit' to quit.")

if __name__ == "__main__":
    cli_model = sys.argv[1] if len(sys.argv) > 1 else None
    run_chatbot(selected_model=cli_model)
