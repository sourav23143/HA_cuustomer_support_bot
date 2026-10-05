"""
HealthAssist AI Support Agent — Streamlit UI

Professional demo interface with:
- Left sidebar: user selector + context
- Center: chat interface
- Right sidebar: agent trace
"""

import streamlit as st
import httpx
import json

# ── Configuration ────────────────────────────────────────────

API_BASE_URL = "http://localhost:8000"

st.set_page_config(
    page_title="HealthAssist AI Support",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────

st.markdown("""
<style>
    /* Main theme */
    .main .block-container {
        padding-top: 1rem;
        max-width: 100%;
    }

    /* Chat message styling */
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px 18px;
        border-radius: 18px 18px 4px 18px;
        margin: 8px 0;
        max-width: 85%;
        float: right;
        clear: both;
        font-size: 0.95rem;
    }

    .assistant-message {
        background: #f0f2f6;
        color: #1a1a2e;
        padding: 12px 18px;
        border-radius: 18px 18px 18px 4px;
        margin: 8px 0;
        max-width: 85%;
        float: left;
        clear: both;
        font-size: 0.95rem;
    }

    /* Trace styling */
    .trace-item {
        padding: 8px 12px;
        margin: 4px 0;
        border-radius: 8px;
        font-size: 0.85rem;
        border-left: 3px solid;
    }

    .trace-success {
        background: #e8f5e9;
        border-color: #4caf50;
        color: #2e7d32;
    }

    .trace-failed {
        background: #ffebee;
        border-color: #f44336;
        color: #c62828;
    }

    /* Header */
    .app-header {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        color: white;
        padding: 15px 25px;
        border-radius: 12px;
        margin-bottom: 20px;
        text-align: center;
    }

    .app-header h1 {
        margin: 0;
        font-size: 1.5rem;
        font-weight: 600;
    }

    .app-header p {
        margin: 4px 0 0 0;
        opacity: 0.8;
        font-size: 0.85rem;
    }

    /* Info card */
    .info-card {
        background: #f8f9fa;
        padding: 12px 16px;
        border-radius: 10px;
        margin: 8px 0;
        border: 1px solid #e9ecef;
    }

    .info-label {
        font-size: 0.75rem;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 2px;
    }

    .info-value {
        font-size: 0.95rem;
        font-weight: 500;
        color: #212529;
    }

    /* Ticket badge */
    .ticket-badge {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
    }

    /* Status badges */
    .status-badge {
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 500;
        display: inline-block;
    }

    .status-success { background: #d4edda; color: #155724; }
    .status-failed { background: #f8d7da; color: #721c24; }
    .status-pending { background: #fff3cd; color: #856404; }
    .status-scheduled { background: #d1ecf1; color: #0c5460; }

    div[data-testid="stSidebarContent"] {
        padding-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# ── Helper functions ─────────────────────────────────────────

def api_call(method: str, endpoint: str, **kwargs):
    """Make an API call to the FastAPI backend."""
    try:
        with httpx.Client(timeout=60.0) as client:
            url = f"{API_BASE_URL}{endpoint}"
            if method == "GET":
                response = client.get(url)
            elif method == "POST":
                response = client.post(url, json=kwargs.get("json"))

            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"API Error: {response.status_code}")
                return None
    except httpx.ConnectError:
        st.error("⚠️ Cannot connect to the API server. Make sure FastAPI is running on port 8000.")
        return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None


def get_status_badge(status: str) -> str:
    """Get HTML for a status badge."""
    css_class = {
        "success": "status-success",
        "completed": "status-success",
        "failed": "status-failed",
        "pending": "status-pending",
        "scheduled": "status-scheduled",
        "refunded": "status-pending",
        "cancelled": "status-failed",
        "in_progress": "status-success",
    }.get(status, "status-pending")
    return f'<span class="status-badge {css_class}">{status}</span>'


# ── Session state initialization ─────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

if "selected_user" not in st.session_state:
    st.session_state.selected_user = None

if "user_details" not in st.session_state:
    st.session_state.user_details = None

if "latest_trace" not in st.session_state:
    st.session_state.latest_trace = []

if "latest_intent" not in st.session_state:
    st.session_state.latest_intent = None

if "latest_confidence" not in st.session_state:
    st.session_state.latest_confidence = None

if "latest_ticket" not in st.session_state:
    st.session_state.latest_ticket = None


# ── Header ───────────────────────────────────────────────────

st.markdown("""
<div class="app-header">
    <h1>🏥 HealthAssist AI Support Agent</h1>
    <p>Intelligent customer support powered by LangGraph + Groq + Qdrant RAG</p>
</div>
""", unsafe_allow_html=True)


# ── Layout: three columns ───────────────────────────────────

left_col, center_col, right_col = st.columns([1.2, 2.5, 1.3])


# ── LEFT SIDEBAR: User Selector ─────────────────────────────

with left_col:
    st.markdown("### 👤 Demo User")

    # Fetch demo users
    users_data = api_call("GET", "/api/demo/users")

    if users_data and "users" in users_data:
        users = users_data["users"]
        user_options = {
            f"{u['name']} ({u['user_id']})": u['user_id']
            for u in users
        }

        selected = st.selectbox(
            "Select a patient:",
            options=list(user_options.keys()),
            key="user_selector",
        )

        if selected:
            user_id = user_options[selected]

            # Reset conversation when user changes
            if st.session_state.selected_user != user_id:
                st.session_state.selected_user = user_id
                st.session_state.messages = []
                st.session_state.conversation_id = None
                st.session_state.latest_trace = []
                st.session_state.latest_intent = None
                st.session_state.latest_confidence = None
                st.session_state.latest_ticket = None
                st.rerun()

            # Fetch user details
            if st.session_state.selected_user:
                details = api_call("GET", f"/api/demo/users/{st.session_state.selected_user}")

                if details and "user" in details:
                    st.session_state.user_details = details

                    user = details["user"]
                    st.markdown(f"""
                    <div class="info-card">
                        <div class="info-label">User ID</div>
                        <div class="info-value">{user['user_id']}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown(f"""
                    <div class="info-card">
                        <div class="info-label">Name</div>
                        <div class="info-value">{user['name']}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown(f"""
                    <div class="info-card">
                        <div class="info-label">City</div>
                        <div class="info-value">{user.get('city', 'N/A')}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Consultation info
                    consultation = details.get("consultation")
                    if consultation:
                        st.markdown("---")
                        st.markdown("#### 📋 Latest Consultation")
                        st.markdown(f"""
                        <div class="info-card">
                            <div class="info-label">Consultation ID</div>
                            <div class="info-value">{consultation['consultation_id']}</div>
                        </div>
                        """, unsafe_allow_html=True)

                        st.markdown(f"""
                        <div class="info-card">
                            <div class="info-label">Status</div>
                            <div class="info-value">{get_status_badge(consultation['status'])}</div>
                        </div>
                        """, unsafe_allow_html=True)

                        if details.get("doctor"):
                            st.markdown(f"""
                            <div class="info-card">
                                <div class="info-label">Doctor</div>
                                <div class="info-value">{details['doctor']['name']}</div>
                            </div>
                            """, unsafe_allow_html=True)

                    # Payment info
                    payment = details.get("payment")
                    if payment:
                        st.markdown("---")
                        st.markdown("#### 💳 Payment")
                        st.markdown(f"""
                        <div class="info-card">
                            <div class="info-label">Amount</div>
                            <div class="info-value">₹{payment['amount']} {get_status_badge(payment['status'])}</div>
                        </div>
                        """, unsafe_allow_html=True)

    else:
        st.warning("No users found. Run seed script first.")
        st.code("python scripts/seed_demo_data.py", language="bash")

    # New conversation button
    st.markdown("---")
    if st.button("🔄 New Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.conversation_id = None
        st.session_state.latest_trace = []
        st.session_state.latest_intent = None
        st.session_state.latest_confidence = None
        st.session_state.latest_ticket = None
        st.rerun()


# ── CENTER: Chat Interface ───────────────────────────────────

with center_col:
    st.markdown("### 💬 Support Chat")

    # Chat container
    chat_container = st.container(height=500)

    with chat_container:
        if not st.session_state.messages:
            st.markdown(
                '<p style="text-align: center; color: #999; padding: 40px 0;">'
                '👋 Select a user and start chatting!<br>'
                '<small>Try: "Where is my doctor?" or "I paid but doctor didn\'t join"</small>'
                '</p>',
                unsafe_allow_html=True,
            )

        for msg in st.session_state.messages:
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.write(msg["content"])
            else:
                with st.chat_message("assistant", avatar="🏥"):
                    st.write(msg["content"])

    # Input
    if st.session_state.selected_user:
        user_input = st.chat_input("Type your support message...")

        if user_input:
            # Add user message
            st.session_state.messages.append({
                "role": "user",
                "content": user_input,
            })

            # Call API
            with st.spinner("🤖 Agent thinking..."):
                result = api_call(
                    "POST",
                    "/api/chat",
                    json={
                        "user_id": st.session_state.selected_user,
                        "message": user_input,
                        "conversation_id": st.session_state.conversation_id,
                    },
                )

            if result:
                # Store conversation ID
                st.session_state.conversation_id = result["conversation_id"]

                # Add assistant message
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result["response"],
                })

                # Update trace
                st.session_state.latest_trace = result.get("trace", [])
                st.session_state.latest_intent = result.get("intent")
                st.session_state.latest_confidence = result.get("confidence")
                st.session_state.latest_ticket = result.get("ticket_id")

            st.rerun()
    else:
        st.info("👈 Select a demo user from the left panel to start chatting.")


# ── RIGHT SIDEBAR: Agent Trace ───────────────────────────────

with right_col:
    st.markdown("### 🔍 Agent Trace")

    if st.session_state.latest_intent:
        # Intent badge
        intent = st.session_state.latest_intent
        confidence = st.session_state.latest_confidence or 0

        conf_color = "#4caf50" if confidence > 0.7 else "#ff9800" if confidence > 0.5 else "#f44336"

        st.markdown(f"""
        <div class="info-card">
            <div class="info-label">Detected Intent</div>
            <div class="info-value">{intent.replace('_', ' ').title()}</div>
            <div style="margin-top: 4px;">
                <span style="color: {conf_color}; font-weight: 600;">
                    Confidence: {confidence:.0%}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    if st.session_state.latest_ticket:
        st.markdown(f"""
        <div style="text-align: center; margin: 10px 0;">
            <span class="ticket-badge">🎫 {st.session_state.latest_ticket}</span>
        </div>
        """, unsafe_allow_html=True)

    # Trace events
    if st.session_state.latest_trace:
        st.markdown("---")

        for event in st.session_state.latest_trace:
            status = event.get("status", "success")
            icon = "✓" if status == "success" else "✗" if status == "failed" else "○"
            css = "trace-success" if status == "success" else "trace-failed"

            st.markdown(f"""
            <div class="trace-item {css}">
                <strong>{icon} {event['step']}</strong><br>
                <small>{event['detail']}</small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(
            '<p style="text-align: center; color: #999; padding: 30px 0; font-size: 0.9rem;">'
            'Send a message to see the agent trace here.'
            '</p>',
            unsafe_allow_html=True,
        )

    # Conversation ID
    if st.session_state.conversation_id:
        st.markdown("---")
        st.markdown(f"""
        <div class="info-card">
            <div class="info-label">Conversation ID</div>
            <div class="info-value" style="font-size: 0.8rem;">{st.session_state.conversation_id}</div>
        </div>
        """, unsafe_allow_html=True)
