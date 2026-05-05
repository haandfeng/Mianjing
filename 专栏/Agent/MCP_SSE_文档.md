# MCP & SSE 技术文档

## 1. SSE 在前后端如何交互？

```
前端 (浏览器/Client)              后端 (Server)
        |                               |
        |  GET /sse                     |
        |  Accept: text/event-stream    |
        |──────────────────────────────>|
        |                               |  连接建立，不关闭
        |  data: {"msg": "hello"}       |
        |<──────────────────────────────|
        |  data: {"msg": "world"}       |
        |<──────────────────────────────|
        |  data: [DONE]                 |
        |<──────────────────────────────|
        |                               |  服务端主动关闭 or 客户端断开
```

- 前端发一次普通 HTTP GET，连接**保持打开不关闭**
- 后端不断往这个连接写数据（单向：server → client）
- 前端用 `EventSource` API 监听：

```javascript
const es = new EventSource("/sse")
es.onmessage = (e) => console.log(JSON.parse(e.data))
```

---

## 2. 后端推送的数据格式

SSE 是纯文本协议，格式固定：

```
data: 你的内容\n\n
```

每条消息以**两个换行**结尾作为分隔符。完整字段有四个：

```
id: 123
event: tool_call
data: {"key": "value"}
retry: 3000

```

| 字段 | 作用 |
|------|------|
| `data` | 消息内容（必填，通常是 JSON 字符串）|
| `event` | 事件类型，客户端可按类型订阅 |
| `id` | 消息 ID，断线重连时用 `Last-Event-ID` 续传 |
| `retry` | 断线后重连等待毫秒数 |

---

## 3. 流式数据是怎么读写的？

### 后端：写流

后端的本质是**向一个长连接持续写文本**，写完一段就 flush，不等全部完成再返回。

**Python（FastAPI）示例：**

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import asyncio, json

app = FastAPI()

async def generate():
    tokens = ["你", "好", "世", "界"]
    for token in tokens:
        data = json.dumps({"delta": token}, ensure_ascii=False)
        yield f"data: {data}\n\n"
        await asyncio.sleep(0.1)          # 模拟 LLM 逐 token 生成
    yield "data: [DONE]\n\n"

@app.get("/stream")
async def stream():
    return StreamingResponse(generate(), media_type="text/event-stream")
```

关键点：
- `yield` 每次输出一段，框架自动 flush 到客户端
- `media_type="text/event-stream"` 告诉浏览器这是 SSE
- 格式必须是 `data: ...\n\n`，两个 `\n` 是分隔符

---

### 前端：读流（方式一）EventSource

```javascript
// 适合 GET 请求，浏览器原生支持
const es = new EventSource("/stream")

es.onmessage = (e) => {
    if (e.data === "[DONE]") {
        es.close()
        return
    }
    const { delta } = JSON.parse(e.data)
    document.getElementById("output").textContent += delta
}

es.onerror = () => es.close()
```

缺点：EventSource 只支持 GET，不能带 body（无法传参数）。

---

### 前端：读流（方式二）fetch + ReadableStream

```javascript
// 支持 POST，可以带 body，更灵活
const response = await fetch("/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt: "你好" }),
})

const reader = response.body.getReader()
const decoder = new TextDecoder()

while (true) {
    const { done, value } = await reader.read()  // 读一块二进制数据
    if (done) break

    const text = decoder.decode(value)            // 解码成字符串
    const lines = text.split("\n")

    for (const line of lines) {
        if (!line.startsWith("data: ")) continue
        const payload = line.slice(6)             // 去掉 "data: " 前缀
        if (payload === "[DONE]") break
        const { delta } = JSON.parse(payload)
        document.getElementById("output").textContent += delta
    }
}
```

---

### Python：读流（作为 Client）

```python
import httpx

with httpx.stream("POST", "http://localhost:8000/stream", json={"prompt": "你好"}) as r:
    for line in r.iter_lines():
        if not line.startswith("data: "):
            continue
        payload = line[6:]                        # 去掉 "data: " 前缀
        if payload == "[DONE]":
            break
        data = json.loads(payload)
        print(data["delta"], end="", flush=True)
```

---

### 流式读写总结

```
后端写                           前端/客户端读
─────────────────────────────────────────────────────
yield f"data: {json}\n\n"   →   逐行读，找 data: 开头
flush（框架自动）            →   去掉前缀，JSON.parse
不等全部完成，写一段推一段   →   拼接到 UI，实时展示
最后 yield "data: [DONE]\n\n" → 收到 [DONE] 停止读取
```

---

## 4. 工具调用时 SSE 事件结构

以 Anthropic API 为例，工具调用会经历这几个事件：

```
# 1. 开始一个新的 content block（类型是 tool_use）
event: content_block_start
data: {
  "type": "content_block_start",
  "index": 0,
  "content_block": {
    "type": "tool_use",
    "id": "toolu_abc123",
    "name": "add",
    "input": {}
  }
}

# 2. 流式传入参数 JSON（可能分多块）
event: content_block_delta
data: {
  "type": "content_block_delta",
  "index": 0,
  "delta": {
    "type": "input_json_delta",
    "partial_json": "{\"a\": 10,"
  }
}

event: content_block_delta
data: {
  "delta": { "partial_json": "\"b\": 32}" }
}

# 3. 这个 block 结束
event: content_block_stop
data: { "type": "content_block_stop", "index": 0 }

# 4. 整条消息结束
event: message_delta
data: {
  "type": "message_delta",
  "delta": { "stop_reason": "tool_use" }
}
```

| 字段 | 含义 |
|------|------|
| `type` | 事件类型（content_block_start / delta / stop）|
| `content_block.type` | `tool_use` 表示这是工具调用 |
| `content_block.id` | 工具调用 ID，返回结果时要带上 |
| `content_block.name` | 调用的工具名 |
| `delta.partial_json` | 参数 JSON 的流式分片 |
| `stop_reason` | `tool_use` 表示 LLM 需要工具结果才能继续 |

---

## 5. MCP 完整交互流程

```
Client                          MCP Server
  |                                  |
  |─── initialize ──────────────────>|  握手：协商版本、能力
  |<── initialized ──────────────────|
  |                                  |
  |─── tools/list ──────────────────>|  查询有哪些工具
  |<── [{name, description, schema}] |
  |                                  |
  |─── tools/call ──────────────────>|  调用工具
  |    { name: "add", args: {a,b} }  |
  |<── { content: [{text: "42"}] } ──|  返回结果
  |                                  |
  |─── (可继续调用其他工具) ─────────>|
  |                                  |
  |─── (Client 主动断开) ────────────>|
```

所有消息都是 **JSON-RPC 2.0** 格式：

```json
// 请求
{ "jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {...} }

// 响应
{ "jsonrpc": "2.0", "id": 1, "result": {...} }
```

---

## 6. Agent 如何与 MCP Server 连接通信

两种模式，本质区别只在**传输层**：

### stdio 模式（本地）

```
Agent 进程
  └── 子进程: mcp_server.py
        ├── stdin  ←─ Agent 写 JSON-RPC 请求
        └── stdout ──→ Agent 读 JSON-RPC 响应
```

Agent 直接 spawn 一个子进程，读写它的标准输入输出，不走网络。适合本地工具（Claude Desktop 用这种）。

### SSE 模式（远程）

```
Agent
  ├── GET http://server/sse      → 建立 SSE 长连接（接收响应用）
  └── POST http://server/messages → 发送请求

MCP Server
  ├── /sse       接受 SSE 连接，等待推送时机
  └── /messages  接收 POST 请求，处理后通过 SSE 通道推回结果
```

**为什么 SSE 模式需要两个端点？**

因为 SSE 是单向的（server→client），所以：

- 发请求用 `POST /messages`（client→server）
- 收响应用 `GET /sse` 的推送（server→client）
- 两者合起来才实现了双向通信

### 两种模式对比

| | stdio | SSE |
|---|---|---|
| 传输介质 | stdin/stdout | HTTP |
| 是否需要网络 | 否 | 是 |
| 适合场景 | 本地工具 | 远程部署、多客户端 |
| 启动方式 | Agent 作为父进程 spawn | Server 独立运行 |
