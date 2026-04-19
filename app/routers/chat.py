from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from langchain_core.messages import AIMessage, HumanMessage

from app.repository.chat_repository import ChatRepository
from app.graph.builder import build_graph

router = APIRouter(tags=["chat"])

_PLAYGROUND_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>WebSocket Playground — Recipe Chat</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; }
    body { font-family: system-ui, sans-serif; max-width: 820px; margin: 40px auto; padding: 0 20px; background: #0f0f0f; color: #e0e0e0; }
    h1 { color: #fff; margin-bottom: 4px; }
    p.sub { color: #666; font-size: 13px; margin-top: 0; margin-bottom: 24px; }
    .row { display: flex; gap: 10px; margin-bottom: 14px; align-items: center; }
    label { min-width: 140px; color: #888; font-size: 13px; }
    input[type=text] { flex: 1; padding: 8px 12px; border: 1px solid #2a2a2a; border-radius: 6px; background: #1a1a1a; color: #e0e0e0; font-size: 14px; outline: none; }
    input[type=text]:focus { border-color: #444; }
    button { padding: 8px 18px; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 500; transition: opacity .15s; }
    button:disabled { opacity: .4; cursor: default; }
    #connectBtn { background: #16a34a; color: #fff; }
    #connectBtn.on { background: #dc2626; }
    #sendBtn { background: #2563eb; color: #fff; }
    #clearBtn { background: #262626; color: #aaa; }
    #status { font-size: 12px; padding: 4px 10px; border-radius: 4px; }
    .s-off { background: #1c1c1c; color: #666; }
    .s-on  { background: #14532d; color: #86efac; }
    .s-err { background: #450a0a; color: #fca5a5; }
    #msgInput { width: 100%; padding: 10px 12px; border: 1px solid #2a2a2a; border-radius: 6px; background: #1a1a1a; color: #e0e0e0; font-size: 14px; outline: none; margin-bottom: 10px; }
    #msgInput:focus { border-color: #444; }
    .btn-row { display: flex; gap: 8px; margin-bottom: 16px; }
    #output { background: #0a0a0a; border: 1px solid #1e1e1e; border-radius: 8px; padding: 16px; min-height: 320px; max-height: 520px; overflow-y: auto; font-family: ui-monospace, monospace; font-size: 13px; }
    .u { color: #60a5fa; margin: 10px 0 3px; } /* user */
    .a { color: #a3e635; margin: 3px 0 10px; } /* ai */
    .e { color: #f87171; }                      /* error */
    .s { color: #555; font-style: italic; }     /* system */
  </style>
</head>
<body>
  <h1>&#x1F373; Recipe Chat &mdash; WebSocket Playground</h1>
  <p class="sub">Real-time streaming chat. Tokens stream as they arrive from the LLM.</p>

  <div class="row">
    <label>User ID</label>
    <input id="uid" type="text" value="user1" />
  </div>
  <div class="row">
    <label>Conversation ID</label>
    <input id="cid" type="text" value="conv1" />
  </div>
  <div class="row">
    <button id="connectBtn" onclick="toggle()">Connect</button>
    <span id="status" class="s-off">Disconnected</span>
  </div>

  <input id="msgInput" type="text" placeholder="Type a message and press Enter…" disabled
         onkeydown="if(event.key==='Enter')send()" />
  <div class="btn-row">
    <button id="sendBtn" onclick="send()" disabled>Send</button>
    <button id="clearBtn" onclick="out.innerHTML=''">Clear</button>
    <a href="/docs" style="margin-left:auto;color:#555;font-size:13px;align-self:center;">Back to Swagger →</a>
  </div>
  <div id="output"><span class="s">Connect to start chatting…</span></div>

  <script>
    let ws = null, cur = null;
    const out = document.getElementById('output');

    function toggle() { ws ? disc() : conn(); }

    function conn() {
      const uid = document.getElementById('uid').value.trim();
      const cid = document.getElementById('cid').value.trim();
      if (!uid || !cid) { st('Fill in both fields', 'err'); return; }
      const url = `ws://${location.host}/ws/chat/${uid}/${cid}`;
      ws = new WebSocket(url);
      ws.onopen  = () => {
        st('Connected', 'on');
        document.getElementById('connectBtn').textContent = 'Disconnect';
        document.getElementById('connectBtn').classList.add('on');
        document.getElementById('msgInput').disabled = false;
        document.getElementById('sendBtn').disabled = false;
        document.getElementById('msgInput').focus();
        sys(`Connected → /ws/chat/${uid}/${cid}`);
      };
      ws.onmessage = ({ data }) => {
        const d = JSON.parse(data);
        if (d.type === 'token') {
          if (!cur) { cur = mk('a', String.fromCodePoint(0x1F916) + ' '); out.appendChild(cur); }
          cur.textContent += d.content;
          scroll();
        } else if (d.type === 'end') {
          cur = null; scroll();
        } else if (d.type === 'error') {
          line('e', String.fromCodePoint(0x274C) + ' ' + d.content);
        }
      };
      ws.onclose = () => { gone(); sys('Disconnected.'); };
      ws.onerror = () => st('Connection error', 'err');
    }

    function disc() { if (ws) { ws.close(); ws = null; } }

    function gone() {
      ws = null; cur = null;
      st('Disconnected', 'off');
      document.getElementById('connectBtn').textContent = 'Connect';
      document.getElementById('connectBtn').classList.remove('on');
      document.getElementById('msgInput').disabled = true;
      document.getElementById('sendBtn').disabled = true;
    }

    function send() {
      const inp = document.getElementById('msgInput');
      const msg = inp.value.trim();
      if (!msg || !ws) return;
      line('u', String.fromCodePoint(0x1F464) + ' ' + msg);
      ws.send(JSON.stringify({ message: msg }));
      inp.value = ''; cur = null;
    }

    function mk(cls, txt) {
      const d = document.createElement('div');
      d.className = cls; d.textContent = txt; return d;
    }
    function line(cls, txt) { out.appendChild(mk(cls, txt)); scroll(); }
    function sys(txt) { line('s', txt); }
    function st(txt, k) {
      const el = document.getElementById('status');
      el.textContent = txt; el.className = 's-' + k;
    }
    function scroll() { out.scrollTop = out.scrollHeight; }
  </script>
</body>
</html>
"""


@router.get("/ws-playground", response_class=HTMLResponse, include_in_schema=False)
async def ws_playground():
    """Interactive browser-based WebSocket test page."""
    return HTMLResponse(_PLAYGROUND_HTML)


def _to_lc_messages(history: list[dict]) -> list:
    messages = []
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "ai":
            messages.append(AIMessage(content=msg["content"]))
    return messages


def _history_before_last_user_turn(history: list[dict]) -> list[dict]:
    for idx in range(len(history) - 1, -1, -1):
        if history[idx].get("role") == "user":
            return history[:idx]
    raise ValueError("No previous user message found to edit.")


@router.websocket("/ws/chat/{user_id}/{conversation_id}")
async def websocket_chat(
    websocket: WebSocket, user_id: str, conversation_id: str
):
    await websocket.accept()
    chat_repo = ChatRepository(websocket.app.state.redis)
    graph = build_graph()

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action", "send")
            user_message = data.get("message", "").strip()

            if action not in {"send", "edit_last"}:
                await websocket.send_json(
                    {"type": "error", "content": "Unsupported action."}
                )
                continue

            if not user_message:
                await websocket.send_json(
                    {"type": "error", "content": "Message cannot be empty."}
                )
                continue

            history = await chat_repo.get_conversation(user_id, conversation_id)

            if action == "edit_last":
                try:
                    history = _history_before_last_user_turn(history)
                except ValueError as err:
                    await websocket.send_json(
                        {"type": "error", "content": str(err)}
                    )
                    continue

                await chat_repo.replace_messages(user_id, conversation_id, history)

            lc_history = _to_lc_messages(history)

            initial_state = {
                "messages": lc_history + [HumanMessage(content=user_message)],
                "retrieved_context": "",
            }

            full_response = ""
            async for event in graph.astream_events(initial_state, version="v2"):
                if event["event"] == "on_chat_model_stream":
                    token = event["data"]["chunk"].content
                    if token:
                        full_response += token
                        await websocket.send_json(
                            {"type": "token", "content": token}
                        )

            await chat_repo.append_messages(
                user_id,
                conversation_id,
                [
                    {"role": "user", "content": user_message},
                    {"role": "ai", "content": full_response},
                ],
            )

            await websocket.send_json({"type": "end", "content": full_response})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "content": str(e)})
        except Exception:
            pass


@router.get("/chat/{user_id}/{conversation_id}/history")
async def get_history(user_id: str, conversation_id: str, request: Request):
    chat_repo = ChatRepository(request.app.state.redis)
    messages = await chat_repo.get_conversation(user_id, conversation_id)
    return {"messages": messages}
