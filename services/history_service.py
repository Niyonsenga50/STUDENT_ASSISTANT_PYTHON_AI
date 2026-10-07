"""
Chat history for the Recent and Search buttons.

Chats are stored in chat_history.json in your project root (next to app.py),
so they survive restarts. Delete that file to wipe all history.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path

HISTORY_FILE = Path(__file__).resolve().parent.parent / "chat_history.json"
MAX_CHATS = 100


def _read():
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _write(chats):
    HISTORY_FILE.write_text(
        json.dumps(
            chats[:MAX_CHATS],
            ensure_ascii=False,
            indent=2,
            default=lambda o: float(o) if hasattr(o, "__float__") else str(o),
        ),
        encoding="utf-8",
    )


def new_chat_id():
    return uuid.uuid4().hex[:12]


def load_history():
    """All saved chats, newest first."""
    return sorted(_read(), key=lambda c: c["updated"], reverse=True)


def get_chat(chat_id):
    return next((c for c in _read() if c["id"] == chat_id), None)


def save_chat(chat_id, messages, source=None):
    """Create or update a chat. Title comes from the first question."""
    if not messages:
        return
    first = next((m["content"] for m in messages if m["role"] == "user"), "New chat")
    title = first if len(first) <= 50 else first[:47] + "..."
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    chats = _read()
    for chat in chats:
        if chat["id"] == chat_id:
            chat.update(messages=messages, updated=now, source=source, title=title)
            break
    else:
        chats.append({"id": chat_id, "title": title, "source": source,
                      "created": now, "updated": now, "messages": messages})
    _write(sorted(chats, key=lambda c: c["updated"], reverse=True))


def delete_chat(chat_id):
    _write([c for c in _read() if c["id"] != chat_id])


def clear_history():
    _write([])


def _snippet(text, query, width=90):
    flat = " ".join(text.split())
    i = flat.lower().find(query.lower())
    if i < 0:
        return flat[: width * 2]
    start, end = max(0, i - width), min(len(flat), i + len(query) + width)
    return ("…" if start else "") + flat[start:end] + ("…" if end < len(flat) else "")


def search_chats(query, limit=30):
    """Keyword search across every saved message and chat title."""
    q = query.strip().lower()
    if not q:
        return []

    hits = []
    for chat in load_history():
        matched = False
        for m in chat["messages"]:
            if q in m["content"].lower():
                matched = True
                hits.append({"chat_id": chat["id"], "title": chat["title"],
                             "updated": chat["updated"], "role": m["role"],
                             "snippet": _snippet(m["content"], query)})
                if len(hits) >= limit:
                    return hits
        if not matched and q in chat["title"].lower():
            hits.append({"chat_id": chat["id"], "title": chat["title"],
                         "updated": chat["updated"], "role": "title",
                         "snippet": chat["title"]})
    return hits
