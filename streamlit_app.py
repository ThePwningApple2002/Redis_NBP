
import json
import os
import urllib.parse
from dataclasses import dataclass
from typing import Iterator, List, Optional
from uuid import uuid4

import httpx
import streamlit as st
from websockets.sync.client import ClientConnection, connect


@dataclass
class ChatMessage:
    role: str
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
    netloc = parsed.netloc or parsed.path
    return f"{scheme}://{netloc}/ws/chat/{user_id}/{conversation_id}"


def send_and_stream(
    ws_url: str,
    message: str,
    timeout: float = 30.0,
    action: str = "send",
) -> Iterator[tuple[str, str]]:
    """Send one message, stream tokens, return full response."""
    response_tokens: List[str] = []
    ws: Optional[ClientConnection] = st.session_state.get("ws")

    if ws is None or ws.state.name != "OPEN":
        ws = connect(ws_url, open_timeout=timeout, close_timeout=timeout)
        st.session_state.ws = ws

    ws.send(json.dumps({"message": message, "action": action}))

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
        st.session_state.messages = []
    if "backend" not in st.session_state:
        st.session_state.backend = os.getenv("BACKEND_URL", "http://localhost:8000")
    if "user_id" not in st.session_state:
        st.session_state.user_id = ""
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = uuid4().hex
    if "ws" not in st.session_state:
        st.session_state.ws = None
    if "ws_url" not in st.session_state:
        st.session_state.ws_url = None
    if "conversations" not in st.session_state:
        st.session_state.conversations = []
    if "last_loaded_conv" not in st.session_state:
        st.session_state.last_loaded_conv = None
    if "edit_last_source" not in st.session_state:
        st.session_state.edit_last_source = None
    if "edit_last_input" not in st.session_state:
        st.session_state.edit_last_input = ""
    if "is_editing_last_user" not in st.session_state:
        st.session_state.is_editing_last_user = False


def get_last_user_message_info(messages: List[ChatMessage]) -> tuple[Optional[int], Optional[str]]:
    for idx in range(len(messages) - 1, -1, -1):
        if messages[idx].role == "user":
            return idx, messages[idx].content
    return None, None


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
            st.session_state.user_id = (user_id or "").strip()
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

        st.session_state.conversations = fetch_conversations(st.session_state.backend, st.session_state.user_id)

        if st.session_state.conversations:
            st.markdown("### Your chats")
            for meta in st.session_state.conversations:
                active = meta.conversation_id == st.session_state.conversation_id
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
            if st.session_state.user_id:
                st.info("No chats yet. Send a message to start one.")
            else:
                st.warning("Enter a User ID above to see your chats.")


def render_history(last_user_idx: Optional[int]) -> Optional[str]:
    for idx, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg.role):
            if msg.role == "user" and last_user_idx is not None and idx == last_user_idx:
                if st.session_state.is_editing_last_user:
                    st.text_area(
                        "Edit last message",
                        key="edit_last_input",
                        height=120,
                        label_visibility="collapsed",
                    )
                    col_save, col_cancel = st.columns(2)
                    if col_save.button("Save", use_container_width=True):
                        return st.session_state.edit_last_input.strip()
                    if col_cancel.button("Cancel", use_container_width=True):
                        st.session_state.is_editing_last_user = False
                        st.rerun()
                else:
                    content_col, edit_col = st.columns([12, 1])
                    content_col.markdown(msg.content)
                    if edit_col.button("✏️", key=f"edit_last_btn_{idx}", help="Edit last message"):
                        st.session_state.is_editing_last_user = True
                        st.session_state.edit_last_input = msg.content
                        st.rerun()
            else:
                st.markdown(msg.content)
    return None


def submit_last_message_edit(edited_message: str) -> None:
    if not edited_message:
        st.error("Edited message cannot be empty.")
        return
    if not st.session_state.user_id:
        st.error("Please enter and save a User ID in the sidebar first.")
        return

    ws_url = st.session_state.ws_url or build_ws_url(
        st.session_state.backend,
        st.session_state.user_id,
        st.session_state.conversation_id,
    )
    st.session_state.ws_url = ws_url

    with st.chat_message("assistant"):
        placeholder = st.empty()
        try:
            full = ""
            for _, chunk in send_and_stream(
                ws_url,
                edited_message,
                action="edit_last",
            ):
                full = chunk
                placeholder.markdown(full if full else "…")

            st.session_state.messages = fetch_history(
                st.session_state.backend,
                st.session_state.user_id,
                st.session_state.conversation_id,
            )
            st.session_state.conversations = fetch_conversations(
                st.session_state.backend,
                st.session_state.user_id,
            )
            st.session_state.is_editing_last_user = False
            st.rerun()
        except Exception as e:
            placeholder.error(f"WebSocket error: {e}")


def main():
    st.set_page_config(page_title="Recipe Chat", page_icon="🥘", layout="wide")
    init_state()

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

    last_user_idx, last_user_message = get_last_user_message_info(st.session_state.messages)
    if last_user_message is not None and last_user_idx is not None:
        source_key = f"{st.session_state.conversation_id}:{last_user_idx}:{last_user_message}"
        if st.session_state.edit_last_source != source_key:
            st.session_state.edit_last_source = source_key
            st.session_state.edit_last_input = last_user_message
    else:
        st.session_state.is_editing_last_user = False

    edited_message = render_history(last_user_idx)
    if edited_message is not None:
        submit_last_message_edit(edited_message)
        return

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
                st.rerun()
            except Exception as e:
                placeholder.error(f"WebSocket error: {e}")


if __name__ == "__main__":
    main()