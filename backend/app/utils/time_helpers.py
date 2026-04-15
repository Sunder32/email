import random
from datetime import datetime, timezone


def random_delay(min_sec: float, max_sec: float) -> float:
    return random.uniform(min_sec, max_sec)


def calc_eta(sent: int, total: int, started_at: datetime | None) -> float | None:
    if not started_at or sent == 0 or total == 0:
        return None
    elapsed = (datetime.now(timezone.utc) - started_at).total_seconds()
    rate = sent / elapsed
    remaining = total - sent
    return remaining / rate


def elapsed_seconds(started_at: datetime | None) -> float | None:
    if not started_at:
        return None
    return (datetime.now(timezone.utc) - started_at).total_seconds()
