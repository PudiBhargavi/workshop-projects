import streamlit as st
import requests

OPENROUTER_API_KEY = "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"

st.title("📚 AI Tutor")

user_question = st.text_input("Ask me anything:")

if user_question:
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "openai/gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a helpful AI tutor."},
                {"role": "user", "content": user_question}
            ]
        }
    )

    result = response.json()
    answer = result["choices"][0]["message"]["content"]
    st.write(answer)