import streamlit as st
import requests
import os
import time

# ---------- RAG Imports (Updated for latest LangChain) ----------
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA

# ---------- API Key ----------
OPENROUTER_API_KEY = "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"  # Replace with your actual key

st.set_page_config(page_title="AI Tutor", page_icon="🤖", layout="wide")

# ---------- Custom Styling ----------
st.markdown("""
<style>
.stChatMessage { border-radius: 12px; padding: 10px; }
[data-testid="stChatMessage-user"] { background-color: #1E1E1E; color: #fff; }
[data-testid="stChatMessage-assistant"] { background-color: #111827; color: #fff; }
</style>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------
with st.sidebar:
    st.title("🤖 AI Tutor")
    st.markdown("Built with ❤️ using OpenRouter + RAG")
    if st.button("🗑 Clear Chat"):
        st.session_state.messages = [
            {"role": "system", "content": "You are a helpful AI tutor. Be intelligent, friendly, and structured like ChatGPT."}
        ]
        st.session_state.vector_store = None
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
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None

# ---------- File Upload for RAG ----------
uploaded_files = st.file_uploader("Upload PDFs/TXT files to teach me 📚", accept_multiple_files=True)
if uploaded_files:
    documents = []
    for file in uploaded_files:
        try:
            text = file.read().decode("utf-8")
        except:
            text = file.read().decode("latin-1")
        documents.append(text)

    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=50)
    docs_split = text_splitter.split_text(" ".join(documents))

    # Create embeddings and store in session
    embeddings = OpenAIEmbeddings(openai_api_key=OPENROUTER_API_KEY)
    vector_store = FAISS.from_texts(docs_split, embeddings)
    st.session_state.vector_store = vector_store
    st.success(f"✅ {len(docs_split)} text chunks indexed for RAG.")

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

    st.session_state.messages.append({"role": "user", "content": user_input})

    # Assistant response with typing effect
    with st.chat_message("assistant", avatar="🤖"):
        message_placeholder = st.empty()
        full_response = ""

        with st.spinner("Thinking..."):
            # ---------- RAG-enabled response ----------
            if st.session_state.vector_store:
                # Build QA chain
                qa_chain = RetrievalQA.from_chain_type(
                    llm=ChatOpenAI(model_name="gpt-4o-mini", temperature=0),
                    chain_type="stuff",
                    retriever=st.session_state.vector_store.as_retriever()
                )
                answer = qa_chain.run(user_input)
            else:
                # Fallback to OpenRouter API
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
        st.session_state.messages.append({"role": "assistant", "content": full_response})