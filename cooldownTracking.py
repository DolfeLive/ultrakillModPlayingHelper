from datetime import datetime, timedelta, timezone

USER_COOLDOWNS: dict[int, datetime] = {}
COOLDOWN_SECONDS = 5

def can_run(user_id: int) -> bool:
    now = datetime.now(timezone.utc)
    return user_id not in USER_COOLDOWNS or now >= USER_COOLDOWNS[user_id]

def update_cooldown(user_id: int):
    USER_COOLDOWNS[user_id] = datetime.now(timezone.utc) + timedelta(seconds=COOLDOWN_SECONDS)

def remaining_time(user_id: int) -> int:
    return max(0, (USER_COOLDOWNS[user_id] - datetime.now(timezone.utc)).seconds)
