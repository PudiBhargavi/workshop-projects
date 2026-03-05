import streamlit as st
import os
import time
import tempfile

# ---------- LangChain Imports ----------
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.document_loaders import PyPDFLoader

# ---------- API KEY ----------
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

st.set_page_config(page_title="AI Tutor Pro", page_icon="🤖", layout="wide")

# ---------- SESSION STATE ----------
if "chats" not in st.session_state:
    st.session_state.chats = {"New Chat": []}

if "current_chat" not in st.session_state:
    st.session_state.current_chat = "New Chat"

if "vector_store" not in st.session_state:
    st.session_state.vector_store = None

# ---------- SIDEBAR ----------
with st.sidebar:
    st.title("🤖 AI Tutor Pro")

    # ➕ New Chat
    if st.button("➕ New Chat"):
        st.session_state.current_chat = "New Chat"
        st.session_state.chats["New Chat"] = []
        st.rerun()

    st.divider()
    st.subheader("💬 Chat History")

    for chat_name in list(st.session_state.chats.keys()):
        if st.button(chat_name):
            st.session_state.current_chat = chat_name
            st.rerun()

    st.divider()

    if st.button("🗑 Delete Current Chat"):
        del st.session_state.chats[st.session_state.current_chat]

        if not st.session_state.chats:
            st.session_state.chats["New Chat"] = []

        st.session_state.current_chat = list(st.session_state.chats.keys())[0]
        st.rerun()

    st.divider()

    mode = st.selectbox(
        "🧠 Thinking Mode",
        ["Smart Balanced", "Exam Mode", "Deep Explanation", "Quick Answer"]
    )

    temperature = st.slider("🎨 Creativity", 0.0, 1.0, 0.3, 0.1)
    response_length = st.selectbox("📏 Length", ["Short", "Medium", "Long"])

    use_rag = st.toggle("📚 Use RAG", value=True)
    top_k = st.slider("🔎 Chunks", 1, 6, 2)
    similarity_threshold = st.slider("🎯 Similarity", 0.0, 1.5, 0.8, 0.05)

st.title(st.session_state.current_chat)

if not OPENROUTER_API_KEY:
    st.error("❌ OPENROUTER_API_KEY not set.")
    st.stop()

# ---------- DISPLAY CHAT ----------
for message in st.session_state.chats[st.session_state.current_chat]:
    avatar = "👤" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# ---------- CHAT INPUT ----------
user_input = st.chat_input("Message AI Tutor...")

if user_input:

    current_messages = st.session_state.chats[st.session_state.current_chat]

    current_messages.append({"role": "user", "content": user_input})

    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="🤖"):

        message_placeholder = st.empty()
        full_response = ""

        with st.spinner("Thinking..."):

            llm = ChatOpenAI(
                model="openai/gpt-4o-mini",
                temperature=temperature,
                api_key=OPENROUTER_API_KEY,
                base_url="https://openrouter.ai/api/v1"
            )

            context = ""

            # ---------- RAG ----------
            if st.session_state.vector_store and use_rag:
                results = st.session_state.vector_store.similarity_search_with_score(
                    user_input, k=top_k
                )

                filtered_docs = []
                for doc, score in results:
                    if score < similarity_threshold:
                        filtered_docs.append(doc)

                if filtered_docs:
                    context = "\n\n".join([doc.page_content for doc in filtered_docs])

            # ---------- MEMORY ----------
            conversation_history = ""
            for msg in current_messages[-4:]:
                conversation_history += f"{msg['role']}: {msg['content']}\n"

            # ---------- PROMPT ----------
            prompt = f"""
You are an intelligent AI tutor.

Thinking Mode: {mode}
Response Length: {response_length}

Conversation History:
{conversation_history}

Context:
{context}

User Question:
{user_input}

Answer:
"""

            response = llm.invoke(prompt)
            answer = response.content

            # ---------- AUTO TITLE GENERATION ----------
            if (
                st.session_state.current_chat == "New Chat"
                and len(current_messages) == 1
            ):
                title_prompt = f"""
Generate a short 3-5 word title for this conversation:

User: {user_input}

Only return the title.
"""
                title = llm.invoke(title_prompt).content.strip()

                # Rename chat
                st.session_state.chats[title] = st.session_state.chats.pop("New Chat")
                st.session_state.current_chat = title

        for word in answer.split():
            full_response += word + " "
            time.sleep(0.01)
            message_placeholder.markdown(full_response + "▌")

        message_placeholder.markdown(full_response)

        current_messages.append({"role": "assistant", "content": full_response})