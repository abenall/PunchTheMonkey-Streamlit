import os
import time
import json
import streamlit as st

from google.cloud import dialogflow_v2 as dialogflow
from google.oauth2 import service_account
from google.protobuf.json_format import MessageToDict

# ---------------------------------------------------------
# 1. AUTHENTICATION (STREAMLIT CLOUD SAFE)
# ---------------------------------------------------------
# ---------------------------------------------------------
# 1. AUTHENTICATION (STREAMLIT CLOUD SAFE + LOCAL SAFE)
# ---------------------------------------------------------
use_cloud_creds = (
    hasattr(st, "secrets")
    and "dialogflow" in st.secrets
    and "credentials" in st.secrets["dialogflow"]
)

if use_cloud_creds:
    creds_dict = st.secrets["dialogflow"]["credentials"]
    credentials = service_account.Credentials.from_service_account_info(creds_dict)
    PROJECT_ID = st.secrets["dialogflow"]["project_id"]
else:
    credentials = service_account.Credentials.from_service_account_file(
        "punchthemonkey-streamlit-key.json"
    )
    PROJECT_ID = "punchthemonkey-bmtm"

# Create Dialogflow session client
session_client = dialogflow.SessionsClient(credentials=credentials)
SESSION_ID = "streamlit-session"
session_path = session_client.session_path(PROJECT_ID, SESSION_ID)

# ---------------------------------------------------------
# 2. STREAMLIT PAGE SETUP
# ---------------------------------------------------------
st.set_page_config(page_title="Punch The Monkey Chatbot", page_icon="🐒")

st.title("🐒 Punch The Monkey - Dialogflow Chatbot")

st.markdown(
    """
    <div style='padding:10px;background-color:#1e1e1e;border-radius:10px;
    margin-bottom:15px;color:#ccc;text-align:center;'>
        <b>Welcome to PunchTheMonkey — Your Dialogflow Chatbot</b>
    </div>
    """,
    unsafe_allow_html=True
)

# Sidebar clear chat button
if st.sidebar.button("Clear Chat"):
    st.session_state.messages = []
    st.experimental_rerun()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Avatars
PUNCH_AVATAR = "🐒"
USER_AVATAR = "🧑"

# ---------------------------------------------------------
# 3. FUNCTION TO SEND MESSAGE TO DIALOGFLOW
# ---------------------------------------------------------
def send_to_dialogflow(text):
    text_input = dialogflow.TextInput(text=text, language_code="en")
    query_input = dialogflow.QueryInput(text=text_input)

    response = session_client.detect_intent(
        request={"session": session_path, "query_input": query_input}
    )
    return response

# ---------------------------------------------------------
# 4. DISPLAY CHAT HISTORY
# ---------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=msg["avatar"]):
        st.markdown(
            f"""
            <div style='background-color:{msg["bg"]};padding:10px;border-radius:10px;
            max-width:70%;margin-bottom:5px;color:white;'>
                {msg["content"]}
            </div>
            """,
            unsafe_allow_html=True
        )

# ---------------------------------------------------------
# 5. USER INPUT
# ---------------------------------------------------------
user_input = st.chat_input("Say something to Punch...")

if user_input:
    # Store + display user message
    st.session_state.messages.append({
        "role": "user",
        "avatar": USER_AVATAR,
        "content": user_input,
        "bg": "#2b2b2b"
    })

    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(
            """
            <div style='background-color:#2b2b2b;padding:10px;border-radius:10px;
            max-width:70%;margin-bottom:5px;color:white;'>
                {user_input}
            </div>
            """,
            unsafe_allow_html=True
        )

    # Typing indicator
    with st.chat_message("assistant", avatar=PUNCH_AVATAR):
        with st.spinner("Punch is thinking…"):
            time.sleep(0.8)

    # Send to Dialogflow
    df_response = send_to_dialogflow(user_input)
    punch_reply = df_response.query_result.fulfillment_text

    # Store + display Punch's reply
    st.session_state.messages.append({
        "role": "assistant",
        "avatar": PUNCH_AVATAR,
        "content": punch_reply,
        "bg": "#1e88e5"
    })

    with st.chat_message("assistant", avatar=PUNCH_AVATAR):
        st.markdown(
            f"""
            <div style='background-color:#1e88e5;padding:10px;border-radius:10px;
            max-width:70%;margin-bottom:5px;color:white;'>
                {punch_reply}
            </div>
            """,
            unsafe_allow_html=True
        )

    # ---------------------------------------------------------
    # 6. DIAGNOSTIC PANEL (FIXED)
    # ---------------------------------------------------------
    with st.expander("Show diagnostic info"):
        df_dict = MessageToDict(df_response._pb)
        st.json(df_dict)
