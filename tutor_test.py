import streamlit as st
import os
import time
import tempfile
import json
from datetime import datetime

# ---------- LangChain ----------
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.document_loaders import PyPDFLoader

# ---------- PDF Export ----------
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet

# ---------- CONFIG ----------
st.set_page_config(page_title="AI Tutor Pro", page_icon="🤖", layout="wide")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
CHAT_FILE = "saved_chats.json"

# ---------- LOAD PERSISTENT CHATS ----------
if os.path.exists(CHAT_FILE):
    with open(CHAT_FILE, "r") as f:
        saved_data = json.load(f)
else:
    saved_data = {"New Chat": []}

if "chats" not in st.session_state:
    st.session_state.chats = saved_data

if "current_chat" not in st.session_state:
    st.session_state.current_chat = list(st.session_state.chats.keys())[0]

if "vector_store" not in st.session_state:
    st.session_state.vector_store = None

# ---------- SAVE FUNCTION ----------
def save_chats():
    with open(CHAT_FILE, "w") as f:
        json.dump(st.session_state.chats, f)

# ---------- SIDEBAR ----------
with st.sidebar:

    st.title("🤖 AI Tutor Pro")
    st.caption("Your Intelligent Learning Companion")

    if st.button("➕ New Chat"):
        st.session_state.chats["New Chat"] = []
        st.session_state.current_chat = "New Chat"
        save_chats()
        st.rerun()

    st.divider()
    st.subheader("💬 Chats")

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
        save_chats()
        st.rerun()

    st.divider()

    # ---------- FILE UPLOAD (RAG) ----------
    st.subheader("📚 Knowledge Base")

    uploaded_files = st.file_uploader(
        "Upload PDF, TXT",
        type=["pdf", "txt"],
        accept_multiple_files=True
    )

    if st.button("🗑 Clear Documents"):
        st.session_state.vector_store = None
        st.success("Knowledge cleared.")

    # ---------- IMAGE UPLOAD ----------
    st.subheader("🖼 Image Analysis")

    uploaded_image = st.file_uploader(
        "Upload Image",
        type=["png", "jpg", "jpeg"]
    )

    st.divider()

    mode = st.selectbox(
        "🧠 Thinking Mode",
        ["Smart Balanced", "Exam Mode", "Deep Explanation", "Quick Answer"]
    )

    temperature = st.slider("🎨 Creativity", 0.0, 1.0, 0.3, 0.1)
    response_length = st.selectbox("📏 Length", ["Short", "Medium", "Long"])
    use_rag = st.toggle("📚 Use RAG", value=True)
    top_k = st.slider("🔎 Chunks", 1, 6, 2)

    st.divider()

    # ---------- EXPORT PDF ----------
    if st.button("📥 Export Chat as PDF"):
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

st.title(st.session_state.current_chat)

if not OPENROUTER_API_KEY:
    st.error("❌ OPENROUTER_API_KEY not set.")
    st.stop()

# ---------- FILE PROCESSING ----------
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
    st.sidebar.success(f"✅ {len(docs_split)} chunks indexed")

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
    save_chats()

    with st.chat_message("assistant", avatar="🤖"):

        placeholder = st.empty()
        full_response = ""

        llm = ChatOpenAI(
            model="openai/gpt-4o-mini",
            temperature=temperature,
            api_key=OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1"
        )

        context = ""

        # ---------- RAG ----------
        if st.session_state.vector_store and use_rag:
            results = st.session_state.vector_store.similarity_search(user_input, k=top_k)
            context = "\n\n".join([doc.page_content for doc in results])

        # ---------- IMAGE UNDERSTANDING ----------
        image_context = ""
        if uploaded_image:
            image_context = "User uploaded an image. Analyze it carefully."

        # ---------- MEMORY ----------
        history = ""
        for msg in current_messages[-6:]:
            history += f"{msg['role']}: {msg['content']}\n"

        prompt = f"""
You are an advanced AI Tutor.

Thinking Mode: {mode}
Response Length: {response_length}

Conversation History:
{history}

Context:
{context}

{image_context}

User Question:
{user_input}

Answer naturally and avoid repetition.
"""

        response = llm.invoke(prompt)
        answer = response.content

        for word in answer.split():
            full_response += word + " "
            time.sleep(0.01)
            placeholder.markdown(full_response + "▌")

        placeholder.markdown(full_response)

        current_messages.append({"role": "assistant", "content": full_response})
        save_chats()