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

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="AI Tutor Pro", page_icon="🤖", layout="wide")

# ---------- STYLE ----------
st.markdown("""
<style>
.stChatMessage { border-radius: 12px; padding: 10px; }
[data-testid="stChatMessage-user"] { background-color: #1E1E1E; color: #fff; }
[data-testid="stChatMessage-assistant"] { background-color: #111827; color: #fff; }
</style>
""", unsafe_allow_html=True)

# ---------- SIDEBAR ----------
with st.sidebar:
    st.title("🤖 AI Tutor Pro")

    st.divider()

    mode = st.selectbox(
        "🧠 Thinking Mode",
        ["Smart Balanced", "Exam Mode", "Deep Explanation", "Quick Answer"]
    )

    temperature = st.slider(
        "🎨 Creativity Level",
        0.0, 1.0, 0.3, 0.1
    )

    response_length = st.selectbox(
        "📏 Response Length",
        ["Short", "Medium", "Long"]
    )

    st.divider()

    use_rag = st.toggle("📚 Use Document Knowledge (RAG)", value=True)
    top_k = st.slider("🔎 Number of Chunks", 1, 6, 2)
    similarity_threshold = st.slider("🎯 Similarity Threshold (Lower = stricter)", 0.0, 1.5, 0.8, 0.05)
    show_context = st.toggle("🛠 Show Retrieved Context (Debug)", value=False)

    st.divider()

    if st.button("🗑 Clear Chat"):
        st.session_state.messages = []
        st.session_state.vector_store = None
        st.rerun()

st.title("AI Tutor Pro")
st.caption("Your intelligent learning companion")

if not OPENROUTER_API_KEY:
    st.error("❌ OPENROUTER_API_KEY not set.")
    st.stop()

# ---------- SESSION STATE ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "vector_store" not in st.session_state:
    st.session_state.vector_store = None

# ---------- FILE UPLOAD ----------
uploaded_files = st.file_uploader(
    "Upload PDFs/TXT files to teach me 📚",
    type=["pdf", "txt"],
    accept_multiple_files=True
)

if uploaded_files:
    documents = []

    for file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(file.read())
            tmp_path = tmp.name

        if file.name.endswith(".pdf"):
            loader = PyPDFLoader(tmp_path)
            docs = loader.load()
            documents.extend(docs)

        elif file.name.endswith(".txt"):
            with open(tmp_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            documents.append(Document(page_content=text))

    if documents:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150
        )

        docs_split = splitter.split_documents(documents)

        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1"
        )

        vector_store = FAISS.from_documents(docs_split, embeddings)
        st.session_state.vector_store = vector_store

        st.success(f"✅ {len(docs_split)} chunks indexed successfully!")
    else:
        st.error("No readable content found.")

# ---------- DISPLAY CHAT ----------
for message in st.session_state.messages:
    avatar = "👤" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# ---------- CHAT INPUT ----------
user_input = st.chat_input("Message AI Tutor...")

if user_input:

    st.session_state.messages.append({"role": "user", "content": user_input})

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

            # ---------- SMART RAG ----------
            if st.session_state.vector_store and use_rag:

                results = st.session_state.vector_store.similarity_search_with_score(
                    user_input,
                    k=top_k
                )

                filtered_docs = []
                for doc, score in results:
                    if score < similarity_threshold:
                        filtered_docs.append(doc)

                if filtered_docs:
                    context = "\n\n".join([doc.page_content for doc in filtered_docs])

                if show_context and context:
                    st.info("Retrieved Context:")
                    st.write(context[:1500])

            # ---------- MEMORY ----------
            conversation_history = ""
            for msg in st.session_state.messages[-4:]:
                conversation_history += f"{msg['role']}: {msg['content']}\n"

            # ---------- MAIN PROMPT ----------
            prompt = f"""
You are an intelligent, friendly AI tutor.

Thinking Mode: {mode}
Response Length: {response_length}

Guidelines:
- Adapt style based on Thinking Mode.
- If Quick Answer → short and direct.
- If Exam Mode → structured points.
- If Deep Explanation → step-by-step with examples.
- If Smart Balanced → natural conversational tone.
- Avoid repetition.
- Rephrase content in your own words.
- If context is irrelevant, ignore it.

Conversation History:
{conversation_history}

Context:
{context}

Current Question:
{user_input}

Answer:
"""

            response = llm.invoke(prompt)
            answer = response.content

            # ---------- SELF-CHECK ----------
            verification_prompt = f"""
Improve the following answer if needed:
- Remove repetition
- Ensure it follows user instruction
- Make it clearer

Answer:
{answer}
"""
            verified = llm.invoke(verification_prompt)
            answer = verified.content

            # ---------- CONFIDENCE SCORE ----------
            confidence_prompt = f"""
Rate confidence of this answer from 0 to 100.
Only return a number.

Answer:
{answer}
"""
            confidence = llm.invoke(confidence_prompt).content.strip()

        for word in answer.split():
            full_response += word + " "
            time.sleep(0.01)
            message_placeholder.markdown(full_response + "▌")

        message_placeholder.markdown(full_response)

        st.caption(f"Confidence Score: {confidence}%")

        st.session_state.messages.append(
            {"role": "assistant", "content": full_response}
        )