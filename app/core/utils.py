import time
import random
from mistralai.models.sdkerror import SDKError


def retry_with_backoff(func, max_retries=10, base_delay=1.5, jitter=0.5, *args, **kwargs):
    """
    Retry Mistral API calls with exponential backoff and jitter.
    """
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except SDKError as e:
            if "429" in str(e) or "rate limit" in str(e).lower():
                wait = base_delay * (2 ** attempt/2) + random.uniform(0, jitter)
                print(f"[WARN] Rate limited. Retrying ({attempt+1}/{max_retries}) in {wait:.1f}s...")
                time.sleep(wait)
                continue
            else:
                raise e
    raise RuntimeError("Max retries exceeded for Mistral API call.")
