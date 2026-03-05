import streamlit as st
import os
import time
import tempfile
import json
import base64
from datetime import datetime

# ---------- LangChain ----------
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.document_loaders import PyPDFLoader

# ---------- PDF Export ----------
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

# ---------- CONFIG ----------
st.set_page_config(page_title="AI Tutor Pro", page_icon="🤖", layout="wide")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
CHAT_FILE = "saved_chats.json"
VECTOR_PATH = "vector_store"

# ---------- LOAD SAVED CHATS ----------
if os.path.exists(CHAT_FILE):
    with open(CHAT_FILE, "r") as f:
        saved_data = json.load(f)
else:
    saved_data = {}

if "chats" not in st.session_state:
    st.session_state.chats = saved_data

if not st.session_state.chats:
    st.session_state.chats["Chat 1"] = []

if "current_chat" not in st.session_state:
    st.session_state.current_chat = list(st.session_state.chats.keys())[0]

if "vector_store" not in st.session_state:
    if os.path.exists(VECTOR_PATH):
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1"
        )
        st.session_state.vector_store = FAISS.load_local(
            VECTOR_PATH, embeddings, allow_dangerous_deserialization=True
        )
    else:
        st.session_state.vector_store = None

# ---------- SAVE ----------
def save_chats():
    with open(CHAT_FILE, "w") as f:
        json.dump(st.session_state.chats, f)

def save_vector_db():
    if st.session_state.vector_store:
        st.session_state.vector_store.save_local(VECTOR_PATH)

# ---------- SIDEBAR ----------
with st.sidebar:

    st.title("🤖 AI Tutor Pro")

    # Theme Toggle
    theme = st.toggle("🌙 Dark Mode", value=True)

    if theme:
        st.markdown("""
        <style>
        body {background-color: #0e1117; color: white;}
        </style>
        """, unsafe_allow_html=True)

    st.divider()

    # New Chat
    if st.button("➕ New Chat"):
        name = f"Chat {len(st.session_state.chats)+1}"
        st.session_state.chats[name] = []
        st.session_state.current_chat = name
        save_chats()
        st.rerun()

    st.subheader("💬 Chats")

    for chat in st.session_state.chats:
        if st.button(chat):
            st.session_state.current_chat = chat
            st.rerun()

    if st.button("🗑 Delete Chat"):
        if len(st.session_state.chats) > 1:
            del st.session_state.chats[st.session_state.current_chat]
            st.session_state.current_chat = list(st.session_state.chats.keys())[0]
            save_chats()
            st.rerun()

    st.divider()

    # ---------- FILE RAG ----------
    st.subheader("📚 Knowledge Base")

    uploaded_files = st.file_uploader(
        "Upload PDF/TXT",
        type=["pdf", "txt"],
        accept_multiple_files=True
    )

    if st.button("🗑 Clear Knowledge"):
        st.session_state.vector_store = None
        if os.path.exists(VECTOR_PATH):
            import shutil
            shutil.rmtree(VECTOR_PATH)
        st.success("Knowledge Cleared")

    st.divider()

    # Image Upload
    uploaded_image = st.file_uploader(
        "🖼 Upload Image",
        type=["png", "jpg", "jpeg"]
    )

    st.divider()

    mode = st.selectbox(
        "🧠 Thinking Mode",
        ["Smart Balanced", "Exam Mode", "Deep Explanation", "Quick Answer"]
    )

    temperature = st.slider("🎨 Creativity", 0.0, 1.0, 0.3, 0.1)
    use_rag = st.toggle("📚 Use RAG", True)
    top_k = st.slider("🔎 Retrieval Chunks", 1, 6, 2)

    st.divider()

    # PDF Export
    if st.button("📥 Export Chat"):
        filename = f"{st.session_state.current_chat}.pdf"
        doc = SimpleDocTemplate(filename)
        elements = []
        styles = getSampleStyleSheet()

        for msg in st.session_state.chats[st.session_state.current_chat]:
            role = "User" if msg["role"] == "user" else "AI"
            elements.append(Paragraph(f"<b>{role}:</b> {msg['content']}", styles["Normal"]))
            elements.append(Spacer(1, 0.3 * inch))

        doc.build(elements)
        st.success(f"Saved as {filename}")

# ---------- MAIN ----------
st.title(st.session_state.current_chat)

if not OPENROUTER_API_KEY:
    st.error("❌ OPENROUTER_API_KEY not set.")
    st.stop()

# ---------- PROCESS DOCUMENTS ----------
if uploaded_files:
    documents = []

    for file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(file.read())
            tmp_path = tmp.name

        if file.name.endswith(".pdf"):
            loader = PyPDFLoader(tmp_path)
            documents.extend(loader.load())
        else:
            with open(tmp_path, "r", encoding="utf-8", errors="ignore") as f:
                documents.append(Document(page_content=f.read()))

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    docs_split = splitter.split_documents(documents)

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1"
    )

    st.session_state.vector_store = FAISS.from_documents(docs_split, embeddings)
    save_vector_db()
    st.sidebar.success(f"✅ {len(docs_split)} chunks indexed")

# ---------- DISPLAY CHAT ----------
for msg in st.session_state.chats[st.session_state.current_chat]:
    avatar = "👤" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# ---------- CHAT INPUT ----------
user_input = st.chat_input("Message AI Tutor...")

if user_input:

    current_messages = st.session_state.chats[st.session_state.current_chat]
    current_messages.append({"role": "user", "content": user_input})
    save_chats()

    llm = ChatOpenAI(
        model="openai/gpt-4o",
        temperature=temperature,
        streaming=True,
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1"
    )

    # Auto Rename Chat
    if len(current_messages) == 1:
        title_prompt = f"Generate a short 4-word title:\n{user_input}"
        title = llm.invoke(title_prompt).content.strip()
        st.session_state.chats[title] = st.session_state.chats.pop(st.session_state.current_chat)
        st.session_state.current_chat = title
        save_chats()

    history = "\n".join([f"{m['role']}: {m['content']}" for m in current_messages[-6:]])

    context = ""
    if st.session_state.vector_store and use_rag:
        docs = st.session_state.vector_store.similarity_search(user_input, k=top_k)
        context = "\n\n".join([d.page_content for d in docs])

    image_message = None
    if uploaded_image:
        image_bytes = uploaded_image.read()
        encoded = base64.b64encode(image_bytes).decode()
        image_message = {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}
        }

    prompt = f"""
You are an advanced AI Tutor.

Thinking Mode: {mode}

Conversation History:
{history}

Context:
{context}

User Question:
{user_input}
"""

    with st.chat_message("assistant", avatar="🤖"):
        placeholder = st.empty()
        full_response = ""

        if image_message:
            response = llm.invoke([
                {"type": "text", "text": prompt},
                image_message
            ])
            full_response = response.content
            placeholder.markdown(full_response)
        else:
            for chunk in llm.stream(prompt):
                if chunk.content:
                    full_response += chunk.content
                    placeholder.markdown(full_response + "▌")

        placeholder.markdown(full_response)

    current_messages.append({"role": "assistant", "content": full_response})
    save_chats()