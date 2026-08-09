import os
from datetime import datetime, timezone, timedelta

from supabase import create_client


def get_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        return None

    return create_client(url, key)


def log_usage(user_id, event_type="visit", question_count=0):
    supabase = get_supabase()

    if supabase is None:
        return False

    now = datetime.now(timezone.utc).isoformat()

    try:
        existing = (
            supabase
            .table("usage_logs")
            .select("*")
            .eq("user_id", str(user_id))
            .limit(1)
            .execute()
        )

        if existing.data:
            row = existing.data[0]

            new_count = int(row.get("question_count") or 0) + int(question_count)

            (
                supabase
                .table("usage_logs")
                .update({
                    "last_active": now,
                    "event_type": event_type,
                    "question_count": new_count,
                })
                .eq("id", row["id"])
                .execute()
            )

        else:
            (
                supabase
                .table("usage_logs")
                .insert({
                    "user_id": str(user_id),
                    "started_at": now,
                    "last_active": now,
                    "event_type": event_type,
                    "question_count": int(question_count),
                })
                .execute()
            )

        return True

    except Exception:
        return False
