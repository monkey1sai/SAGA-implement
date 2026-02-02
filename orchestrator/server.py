"""
sglangRAG Orchestrator Server

簡化版 orchestrator，支援：
- WebSocket 聊天介面
- RAG 檢索增強（可選）
- SGLang LLM 串流回覆

移除了 TTS 相關功能。
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import aiohttp
from aiohttp import WSMsgType, web


def json_dumps(obj: Any) -> str:
    """JSON 序列化，無額外空格"""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


async def ws_send_json(ws: web.WebSocketResponse, payload: Dict[str, Any]) -> None:
    """透過 WebSocket 發送 JSON"""
    await ws.send_str(json_dumps(payload))


def _require_str(obj: Dict[str, Any], key: str) -> str:
    val = obj.get(key)
    if not isinstance(val, str) or not val:
        raise ValueError(f"欄位 {key} 必須是非空字串")
    return val


def _optional_bool(obj: Dict[str, Any], key: str, default: bool = True) -> bool:
    val = obj.get(key)
    if val is None:
        return default
    return bool(val)


def _optional_int_env(name: str) -> Optional[int]:
    v = os.getenv(name)
    if v is None or not v.strip():
        return None
    try:
        return int(v)
    except Exception:
        raise ValueError(f"環境變數 {name} 必須是整數")


def _optional_float_env(name: str) -> Optional[float]:
    v = os.getenv(name)
    if v is None or not v.strip():
        return None
    try:
        return float(v)
    except Exception:
        raise ValueError(f"環境變數 {name} 必須是數字")


def _bool_env(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


def _build_sampling_overrides() -> Dict[str, Any]:
    """
    Build optional OpenAI-compatible sampling params for SGLang.
    """
    overrides: Dict[str, Any] = {}

    max_tokens = _optional_int_env("SGLANG_MAX_TOKENS")
    if max_tokens is not None and max_tokens > 0:
        overrides["max_tokens"] = max_tokens

    temperature = _optional_float_env("SGLANG_TEMPERATURE")
    if temperature is not None and temperature >= 0:
        overrides["temperature"] = temperature

    top_p = _optional_float_env("SGLANG_TOP_P")
    if top_p is not None and 0 <= top_p <= 1:
        overrides["top_p"] = top_p

    top_k = _optional_int_env("SGLANG_TOP_K")
    if top_k is not None and top_k > 0:
        overrides["top_k"] = top_k

    repetition_penalty = _optional_float_env("SGLANG_REPETITION_PENALTY")
    if repetition_penalty is not None and repetition_penalty > 0:
        overrides["repetition_penalty"] = repetition_penalty

    return overrides


@dataclass
class ChatMessage:
    """單一聊天訊息"""
    type: str  # "chat"
    text: str
    use_rag: bool = True

    @staticmethod
    def parse(obj: Dict[str, Any]) -> "ChatMessage":
        return ChatMessage(
            type=obj.get("type", "chat"),
            text=_require_str(obj, "text"),
            use_rag=_optional_bool(obj, "use_rag", True),
        )


@dataclass
class ConversationContext:
    """對話上下文管理"""
    messages: List[Dict[str, str]] = field(default_factory=list)
    
    def add_user_message(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})
    
    def add_assistant_message(self, content: str) -> None:
        self.messages.append({"role": "assistant", "content": content})
    
    def get_messages(self, system_prompt: Optional[str] = None) -> List[Dict[str, str]]:
        result = []
        if system_prompt:
            result.append({"role": "system", "content": system_prompt})
        result.extend(self.messages)
        return result


def _build_sglang_url() -> str:
    base = os.getenv("SGLANG_BASE_URL", "http://localhost:8082").rstrip("/")
    return f"{base}/v1/chat/completions"


def _build_rag_url() -> str:
    base = os.getenv("RAG_SERVICE_URL", "http://localhost:8100").rstrip("/")
    return f"{base}/search"


async def _query_rag(
    client: aiohttp.ClientSession,
    query: str,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """查詢 RAG 服務獲取相關上下文"""
    rag_url = _build_rag_url()
    
    try:
        payload = {
            "query": query,
            "top_k": top_k,
            "use_rerank": True,
        }
        
        async with client.post(rag_url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status != 200:
                print(f"[RAG] 查詢失敗: {resp.status}")
                return []
            
            data = await resp.json()
            return data.get("results", [])
    except Exception as e:
        print(f"[RAG] 查詢錯誤: {e}")
        return []


def _format_rag_context(results: List[Dict[str, Any]]) -> str:
    """將 RAG 結果格式化為上下文文字"""
    if not results:
        return ""
    
    context_parts = []
    for i, r in enumerate(results, 1):
        content = r.get("content", "")
        source = r.get("metadata", {}).get("source", "unknown")
        score = r.get("score", 0)
        context_parts.append(f"[文檔 {i}] (來源: {source}, 相關度: {score:.2f})\n{content}")
    
    return "\n\n---\n\n".join(context_parts)


async def _stream_sglang_response(
    *,
    client: aiohttp.ClientSession,
    messages: List[Dict[str, str]],
    ws: web.WebSocketResponse,
    stop: asyncio.Event,
) -> str:
    """串流 SGLang LLM 回覆"""
    sglang_url = _build_sglang_url()
    api_key = os.getenv("SGLANG_API_KEY", "")
    model = os.getenv("SGLANG_MODEL", "twinkle-ai/Llama-3.2-3B-F1-Instruct")

    if not api_key:
        raise RuntimeError("缺少環境變數 SGLANG_API_KEY")

    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": True,
    }
    payload.update(_build_sampling_overrides())

    headers = {"Authorization": f"Bearer {api_key}"}
    full_text = ""

    async with client.post(sglang_url, json=payload, headers=headers) as resp:
        if resp.status != 200:
            body = (await resp.text())[:2000]
            raise RuntimeError(f"SGLang 回應 {resp.status}: {body}")

        while not stop.is_set():
            line = await resp.content.readline()
            if not line:
                break
            
            s = line.decode("utf-8", errors="replace").strip()
            if not s.startswith("data: "):
                continue
            if s == "data: [DONE]":
                break

            try:
                delta = json.loads(s[6:])["choices"][0]["delta"]
            except Exception:
                continue

            content = delta.get("content")
            if isinstance(content, str) and content:
                full_text += content
                await ws_send_json(ws, {"type": "llm_delta", "delta": content})

    return full_text


async def ws_chat_handler(request: web.Request) -> web.WebSocketResponse:
    """WebSocket 聊天端點 /ws/chat"""
    
    # API Key 驗證（可選）
    expected = os.getenv("ORCH_API_KEY", "").strip()
    if expected:
        got = request.query.get("api_key", "").strip()
        auth = request.headers.get("Authorization", "")
        bearer = ""
        if auth:
            parts = auth.strip().split(" ", 1)
            if len(parts) == 2 and parts[0].lower() == "bearer":
                bearer = parts[1].strip()
        if got != expected and bearer != expected:
            raise web.HTTPUnauthorized(text="missing/invalid api_key")

    ws = web.WebSocketResponse(heartbeat=20)
    await ws.prepare(request)

    client: aiohttp.ClientSession = request.app["client_session"]
    context = ConversationContext()
    
    # 系統提示詞
    system_prompt = os.getenv("SGLANG_SYSTEM_PROMPT", "").strip()
    rag_prompt_template = os.getenv(
        "RAG_PROMPT_TEMPLATE",
        "根據以下參考資料回答問題。如果資料中沒有相關內容，請說明你不確定。\n\n參考資料：\n{context}\n\n問題：{query}"
    )

    await ws_send_json(ws, {"type": "connected", "message": "歡迎使用 sglangRAG"})

    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                except Exception:
                    await ws_send_json(ws, {"type": "error", "message": "無效的 JSON 格式"})
                    continue

                msg_type = data.get("type", "")
                
                if msg_type == "chat":
                    try:
                        chat_msg = ChatMessage.parse(data)
                    except Exception as e:
                        await ws_send_json(ws, {"type": "error", "message": str(e)})
                        continue

                    stop = asyncio.Event()
                    start_time = time.perf_counter()
                    
                    user_text = chat_msg.text
                    rag_context = ""
                    
                    # RAG 檢索
                    if chat_msg.use_rag:
                        rag_results = await _query_rag(client, user_text)
                        if rag_results:
                            rag_context = _format_rag_context(rag_results)
                            await ws_send_json(ws, {
                                "type": "rag_context",
                                "results": rag_results,
                                "count": len(rag_results),
                            })
                    
                    # 構建提示詞
                    if rag_context:
                        enhanced_prompt = rag_prompt_template.format(
                            context=rag_context,
                            query=user_text,
                        )
                        context.add_user_message(enhanced_prompt)
                    else:
                        context.add_user_message(user_text)
                    
                    messages = context.get_messages(system_prompt)
                    
                    try:
                        full_response = await _stream_sglang_response(
                            client=client,
                            messages=messages,
                            ws=ws,
                            stop=stop,
                        )
                        
                        context.add_assistant_message(full_response)
                        
                        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
                        await ws_send_json(ws, {
                            "type": "llm_complete",
                            "elapsed_ms": elapsed_ms,
                            "response_length": len(full_response),
                        })
                        
                    except Exception as e:
                        await ws_send_json(ws, {
                            "type": "error",
                            "message": f"LLM 錯誤: {str(e)}",
                        })
                
                elif msg_type == "clear":
                    # 清除對話上下文
                    context = ConversationContext()
                    await ws_send_json(ws, {"type": "cleared"})
                
                elif msg_type == "ping":
                    await ws_send_json(ws, {"type": "pong"})
                
                else:
                    await ws_send_json(ws, {"type": "error", "message": f"未知訊息類型: {msg_type}"})

            elif msg.type == WSMsgType.ERROR:
                print(f"[WS] 錯誤: {ws.exception()}")
                break

    except asyncio.CancelledError:
        pass
    except Exception as e:
        try:
            await ws_send_json(ws, {"type": "error", "message": f"伺服器錯誤: {str(e)}"})
        except Exception:
            pass
    finally:
        await ws.close()

    return ws


async def healthz(_: web.Request) -> web.Response:
    """健康檢查端點"""
    return web.json_response({"status": "ok", "service": "sglangRAG-orchestrator"})


async def on_startup(app: web.Application) -> None:
    """啟動時初始化 HTTP client"""
    app["client_session"] = aiohttp.ClientSession()
    print("[Orchestrator] 服務已啟動")


async def on_cleanup(app: web.Application) -> None:
    """清理資源"""
    await app["client_session"].close()
    print("[Orchestrator] 服務已關閉")


def create_app() -> web.Application:
    """建立 aiohttp 應用"""
    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    
    # 路由
    app.router.add_get("/healthz", healthz)
    app.router.add_get("/ws/chat", ws_chat_handler)
    
    # 相容舊端點
    app.router.add_get("/chat", ws_chat_handler)
    
    return app


def main() -> None:
    """主程式進入點"""
    host = os.getenv("ORCH_HOST", "0.0.0.0")
    port = int(os.getenv("ORCH_PORT", "9100"))
    
    print(f"[Orchestrator] 啟動於 {host}:{port}")
    print(f"[Orchestrator] SGLang URL: {_build_sglang_url()}")
    print(f"[Orchestrator] RAG URL: {_build_rag_url()}")
    
    app = create_app()
    web.run_app(app, host=host, port=port)


if __name__ == "__main__":
    main()
