import threading
from collections import defaultdict


MAX_AZURE_OPENAI_5_REQUESTS =12


class SessionRateLimiter:

    def __init__(self):
        self._counters = defaultdict(int)
        self._lock = threading.Lock()

    def try_acquire_azure_openai_5(self, session_id: str) -> bool:

        with self._lock:
            current_count = self._counters[session_id]
            print(current_count)
            if current_count >= MAX_AZURE_OPENAI_5_REQUESTS:
                return False

            self._counters[session_id] = current_count + 1
            return True

        return None

    def get_count(self, session_id: str) -> int:

        with self._lock:
            return self._counters.get(session_id, 0)
        return None


rate_limiter = SessionRateLimiter()