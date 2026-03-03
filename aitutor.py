import streamlit as st
import requests
import os
import time

# Get API key
OPENROUTER_API_KEY = "your_key"

st.set_page_config(page_title="AI Tutor", page_icon="🤖", layout="wide")

# ---------- Custom Styling (ChatGPT Look) ----------
st.markdown("""
<style>
.stChatMessage {
    border-radius: 12px;
    padding: 10px;
}
[data-testid="stChatMessage-user"] {
    background-color: #1E1E1E;
}
[data-testid="stChatMessage-assistant"] {
    background-color: #111827;
}
</style>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------
with st.sidebar:
    st.title("🤖 AI Tutor")
    st.markdown("Built with ❤️ using OpenRouter")
    if st.button("🗑 Clear Chat"):
        st.session_state.messages = [
            {"role": "system", "content": "You are a helpful AI tutor. Be intelligent, friendly, and structured like ChatGPT."}
        ]
        st.rerun()

st.title("AI Tutor")
st.caption("Your intelligent learning companion")

if not OPENROUTER_API_KEY:
    st.error("API Key missing.")
    st.stop()

# ---------- Initialize Chat ----------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are a helpful AI tutor. Be intelligent, friendly, and structured like ChatGPT."}
    ]

# ---------- Display Chat ----------
for message in st.session_state.messages:
    if message["role"] != "system":
        avatar = "👤" if message["role"] == "user" else "🤖"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

# ---------- Chat Input ----------
user_input = st.chat_input("Message AI Tutor...")

if user_input:
    # Show user message
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    st.session_state.messages.append(
        {"role": "user", "content": user_input}
    )

    # Assistant response with typing effect
    with st.chat_message("assistant", avatar="🤖"):
        message_placeholder = st.empty()
        full_response = ""

        with st.spinner("Thinking..."):
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "openai/gpt-4o-mini",
                    "messages": st.session_state.messages
                }
            )

            result = response.json()

            if response.status_code == 200 and "choices" in result:
                answer = result["choices"][0]["message"]["content"]
            else:
                answer = "⚠ Something went wrong."

        # Typing animation
        for chunk in answer.split():
            full_response += chunk + " "
            time.sleep(0.03)
            message_placeholder.markdown(full_response + "▌")

        message_placeholder.markdown(full_response)

    st.session_state.messages.append(
        {"role": "assistant", "content": full_response})
