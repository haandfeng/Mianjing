---
title: 三家大模型API协议对比（OpenAI / Anthropic / Gemini）
tags:
  - Agent
  - LLM-API
  - LangChain
  - 面试八股
date: 2026-05-24
---

> **归档说明**：本页为学习材料 / 历史笔记，保留原文和当时记录；主题解释见 [[LLM多协议网关适配]]。


# OpenAI / Anthropic / Gemini 三家 API 协议全对比

> 一句话心智模型：
> - **OpenAI**：扁平。`messages` 数组，system 混在里面，content 能用字符串偷懒。
> - **Anthropic**：显式。`system` 拎出来单放，content 永远是「块」，结构最规整。
> - **Gemini**：换词。`messages`→`contents`、`content`→`parts`、`assistant`→`model`，采样参数全塞进 `generationConfig`。

贯穿全篇的三层抽象：**协议层（HTTP/JSON）→ 官方 SDK 层（Python 对象）→ 框架层（LangChain）**。越往上差异越被抹平，但厂商独有的好东西（缓存 / 思考 / 签名）越容易被挡住，要榨它们就得往下沉。

---

## 一、地基：一次 API 调用长什么样

跟模型聊天，本质是**一个消息列表**。每条消息只有两样东西：

- **谁说的** = `role`（角色）
- **说了啥** = `content`（内容）

| role | 是谁 | 大白话 |
|---|---|---|
| `system` | 给 AI 的设定 | 幕后导演定规矩 |
| `user` | 你（人类） | 你问的话 |
| `assistant` | **AI 自己** | **AI 的回复就叫 assistant**（Gemini 改名 `model`） |

```jsonc
"messages": [
  {"role": "system",    "content": "你是翻译助手"},
  {"role": "user",      "content": "把 hello 翻成中文"},
  {"role": "assistant", "content": "你好"},
  {"role": "user",      "content": "那 world 呢"}
]
```

**多轮 = 不停往列表后面追加。** 关键：API 没记忆，每次请求都要把整段历史重发，AI 才知道之前聊了啥（后面 signature、缓存都因为这点而存在）。

三个名词对照：

| 概念 | OpenAI | Anthropic | Gemini |
|---|---|---|---|
| 对话字段（装消息列表） | `messages` | `messages` | `contents` |
| 内容字段（装"说了啥"） | `content` | `content` | `parts` |
| 助手角色（AI 那条） | `assistant` | `assistant` | `model` |

---

## 二、端点与认证

```bash
# OpenAI
curl https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $KEY"

# Anthropic —— 必须带 anthropic-version
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $KEY" -H "anthropic-version: 2023-06-01"

# Gemini —— 模型名在 URL 路径里
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro:generateContent" \
  -H "x-goog-api-key: $KEY"
```

坑：Gemini 模型名在 URL；Anthropic 漏 `anthropic-version` 头直接报错。

---

## 三、协议差异速查

| 维度 | OpenAI | Anthropic | Gemini |
|------|--------|-----------|--------|
| 对话字段 | `messages` | `messages` | `contents` |
| 内容字段 | `content`（可字符串） | `content`（块数组） | `parts` |
| 助手角色 | `assistant` | `assistant` | `model` |
| system 放哪 | messages 里一条 | 顶层 `system` | 顶层 `systemInstruction` |
| 模型名在哪 | body | body | **URL 路径** |
| 采样参数位置 | body 顶层 | body 顶层 | `generationConfig` 内 |
| 工具 schema 字段 | `function.parameters` | `input_schema` | `functionDeclarations` |
| 工具参数返回 | **JSON 字符串** | dict | dict |
| 工具结果回传 | 新增 `role:"tool"` | 塞回 `role:"user"` 的 `tool_result` | `role:"function"` 的 `functionResponse` |
| 命名风格 | snake_case | snake_case | **camelCase** |

---

## 四、发起请求：同步 / 异步 / 流式

用打电话比喻：
- **同步**：举着电话干等到对方说完。
- **异步**：发微信问完去干别的，回了再处理（适合并发服务很多用户）。
- **流式**：对方说一个字你收一个字（ChatGPT 打字机效果）。

> 流式和异步是两个独立维度，可组合。学习/写脚本用同步即可；想要打字机效果加流式；做并发后端才需要异步。

### OpenAI

```python
from openai import OpenAI, AsyncOpenAI
client, aclient = OpenAI(), AsyncOpenAI()

# 同步
r = client.chat.completions.create(model="gpt-4o", messages=msgs)

# 同步流式：for 循环读 delta（增量）
for chunk in client.chat.completions.create(model="gpt-4o", messages=msgs, stream=True):
    piece = chunk.choices[0].delta.content      # delta = 这一块新增的文字
    if piece:
        print(piece, end="", flush=True)        # 不换行 + 立即刷出 → 打字机

# 异步：async def + await
import asyncio
async def main():
    r = await aclient.chat.completions.create(model="gpt-4o", messages=msgs)
    # 异步流式：async for
    async for chunk in await aclient.chat.completions.create(..., stream=True):
        ...
asyncio.run(main())
```

语法点：`async def` 定义异步函数；`await` 表示"在这等结果，但 CPU 可去干别的"；`async for` 异步遍历流；`asyncio.run()` 启动。

### Anthropic（流式最省心）

```python
from anthropic import Anthropic, AsyncAnthropic
client, aclient = Anthropic(), AsyncAnthropic()

r = client.messages.create(model="claude-opus-4-7", max_tokens=1024, messages=msgs)

# 流式：with 上下文管理器 + text_stream（已帮你提取好文字）
with client.messages.stream(model="claude-opus-4-7", max_tokens=1024, messages=msgs) as s:
    for text in s.text_stream:
        print(text, end="", flush=True)
    final = s.get_final_message()
```

### Gemini（新包 google-genai）

```python
from google import genai
client = genai.Client()

r = client.models.generate_content(model="gemini-3-pro", contents="...")

# 流式：专门方法 generate_content_stream
for chunk in client.models.generate_content_stream(model="gemini-3-pro", contents="..."):
    print(chunk.text, end="", flush=True)

# 异步：统一走 client.aio.*
r = await client.aio.models.generate_content(model="gemini-3-pro", contents="...")
```

> Gemini 注意装新包 `google-genai`（`genai.Client`），旧包 `google-generativeai`（`genai.GenerativeModel`）已弃用。

| | 同步入口 | 异步 | 流式方法 | 流式拆包 |
|---|---|---|---|---|
| OpenAI | `chat.completions.create` | `AsyncOpenAI`+await | 同方法 `stream=True` | `chunk.choices[0].delta.content` |
| Anthropic | `messages.create` | `AsyncAnthropic`+await | `messages.stream()` | `s.text_stream`（已拼好） |
| Gemini | `models.generate_content` | `client.aio.*`+await | `generate_content_stream` | `chunk.text` |

---

## 五、请求参数 & 性能参数

### max_tokens —— 最易误解

**本次最多生成多少 token（只算输出，不含输入）**，不是上下文总长。
- OpenAI：`max_completion_tokens`（旧 `max_tokens` 弃用），可选。
- Anthropic：`max_tokens`，**必填**。
- Gemini：`maxOutputTokens`，可选。

**陷阱（三家通用）**：开思考后，思考 token 也算进 max_tokens 并按输出价计费。设太小会"额度全花在思考上、返回空内容"。

### 采样参数

| | temperature | top_p | top_k | 停止词 | 重复惩罚 | seed | 生成几条 |
|---|---|---|---|---|---|---|---|
| OpenAI | 0–2（默认1） | 有 | 无 | `stop` | 有 | 有 | `n` |
| Anthropic | 0–1（默认1） | 有 | 有 | `stop_sequences` | 无 | 无 | 无 |
| Gemini | 0–2 | `topP` | `topK` | `stopSequences` | 有 | 有 | `candidateCount` |

注意：同一 temperature 数值三家行为不同（上限 2 vs 1），迁移别照搬；开推理/思考后采样参数常被锁死（OpenAI 推理模型不支持 temperature，Claude 开思考时 temperature 强制为 1）。

---

## 六、思考模式 & 思考强度（2026 已分化，重点）

思考强度 = 让模型回答前"内部琢磨多久"的旋钮。**调高 → 准确率↑、延迟↑、花费↑**。简单任务用低强度省钱，复杂任务（数学/代码/多步/agent）用高强度换正确率。

### OpenAI：reasoning_effort（挡板式）

```python
client.chat.completions.create(model="gpt-5", messages=msgs,
                               reasoning_effort="medium")  # minimal/low/medium/high(部分有 none/xhigh)
# Responses API: reasoning={"effort": "medium"}
```
推理过程不返回，但按输出价计费，`usage` 里能看到 reasoning_tokens。

### Anthropic：4.7 大改 —— effort + 自适应思考

```python
client.messages.create(model="claude-opus-4-7", max_tokens=4096,
                       output_config={"effort": "high"},   # low/medium/high/xhigh/max
                       messages=msgs)
```
- 等级 `low/medium/high/xhigh/max`，默认 `high`；`xhigh` 是 4.7 新增、官方推荐用于编码/agent；`max` 仅 Opus 档。
- **`budget_tokens` 在 Opus 4.7 被移除**，老写法 `thinking={"type":"enabled","budget_tokens":N}` 会 400 报错；4.7 思考是自适应的，交错思考自动开启。
- 旧模型（Sonnet 3.7/4/4.5）仍用 `thinking={budget_tokens:N}`（budget < max_tokens）。

### Gemini：按代不同

```python
from google.genai import types
# 2.5 系：token 预算
types.ThinkingConfig(thinking_budget=2048, include_thoughts=True)  # 0=关 -1=动态
# Gemini 3 系：等级制（像 effort）
types.ThinkingConfig(thinking_level="high")  # minimal/low/medium/high
```
`include_thoughts=True` 会返回思考摘要。

| | 调节方式 | 思考可见 | 关键坑 |
|---|---|---|---|
| OpenAI | `reasoning_effort` 等级 | 否 | temperature 不可用 |
| Anthropic 4.7 | `output_config.effort` + 自适应 | 是（thinking 块） | budget_tokens 已废，用了报错 |
| Gemini | 2.5 budget / 3 level | 摘要 | budget 太小会截断 |

---

## 七、Signature（签名）：三家都有

> "三家都有把加密的思考状态回传的机制，本质是为了在多轮/工具调用里**保持推理连续性 + 防篡改**。"

因为 API 没记忆，模型上一步的"想法"下一步要由你原样发回，它才能接着想。这些想法被加密打包成一串带签名的乱码：你看不懂内容（加密），下次原样交回（回传），服务器验证它没被改过（防篡改），于是接着推理（连续性）。**像火漆封印的寄存小票**。

- **Gemini** `thoughtSignature`：Gemini 3 做函数调用时**必须原样回传**，否则 400。
- **Anthropic** thinking 块的 `signature`：开思考 + 工具调用时必须连签名原样回传。
- **OpenAI** Responses API 的 `encrypted_content`：无状态模式下需回传以保留推理链。

实操：用官方 SDK 把上一轮完整回复原样 append 回历史，SDK 自动处理；只有手搓 HTTP 才要操心。

---

## 八、工具调用三步曲

模型只会"说话"，不能真查天气/跑代码。给它配工具，三步：

1. **声明工具（schema）**：用 JSON 告诉模型"有个工具叫 get_weather，要参数 city（字符串）"。这份说明书就是 schema。
2. **模型返回"要调用"（工具参数返回）**：模型不执行，只回"请调 get_weather，city='北京'"。OpenAI 给字符串（要 `json.loads`），另两家给 dict。
3. **你执行并回传（工具结果回传）**：代码真查到"晴25℃"，作为新消息塞回对话，模型再给最终人话。

> 比喻：学生（模型）不会按计算器，写"请算 3+5"，监考（你的代码）算出 8 递回去，学生再写最终答案。

回传方式：OpenAI 新增 `role:"tool"`；Anthropic 塞回 `role:"user"` 的 `tool_result` 块；Gemini 用 `role:"function"` 的 `functionResponse`。

```python
# Anthropic 完整一轮
tool_use = next(b for b in resp.content if b.type == "tool_use")
args = tool_use.input                              # dict，直接用
messages.append({"role": "assistant", "content": resp.content})
messages.append({"role": "user", "content": [
    {"type": "tool_result", "tool_use_id": tool_use.id, "content": "晴,25℃"}]})
```

> Gemini 独有：传 Python 函数可**自动调用闭环**（SDK 自动生成 schema、调用、回传）。

---

## 九、返回值格式

三家都表达同一套信息（答案 + 为什么停 + 用了多少 token），只是嵌套和命名不同。

```jsonc
// OpenAI
{"choices":[{"message":{"role":"assistant","content":"你好"},"finish_reason":"stop"}],
 "usage":{"prompt_tokens":10,"completion_tokens":8,"total_tokens":18}}
// 取答案 resp.choices[0].message.content

// Anthropic（content 是块数组，可能混 thinking/tool_use/text）
{"content":[{"type":"text","text":"你好"}],"stop_reason":"end_turn",
 "usage":{"input_tokens":10,"output_tokens":8}}
// 取答案 遍历 content 找 type=="text"

// Gemini（层级最深）
{"candidates":[{"content":{"parts":[{"text":"你好"}],"role":"model"},"finishReason":"STOP"}],
 "usageMetadata":{"promptTokenCount":10,"candidatesTokenCount":8}}
// 取答案 resp.candidates[0].content.parts[0].text 或 SDK 的 resp.text
```

| 信息 | OpenAI | Anthropic | Gemini |
|---|---|---|---|
| 答案 | `choices[0].message.content` | `content[]` 的 text 块 | `candidates[0].content.parts[0].text` |
| 为什么停 | `finish_reason` (stop/length/tool_calls) | `stop_reason` (end_turn/max_tokens/tool_use) | `finishReason` (STOP/MAX_TOKENS) |
| 输入 token | `prompt_tokens` | `input_tokens` | `promptTokenCount` |
| 输出 token | `completion_tokens` | `output_tokens` | `candidatesTokenCount` |

---

## 十、结构化输出（structured output）

强制模型只吐符合指定结构的 JSON，便于代码直接解析（存库 / 传下游）。

```python
from pydantic import BaseModel
class Person(BaseModel):
    name: str
    age: int
```

三家底层实现：
- **OpenAI**：`response_format` + JSON Schema + `strict:true`，约束解码，100% 符合。
- **Anthropic**：早期靠**工具调用变相实现**（造一个假工具，参数 schema 设成想要的结构，用 `tool_choice` 强制模型"调用"，收上来的参数就是结构化结果——本质是借"工具参数必须符合 schema"这个特性）；现也有原生 structured outputs。
- **Gemini**：`responseSchema` + `responseMimeType:"application/json"`，原生。

LangChain 一句搞定（自动选实现）：

```python
structured = llm.with_structured_output(Person)
structured.invoke("张三今年30")   # → Person(name='张三', age=30)
```

`method=` 手动指定底层手段：`"json_schema"`（原生约束，最可靠）/ `"function_calling"`（借工具，最通用）/ `"json_mode"`（只保证合法 JSON，较弱）。一般不填，自动选默认。

---

## 十一、Prompt Caching（提示缓存）

把请求里**重复不变的前缀**（长 system、长文档、多轮历史）缓存住，第二次直接复用、不重新处理 → 更快 + 命中部分约收 1/10 价钱。

- **OpenAI**：自动，前缀相同自动命中。
- **Anthropic**：**手动**，在不变内容块上打 `cache_control: {"type":"ephemeral"}`。最需操心，也最可控，是省钱关键。
- **Gemini**：显式 context cache，先建缓存对象再引用。

```python
# Anthropic 手动标记
"content": [
  {"type":"text","text":"<2万字固定文档>","cache_control":{"type":"ephemeral"}},  # 缓存住
  {"type":"text","text":"针对上面文档回答：..."}                                   # 每次变
]
```

适用：长 system / 长文档问答 / 多轮长对话 / agent。LangChain 没统一抽象，要回到厂商特性。

---

## 十二、多模态

content 数组里除文字块外，再塞图片/音频/PDF/视频块。发图两种方式：**URL**（给链接模型自己下）或 **base64**（本地文件编码成文本塞进去）。

```python
import base64
with open("cat.jpg","rb") as f:
    b64 = base64.b64encode(f.read()).decode()
```

```python
# OpenAI：图片块叫 image_url
{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}

# Anthropic：图片块叫 image，数据在 source 里（media_type）
{"type":"image","source":{"type":"base64","media_type":"image/jpeg","data":b64}}

# Gemini：最省事，直接给字节
contents=["这张图里有什么?", types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")]
```

| 模态 | OpenAI | Anthropic | Gemini |
|---|---|---|---|
| 图片 | 支持 | 支持 | 支持 |
| PDF/文档 | 支持 | 支持（document 块） | 支持 |
| 音频输入 | 支持 | **不支持** | 支持 |
| 视频 | 有限 | 不支持 | **强（整段视频）** |

**大文件走 File API**：先 `client.files.upload(...)` 拿到引用，后续只引用、不重传（适合长视频/大 PDF）。

---

## 十三、LangChain（最新 1.0）

### 包结构

| 包 | 作用 |
|---|---|
| `langchain-core` | 地基：消息、Runnable、tool、输出解析 |
| `langchain` | 变薄：`init_chat_model`、`create_agent`（基于 LangGraph） |
| `langchain-classic` | 老 chains / 遗留挪这里 |
| `langchain-openai` / `langchain-anthropic` / `langchain-google-genai` | 各厂商集成包 |

> v1 最大新东西：**标准内容块**。消息有 `.content_blocks` 属性，把各家输出归一化成带类型的块（text/reasoning/tool_call...），**读取思考现在可跨厂商统一**。

### 统一的部分

```python
from langchain.chat_models import init_chat_model
llm = init_chat_model("gpt-5",           model_provider="openai")
llm = init_chat_model("claude-opus-4-7", model_provider="anthropic")
llm = init_chat_model("gemini-3-pro",    model_provider="google_genai")

from langchain_core.messages import SystemMessage, HumanMessage
resp = llm.invoke([SystemMessage("你是助手"), HumanMessage("你好")])
```

统一：消息类型（SystemMessage/HumanMessage/AIMessage/ToolMessage）、system 落位、invoke/stream/ainvoke/astream、工具（`@tool`+`bind_tools`，`tool_calls` 永远 dict）、读思考/文本（content_blocks）、结构化输出（with_structured_output）。

多模态统一格式（已核实 1.0）：

```python
HumanMessage(content=[
    {"type":"text","text":"这张图里有什么?"},
    {"type":"image","source_type":"base64","data":b64,"mime_type":"image/jpeg"},  # 或 source_type:"url"
])
```

### 没统一、必须透传的部分

1. **思考强度**：`ChatOpenAI(reasoning_effort=...)` / `ChatAnthropic(output_config={"effort":...})` / `ChatGoogleGenerativeAI(thinking_level=...)`——读取统一，**设置不统一**。
2. **prompt caching**：Anthropic 手打 `cache_control`、OpenAI 自动、Gemini 自己的 cache，无统一开关。
3. **extended thinking 开关**：各家 kwargs 透传。
4. **多模态边缘模态**：常见图/文统一，个别音视频支持进度不齐。
5. **max_tokens**：ChatAnthropic 需给。

**法则**：通用对话/工具/结构化/读思考 → LangChain 全包；思考强度、缓存、思考开关等"省钱调优旋钮" → 回到厂商专属参数。

---

## 十四、总速查 + 学习路径

| 关注点 | OpenAI | Anthropic | Gemini |
|---|---|---|---|
| 异步类 | `AsyncOpenAI` | `AsyncAnthropic` | `client.aio.*` |
| 流式 | `stream=True` | `messages.stream()` | `generate_content_stream` |
| max_tokens | 可选 | **必填** | 可选 |
| temperature | 0–2 | 0–1 | 0–2 |
| 思考强度 | `reasoning_effort` | `output_config.effort`(4.7) | `thinking_level`(3) |
| 思考可见 | 否 | 是 | 摘要 |
| 签名 | `encrypted_content` | thinking 块 `signature` | `thoughtSignature`(3强制) |
| 多模态最全 | | | ✔ |
| LangChain 类 | `ChatOpenAI` | `ChatAnthropic` | `ChatGoogleGenerativeAI` |

学习顺序：
1. 官方 SDK 各写「同步对话 → 流式 → 带工具多轮」，踩 OpenAI 字符串 parse、Claude 结果塞回 user、Gemini 自动函数调用。
2. 各开一次思考，看 usage 里的思考 token。
3. 手搓「带思考的工具调用多轮」，故意不回传 signature 看 Gemini 3 报 400，理解签名为何存在。
4. 上 LangChain 体会 content_blocks 统一读思考 + with_structured_output，以及"缓存/思考强度必须透传"的边界。
5. 单独学 Anthropic prompt caching（cache_control）——LangChain 盖不住又最省钱。

---

## 十五、三家调用函数完整参数手册

> 主调用函数：OpenAI `chat.completions.create` / Anthropic `messages.create` / Gemini `models.generate_content`。

### OpenAI：`client.chat.completions.create(...)`

**必填**

| 参数 | 类型 | 作用 |
|---|---|---|
| `model` | str | 用哪个模型 |
| `messages` | list | 对话消息列表（role + content） |

**长度 & 流式**

| 参数 | 类型 | 作用 |
|---|---|---|
| `max_completion_tokens` | int | 最多生成多少输出 token（含推理 token）。新名字 |
| `max_tokens` | int | 旧名，已弃用（推理模型不能用） |
| `stream` | bool | True 则 SSE 流式 |
| `stream_options` | dict | 流式附加项，如 `{"include_usage":True}` |
| `stop` | str/list | 遇到这些字符串就停，最多 4 个 |

**采样**

| 参数 | 类型 | 作用 |
|---|---|---|
| `temperature` | float | 0–2，默认 1 |
| `top_p` | float | 核采样，默认 1 |
| `n` | int | 生成几条候选，默认 1 |
| `frequency_penalty` | float | -2~2，按频率压制重复词 |
| `presence_penalty` | float | -2~2，鼓励换新词 |
| `logit_bias` | dict | 手动调某些 token 概率 |
| `seed` | int | 固定随机种子，尽量复现（不保证） |

> OpenAI **没有 top_k**。

**logprobs**

| 参数 | 类型 | 作用 |
|---|---|---|
| `logprobs` | bool | 是否返回每个输出 token 的对数概率 |
| `top_logprobs` | int | 0–20，每位置额外返回前几名候选词 |

**工具**

| 参数 | 类型 | 作用 |
|---|---|---|
| `tools` | list | 工具声明 `{"type":"function","function":{...}}` |
| `tool_choice` | str/dict | `auto`/`required`/`none`/指定工具 |
| `parallel_tool_calls` | bool | 是否允许一次返回多个工具调用，默认 True |

**输出格式 & 思考**

| 参数 | 类型 | 作用 |
|---|---|---|
| `response_format` | dict | `{"type":"json_schema"...}`（strict 强约束）/`json_object`/`text` |
| `reasoning_effort` | str | 思考强度（仅推理模型）：minimal/low/medium/high（部分有 none/xhigh） |

**运维**

| 参数 | 类型 | 作用 |
|---|---|---|
| `service_tier` | str | auto/default/flex/priority，影响价格与优先级 |
| `user` | str | 终端用户标识（新版也用 `safety_identifier`） |
| `prompt_cache_key` | str | 提示缓存命中键 |
| `store` | bool | 是否把请求存到平台（评估/蒸馏用） |
| `metadata` | dict | 给请求打自定义标签 |
| `modalities` | list | 输出模态，如 `["text","audio"]` |
| `audio` | dict | 语音输出配置 |
| `prediction` | dict | 预测输出，降延迟 |

> Responses API 参数名不同：`input` / `instructions` / `max_output_tokens` / `reasoning={"effort":...}`。

### Anthropic：`client.messages.create(...)`

**必填（max_tokens 也必填）**

| 参数 | 类型 | 作用 |
|---|---|---|
| `model` | str | 模型 |
| `messages` | list | 对话，user/assistant 严格交替 |
| `max_tokens` | int | **必填**，最多输出 token（设 0 可只预热缓存） |

**长度 & 流式**

| 参数 | 类型 | 作用 |
|---|---|---|
| `stream` | bool | 是否 SSE 流式 |
| `stop_sequences` | list | 自定义停止字符串 |

**system & 采样**

| 参数 | 类型 | 作用 |
|---|---|---|
| `system` | str/list | 顶层 system（不在 messages 里） |
| `temperature` | float | **0–1**，默认 1（范围比 OpenAI 窄） |
| `top_p` | float | 核采样 |
| `top_k` | int | 前 k 采样 |

**工具**

| 参数 | 类型 | 作用 |
|---|---|---|
| `tools` | list | 工具声明（schema 字段叫 `input_schema`） |
| `tool_choice` | dict | auto/any/指定工具名/none |

**思考 & 输出格式**

| 参数 | 类型 | 作用 |
|---|---|---|
| `thinking` | dict | Enabled（带 `budget_tokens`，旧模型）/ Disabled / Adaptive（4.7） |
| `output_config` | dict | `format`（结构化输出 schema）+ `effort`（low/medium/high/xhigh/max，默认 high） |

> Opus 4.7：`thinking` 不能再设 budget_tokens（会 400），强度走 `output_config.effort`；结构化输出走 `output_config.format`。

**运维**

| 参数 | 类型 | 作用 |
|---|---|---|
| `metadata` | dict | 只含 `user_id`（哈希），滥用检测 |
| `service_tier` | str | auto / standard_only |
| `cache_control` | dict | 提示缓存标记（ephemeral） |
| `container` | str | 代码执行容器复用 ID |
| `inference_geo` | str | 推理地理区域 |

### Gemini：`client.models.generate_content(model, contents, config=...)`

> SDK 把内容和配置分开：`contents` 单独传，其余塞进 `config=types.GenerateContentConfig(...)`。

**顶层**

| 参数 | 类型 | 作用 |
|---|---|---|
| `model` | str | 模型 |
| `contents` | list/str | 对话内容（role + parts），单轮可直接给字符串 |
| `config` | GenerateContentConfig | 下面所有配置 |

**config：system / 工具 / 安全**

| 参数 | 类型 | 作用 |
|---|---|---|
| `system_instruction` | str/Content | 系统指令 |
| `tools` | list | 工具声明（`functionDeclarations`），也可直接传 Python 函数 |
| `tool_config` | ToolConfig | 工具模式 ANY/AUTO/NONE |
| `safety_settings` | list | **安全过滤阈值（唯一可调）** |
| `cached_content` | str | 引用已建的 context cache |

**config：采样 & 长度**

| 参数 | 类型 | 作用 |
|---|---|---|
| `temperature` | float | 0–2 |
| `top_p` | float | 核采样 |
| `top_k` | int | 前 k 采样 |
| `candidate_count` | int | 生成几条候选（对应 OpenAI 的 n） |
| `max_output_tokens` | int | 最多输出 token |
| `stop_sequences` | list | 停止字符串 |
| `presence_penalty` / `frequency_penalty` | float | 出现/频率惩罚 |
| `seed` | int | 随机种子 |

**config：输出格式 & 思考**

| 参数 | 类型 | 作用 |
|---|---|---|
| `response_mime_type` | str | 如 `"application/json"` |
| `response_schema` | Schema | 约束 JSON 结构（原生结构化输出） |
| `response_modalities` | list | 输出模态 |
| `thinking_config` | ThinkingConfig | 2.5 用 `thinking_budget`+`include_thoughts`；3 用 `thinking_level` |

**运维**：`service_tier`、`store`。

### 三家参数对照（同一概念，不同名字）

| 概念 | OpenAI | Anthropic | Gemini |
|---|---|---|---|
| 最大输出 | `max_completion_tokens` | `max_tokens`(必填) | `max_output_tokens` |
| system | messages 里一条 | `system`(顶层) | `system_instruction` |
| 停止词 | `stop` | `stop_sequences` | `stop_sequences` |
| 几条候选 | `n` | 无 | `candidate_count` |
| top_k | 无 | `top_k` | `top_k` |
| 结构化输出 | `response_format` | `output_config.format` | `response_schema`+`response_mime_type` |
| 思考强度 | `reasoning_effort` | `output_config.effort`/`thinking` | `thinking_config` |
| 工具选择 | `tool_choice` | `tool_choice` | `tool_config` |
| 缓存 | 自动(`prompt_cache_key`) | `cache_control`(手动) | `cached_content` |
| 安全阈值 | 独立 moderation 接口 | 内置 | `safety_settings`(可调) |
| 滥用标识 | `user` | `metadata.user_id` | 无 |

记忆要点：
- **三家共有**：model、消息、最大输出、temperature、top_p、stop、tools、tool_choice、流式、结构化输出、思考强度。
- **仅 Anthropic/Gemini**：`top_k`。
- **仅 OpenAI**：`logprobs`、`logit_bias`（`n` 在 Gemini 叫 `candidate_count`）。
- **仅 Gemini**：`safety_settings` 可调安全阈值。
- **缓存**机制三家完全不同：OpenAI 自动、Anthropic 手动打标、Gemini 先建后引用。

---

## 相关阅读

- 工具与协议：[[资料/学习材料/Agent/MCP与Tool管理]]
- wiki 压缩版：[[Agent设计模式与MCP]]
