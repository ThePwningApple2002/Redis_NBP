
import json
import os
import urllib.parse
from dataclasses import dataclass
from typing import List, Optional
from uuid import uuid4

import httpx
import streamlit as st
from websockets.sync.client import ClientConnection, connect


@dataclass
class ChatMessage:
    role: str  # "user" or "assistant"
    content: str


@dataclass
class ConversationMeta:
    conversation_id: str
    title: str


def fetch_history(backend: str, user_id: str, conv_id: str) -> List[ChatMessage]:
    if not user_id or not conv_id:
        return []
    url = backend.rstrip("/") + f"/chat/{user_id}/{conv_id}/history"
    try:
        resp = httpx.get(url, timeout=5.0)
        resp.raise_for_status()
        data = resp.json()
        msgs = data.get("messages", [])
        return [ChatMessage(m.get("role", "user"), m.get("content", "")) for m in msgs]
    except Exception:
        return []


def build_ws_url(base_http_url: str, user_id: str, conversation_id: str) -> str:
    """Convert http(s) URL to ws(s) URL and append path."""
    parsed = urllib.parse.urlparse(base_http_url)
    scheme = "wss" if parsed.scheme == "https" else "ws"
    netloc = parsed.netloc or parsed.path  # allow bare host without scheme
    return f"{scheme}://{netloc}/ws/chat/{user_id}/{conversation_id}"


def send_and_stream(ws_url: str, message: str, timeout: float = 30.0) -> str:
    """Send one message, stream tokens, return full response."""
    response_tokens: List[str] = []
    ws: Optional[ClientConnection] = st.session_state.get("ws")

    # Create or reuse persistent connection
    if ws is None or ws.state.name != "OPEN":
        ws = connect(ws_url, open_timeout=timeout, close_timeout=timeout)
        st.session_state.ws = ws

    ws.send(json.dumps({"message": message}))

    for raw in ws:
        data = json.loads(raw)
        if data.get("type") == "token":
            tok = data.get("content", "")
            if tok:
                response_tokens.append(tok)
                yield "partial", "".join(response_tokens)
        elif data.get("type") == "end":
            yield "done", "".join(response_tokens)
            return
        elif data.get("type") == "error":
            raise RuntimeError(data.get("content", "Unknown websocket error"))


def init_state():
    if "messages" not in st.session_state:
        st.session_state.messages: List[ChatMessage] = []
    if "backend" not in st.session_state:
        st.session_state.backend = os.getenv("BACKEND_URL", "http://localhost:8000")
    if "user_id" not in st.session_state:
        st.session_state.user_id = ""
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = uuid4().hex
    if "ws" not in st.session_state:
        st.session_state.ws: Optional[ClientConnection] = None
    if "ws_url" not in st.session_state:
        st.session_state.ws_url: Optional[str] = None
    if "conversations" not in st.session_state:
        st.session_state.conversations: List[ConversationMeta] = []
    if "last_loaded_conv" not in st.session_state:
        st.session_state.last_loaded_conv: Optional[str] = None


def fetch_conversations(backend: str, user_id: str) -> List[ConversationMeta]:
    """Fetch conversation metadata for the user via REST endpoint."""
    if not user_id:
        return []
    url = backend.rstrip("/") + f"/conversations/{user_id}"
    try:
        resp = httpx.get(url, timeout=5.0)
        resp.raise_for_status()
        data = resp.json()
        convs = data.get("conversations", [])
        metas: List[ConversationMeta] = []
        for c in convs:
            cid = c.get("conversation_id")
            title = c.get("title") or "Untitled conversation"
            if cid:
                metas.append(ConversationMeta(conversation_id=cid, title=title))
        return metas
    except Exception:
        return []


def update_conversation_title(backend: str, user_id: str, conv_id: str, title: str) -> bool:
    url = backend.rstrip("/") + f"/conversations/{user_id}/{conv_id}/title"
    try:
        resp = httpx.patch(url, json={"title": title}, timeout=5.0)
        resp.raise_for_status()
        return True
    except Exception:
        return False


def render_sidebar():
    with st.sidebar:
        user_id = st.text_input("Korisnik", st.session_state.user_id)
        col1, col2 = st.columns(2)
        
        if col1.button("Učitaj korisnika"):
            st.session_state.user_id = user_id.strip()
            st.session_state.ws_url = None
            st.session_state.ws = None
            st.session_state.messages = []
            st.session_state.last_loaded_conv = None
            st.session_state.conversations = fetch_conversations(st.session_state.backend, st.session_state.user_id)
            st.rerun()

        if col2.button("Odjavi se"):
            if st.session_state.ws and st.session_state.ws.state.name == "OPEN":
                st.session_state.ws.close()
            st.session_state.ws = None
            st.session_state.ws_url = None
            st.rerun()

        st.markdown("---")
        st.subheader("Chats")
        
        if st.button("+ New chat", use_container_width=True):
            st.session_state.conversation_id = uuid4().hex
            st.session_state.messages = []
            st.session_state.ws = None
            st.session_state.ws_url = None
            st.session_state.last_loaded_conv = st.session_state.conversation_id
            st.rerun()

        # Fetch conversations if a user is set
        st.session_state.conversations = fetch_conversations(st.session_state.backend, st.session_state.user_id)

        if st.session_state.conversations:
            st.markdown("### Your chats")
            for meta in st.session_state.conversations:
                active = meta.conversation_id == st.session_state.conversation_id
                # Add a visual indicator for the active chat
                label = f"{'🔹 ' if active else ''}{meta.title}"
                
                if st.button(label, key=f"btn_{meta.conversation_id}", use_container_width=True):
                    if not active:
                        st.session_state.conversation_id = meta.conversation_id
                        st.session_state.messages = fetch_history(
                            st.session_state.backend,
                            st.session_state.user_id,
                            meta.conversation_id,
                        )
                        st.session_state.ws = None
                        st.session_state.ws_url = None
                        st.session_state.last_loaded_conv = meta.conversation_id
                        st.rerun()

            # Rename section
            st.divider()
            current_meta = next((c for c in st.session_state.conversations if c.conversation_id == st.session_state.conversation_id), None)
            if current_meta:
                new_title = st.text_input(
                    "Rename chat", 
                    value=current_meta.title, 
                    key=f"rename_{current_meta.conversation_id}"
                )                
                if st.button("Save title", use_container_width=True):
                    if update_conversation_title(st.session_state.backend, st.session_state.user_id, current_meta.conversation_id, new_title):
                        st.success("Title updated")
                        st.session_state.conversations = fetch_conversations(st.session_state.backend, st.session_state.user_id)
                        st.rerun()
                    else:
                        st.error("Failed to update title.")
            else:
                st.info("Send a message in this chat to save it before renaming.")
        else:
            if st.session_state.user_id:
                st.info("No chats yet. Send a message to start one.")
            else:
                st.warning("Enter a User ID above to see your chats.")

        # Show connection status at the very bottom
        st.markdown("---")
        ws = st.session_state.ws
        if ws and ws.state.name == "OPEN":
            st.success("WebSocket: Connected")
        else:
            st.info("WebSocket: Not connected")


def render_history():
    for m in st.session_state.messages:
        with st.chat_message(m.role):
            st.markdown(m.content)


def main():
    st.set_page_config(page_title="Recipe Chat", page_icon="🥘", layout="wide")
    init_state()

    # Auto-load history when switching conversations (fallback catch)
    if st.session_state.conversation_id != st.session_state.last_loaded_conv:
        st.session_state.messages = fetch_history(
            st.session_state.backend,
            st.session_state.user_id,
            st.session_state.conversation_id,
        )
        st.session_state.last_loaded_conv = st.session_state.conversation_id

    render_sidebar()

    st.title("🥘 Recipe Chat")
    st.caption("Chat-style Streamlit client for the FastAPI WebSocket backend")
    st.divider()

    render_history()

    # Chat input at bottom
    prompt = st.chat_input("Ask for a recipe or cooking help...")
    if prompt:
        if not st.session_state.user_id:
            st.error("Please enter and save a User ID in the sidebar first.")
            return

        st.session_state.messages.append(ChatMessage("user", prompt))
        with st.chat_message("user"):
            st.markdown(prompt)

        ws_url = st.session_state.ws_url or build_ws_url(
            st.session_state.backend, st.session_state.user_id, st.session_state.conversation_id
        )
        st.session_state.ws_url = ws_url
        
        with st.chat_message("assistant"):
            placeholder = st.empty()
            try:
                full = ""
                for status, chunk in send_and_stream(ws_url, prompt):
                    full = chunk
                    placeholder.markdown(full if full else "…")
                
                st.session_state.messages.append(ChatMessage("assistant", full or "(no response)"))
                st.session_state.conversations = fetch_conversations(st.session_state.backend, st.session_state.user_id)
                # Force a rerun to sync the sidebar conversation list if this was the first message
                st.rerun()
            except Exception as e:
                placeholder.error(f"WebSocket error: {e}")


if __name__ == "__main__":
    main()