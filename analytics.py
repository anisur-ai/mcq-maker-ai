import streamlit as st
from datetime import datetime, timezone
from supabase import create_client


# --------------------------------
# Supabase Connection
# --------------------------------

def get_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]

        if not url or not key:
            return None

        return create_client(url, key)

    except Exception:
        return None


# --------------------------------
# Log User Activity
# --------------------------------

def log_usage(user_id, event_type="visit", question_count=0):

    supabase = get_supabase()

    if supabase is None:
        return False

    now = datetime.now(timezone.utc).isoformat()

    try:

        # Check whether this user already exists
        result = (
            supabase
            .table("usage_logs")
            .select("*")
            .eq("user_id", str(user_id))
            .limit(1)
            .execute()
        )

        # --------------------------------
        # Existing User
        # --------------------------------

        if result.data:

            row = result.data[0]

            old_count = int(
                row.get("question_count") or 0
            )

            new_count = old_count + int(
                question_count
            )

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

        # --------------------------------
        # New User
        # --------------------------------

        else:

            (
                supabase
                .table("usage_logs")
                .insert({
                    "user_id": str(user_id),
                    "started_at": now,
                    "last_active": now,
                    "event_type": event_type,
                    "question_count": int(
                        question_count
                    ),
                })
                .execute()
            )

        return True

    except Exception as e:

        print("Analytics Error:", e)

        return False
