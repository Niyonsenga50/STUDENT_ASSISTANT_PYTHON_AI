import re

import streamlit as st

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from services.search_service import (
    build_knowledge_base,
    search_knowledge
)
from services.ai_service import generate_answer
from services.upload_service import (
    build_index_from_upload,
    search_upload,
    answer_from_upload
)
from services.history_service import (
    load_history,
    get_chat,
    save_chat,
    delete_chat,
    clear_history,
    search_chats,
    new_chat_id
)


st.set_page_config(
    page_title="Student AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_data
def load_knowledge():
    return build_knowledge_base()


knowledge_base = load_knowledge()

st.session_state.setdefault("messages", [])
st.session_state.setdefault("chat_id", new_chat_id())
st.session_state.setdefault("view", "chat")   # chat | search | recent


# ------------------------------------------------------------ callbacks ---
def set_view(view):
    st.session_state.view = view


def start_new_chat():
    st.session_state.messages = []
    st.session_state.chat_id = new_chat_id()
    st.session_state.view = "chat"


def open_chat(chat_id):
    chat = get_chat(chat_id)
    if chat:
        st.session_state.messages = chat["messages"]
        st.session_state.chat_id = chat["id"]
        st.session_state.view = "chat"


def remove_chat(chat_id):
    delete_chat(chat_id)
    if chat_id == st.session_state.chat_id:
        start_new_chat()
    st.session_state.view = "recent"


def remove_all_chats():
    clear_history()
    start_new_chat()
    st.session_state.view = "recent"


# -------------------------------------------------------------- helpers ---
def highlight(text, query):
    return re.sub(f"({re.escape(query)})", r"**\1**", text, flags=re.I)


def show_references(refs):
    """Sources used for an answer, shown under the answer."""
    if not refs:
        return
    with st.expander(f"References ({len(refs)})"):
        for i, r in enumerate(refs, 1):
            page = f" · {r['page']}" if r.get("page") else ""
            st.markdown(
                f"**[{i}] {r['filename']}{page}**  ·  "
                f"relevance {r['score']:.2f}"
            )
            st.caption(r["content"])
            if i < len(refs):
                st.divider()


# -------------------------------------------------------------- sidebar ---
with st.sidebar:

    st.title("Student AI Assistant")
    st.divider()

    current_view = st.session_state.view

    st.button(
        "New Chat",
        use_container_width=True,
        on_click=start_new_chat
    )

    st.button(
        "Search",
        use_container_width=True,
        on_click=set_view,
        args=("search",),
        type="primary" if current_view == "search" else "secondary"
    )

    st.button(
        "Recent",
        use_container_width=True,
        on_click=set_view,
        args=("recent",),
        type="primary" if current_view == "recent" else "secondary"
    )

    st.divider()

    st.subheader("Upload a File")
    uploaded = st.file_uploader(
        "PDF, DOCX or TXT",
        type=["pdf", "docx", "txt", "md"],
        label_visibility="collapsed"
    )

    upload_index = None

    if uploaded:
        key = (uploaded.name, uploaded.size)

        # Index only when a new file arrives, not on every rerun
        if st.session_state.get("upload_key") != key:
            with st.spinner("Reading and indexing your file..."):
                st.session_state.upload_index = build_index_from_upload(uploaded)
                st.session_state.upload_key = key
                start_new_chat()   # new file = new chat

        upload_index = st.session_state.get("upload_index")

        if upload_index is None:
            st.error("No readable text found. Scanned PDFs need OCR first.")
    else:
        st.session_state.pop("upload_key", None)
        st.session_state.pop("upload_index", None)

    st.divider()

    st.subheader("Course Materials")

    if upload_index:
        st.write(f"Source: **{uploaded.name}**")
        st.write(
            f"{upload_index['pages']} pages/sections · "
            f"{len(upload_index['chunks'])} chunks"
        )
    else:
        st.write(f"Knowledge chunks: {len(knowledge_base)}")
        st.caption("Upload a file above to ask questions about it instead.")


source_name = uploaded.name if upload_index else None

# Typing a question always switches back to the chat view
question = st.chat_input("Ask a question about your course materials...")
if question:
    st.session_state.view = "chat"

view = st.session_state.view


# ----------------------------------------------------------------- main ---
st.title("Student AI Assistant")

if view == "chat":
    if upload_index:
        st.write(f"Ask questions about **{uploaded.name}**. "
                 "Answers include references to the exact passages used.")
    else:
        st.write(
            "Ask questions about your course materials "
            "and receive answers based on the available "
            "learning resources."
        )
elif view == "search":
    st.write("Search your past chats and the current course material.")
else:
    st.write("Your saved chats. Open one to continue it.")

st.divider()


# ---------------------------------------------------------- recent view ---
def render_recent():
    chats = load_history()

    if not chats:
        st.info("No saved chats yet. Ask a question and it will appear here.")
        return

    top_left, top_right = st.columns([5, 1])
    top_left.subheader(f"Recent chats ({len(chats)})")
    top_right.button("Clear all", on_click=remove_all_chats,
                     use_container_width=True)

    for chat in chats:
        with st.container(border=True):
            info, open_col, del_col = st.columns([6, 1, 1])

            current = " · current" if chat["id"] == st.session_state.chat_id else ""
            info.markdown(f"**{chat['title']}**{current}")
            info.caption(
                f"{chat['updated']} · "
                f"{chat.get('source') or 'Built-in materials'} · "
                f"{len(chat['messages']) // 2} question(s)"
            )

            open_col.button("Open", key=f"open_{chat['id']}",
                            on_click=open_chat, args=(chat["id"],),
                            use_container_width=True)
            del_col.button("Delete", key=f"del_{chat['id']}",
                           on_click=remove_chat, args=(chat["id"],),
                           use_container_width=True)


# ---------------------------------------------------------- search view ---
def render_search():
    query = st.text_input(
        "Search",
        placeholder="e.g. supervised learning",
        label_visibility="collapsed",
        key="search_query"
    ).strip()

    if not query:
        st.caption("Type a word or phrase to search.")
        return

    doc_label = uploaded.name if upload_index else "course materials"
    tab_chats, tab_doc = st.tabs(["In your chats", f"In {doc_label}"])

    with tab_chats:
        hits = search_chats(query)

        if not hits:
            st.info("No matches in your saved chats.")

        for n, hit in enumerate(hits):
            with st.container(border=True):
                text_col, btn_col = st.columns([6, 1])
                who = {"user": "You asked", "assistant": "Answer",
                       "title": "Chat title"}[hit["role"]]
                text_col.markdown(f"**{hit['title']}**")
                text_col.caption(f"{hit['updated']} · {who}")
                text_col.markdown(highlight(hit["snippet"], query))
                btn_col.button("Open", key=f"sopen_{hit['chat_id']}_{n}",
                               on_click=open_chat, args=(hit["chat_id"],),
                               use_container_width=True)

    with tab_doc:
        if upload_index:
            results = [r for r in search_upload(query, upload_index, 5)
                       if r["score"] >= 0.2]
        else:
            results = search_knowledge(query, knowledge_base, max_results=5)

        if not results:
            st.info("No close matches in the course material.")

        for r in results:
            with st.container(border=True):
                page = f" · {r['page']}" if r.get("page") else ""
                st.markdown(f"**{r['filename']}{page}**")
                st.caption(f"relevance {r['score']:.2f}")
                st.write(r["content"])


# ------------------------------------------------------------ chat view ---
def render_chat():
    if not st.session_state.messages:
        st.caption("Ask a question below, or open an earlier chat from Recent.")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if message["role"] == "assistant":
                show_references(message.get("references"))

    if not question:
        return

    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):

        with st.spinner("Searching..."):

            if upload_index:
                results = search_upload(question, upload_index, max_results=4)
                answer, references = answer_from_upload(question, results)
            else:
                results = search_knowledge(
                    question, knowledge_base, max_results=3
                )
                answer = generate_answer(question, results)
                references = results

        st.write(answer)
        show_references(references)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "references": references
        }
    )

    # Save after every exchange so it shows up in Recent and Search
    save_chat(
        st.session_state.chat_id,
        st.session_state.messages,
        source_name
    )


if view == "recent":
    render_recent()
elif view == "search":
    render_search()
else:
    render_chat()
