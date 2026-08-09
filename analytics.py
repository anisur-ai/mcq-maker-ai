import streamlit as st
from datetime import datetime


def track_event(event_name, details=None):
    """Track a simple app event."""
    try:
        if "analytics_events" not in st.session_state:
            st.session_state.analytics_events = []

        st.session_state.analytics_events.append({
            "event": event_name,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })

    except Exception:
        # Analytics কখনো মূল app-কে বন্ধ করবে না
        pass


def get_events():
    """Return stored analytics events."""
    return st.session_state.get("analytics_events", [])


def clear_events():
    """Clear analytics events."""
    if "analytics_events" in st.session_state:
        st.session_state.analytics_events = []
