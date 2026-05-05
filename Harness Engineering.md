
# OpenAI 文章
[OpenAI](https://openai.com/index/harness-engineering/)


人类与系统的交互几乎全部通过 prompt 完成：工程师描述任务，运行 agent，等它开 PR。为了把一个 PR 推向完成，我们会让 Codex 在本地自审自己的改动，发起多个 agent review（本地和云端），响应人类或 agent 的反馈，循环迭代直到所有 agent reviewer 都满意（这实际上是一个"Ralph Wiggum 循环"）。Codex 直接使用我们的标准开发工具（gh、本地脚本、仓库内置技能）来获取上下文，无需人类复制粘贴到 CLI。

人类可以 review PR，但不是必须的。随着时间推移，我们把几乎所有 review 工作都推向了 **agent 之间互相处理**。
>文章里用 "Ralph Wiggum Loop" 来形容 Codex 的自循环 review 流程——agent 不断自审、响应反馈、再自审，有点像 Ralph 那种自说自话、兜圈子的感觉，带有一点自嘲的幽默意味。


### **提升应用的可读性**

随着代码吞吐量提升，瓶颈变成了人类 QA 的上限。由于人的时间和注意力始终是固定约束，我们的方向是：==让应用 UI、日志、应用指标本身对 Codex **直接可读**，从而给 agent 增加更多能力。==

例如，我们让应用支持按 git worktree 独立启动，这样 Codex 可以为每个变更各启动一个实例。我们还把 Chrome DevTools Protocol 接入了 agent 运行时，并封装了处理 DOM 快照、截图和页面导航的技能。这让 Codex 能够**直接复现 bug、验证修复、并对 UI 行为进行推理**，无需人类介入。

![](https://images.ctfassets.net/kftzwdyauwt9/GxdrnDn8NhpkQdFj5jr14/203e8808c65c9ac73c06b86b9dbe3788/OAI_Harness_engineering_Codex_drives_the_app_with_Chrome_DevTools_MCP_to_validate_its_work_mobile-light.png?w=1920&q=70&fm=webp)

==我们对可观测性工具做了同样的事。日志、指标和链路追踪通过一个本地可观测性栈暴露给 Codex，这个栈对每个 worktree 都是临时的。==Codex 在一个完全隔离的应用实例上工作——包括它的日志和指标，任务完成后整个环境会被销毁。Agent 可以用 LogQL 查询日志，用 PromQL 查询指标。有了这些上下文，像"确保服务启动在 800ms 内完成"或"这四条核心用户路径中没有任何 span 超过两秒"这样的 prompt 就变得可操作了。

![](https://images.ctfassets.net/kftzwdyauwt9/7k7c3KoD6hMHpjOXM8fUr5/6a3abccffd63637cbd82dbb7ef359859/OAI_Harness_engineering_Giving_Codex_a_full_observability_stack_mobile-light.png?w=1920&q=70&fm=webp)

### **将仓库知识作为唯一事实来源**

上下文管理是让 agent 在大型复杂任务中有效工作的最大挑战之一。我们最早学到的教训很简单：给 Codex 一张地图，而不是一本 1000 页的操作手册。


因此，我们不再把 AGENTS.md 当作百科全书，而是把它当作**目录索引**。

仓库的知识库存放在一个结构化的 `docs/` 目录中，作为唯一事实来源。一个简短的 AGENTS.md（约 100 行）被注入上下文，主要作为地图使用，通过指针指向其他地方更深层的事实来源。

```text
AGENTS.md
ARCHITECTURE.md
docs/
├── design-docs/
│   ├── index.md
│   ├── core-beliefs.md
│   └── ...
├── exec-plans/
│   ├── active/
│   ├── completed/
│   └── tech-debt-tracker.md
├── generated/
│   └── db-schema.md
├── product-specs/
│   ├── index.md
│   ├── new-user-onboarding.md
│   └── ...
├── references/
│   ├── design-system-reference-llms.txt
│   ├── nixpacks-llms.txt
│   ├── uv-llms.txt
│   └── ...
├── DESIGN.md
├── FRONTEND.md
├── PLANS.md
├── PRODUCT_SENSE.md
├── QUALITY_SCORE.md
├── RELIABILITY.md
└── SECURITY.md
```


Design documentation is catalogued and indexed, including verification status and a set of core beliefs that define agent-first operating principles. [Architecture documentation⁠(opens in a new window)](https://matklad.github.io/2021/02/06/ARCHITECTURE.md.html) provides a top-level map of domains and package layering. A quality document grades each product domain and architectural layer, tracking gaps over time.


Plans are treated as first-class artifacts. Ephemeral lightweight plans are used for small changes, while complex work is captured in [execution plans⁠(opens in a new window)](https://cookbook.openai.com/articles/codex_exec_plans) with progress and decision logs that are checked into the repository. Active plans, completed plans, and known technical debt are all versioned and co-located, allowing agents to operate without relying on external context.


这实现了**渐进式披露**：agent 从一个小而稳定的入口开始，被告知下一步去哪里找，而不是一开始就被淹没。


一个定期运行的"Document Gardener"agent 会扫描过时或已废弃的文档，找出那些不再反映真实代码行为的内容，并自动开 PR 修复。



**agent 看不到的东西，对它来说不存在。**


**问题是什么** Agent 的上下文窗口就是它的全部世界。团队在 Slack 聊的架构决策、Google Doc 里的设计方案、工程师脑子里的隐性知识——这些对 agent 来说全是黑洞，它根本不知道有这些东西存在。

**解法是什么** 把所有知识都搬进仓库，用 Markdown、Schema、执行计划等文件的形式存起来。就像给新员工写 onboarding 文档一样，你要把产品理念、工程规范、团队决策都写清楚，agent 才能做出符合预期的决策。

**由此带来的技术取舍** 既然 agent 要能"读懂"代码，就要选它能理解的技术：

- 优先选"无聊"的、稳定的技术，因为训练数据里见过的多，agent 推理更准
- 有时候宁可让 agent 自己重新实现一个小功能，也不引入一个行为复杂、难以预测的第三方库

**本质上**，这是在说：过去工程师写代码是给人看的，现在要同时考虑给 agent 看——仓库的组织方式、文档的完整性，直接决定了 agent 能不能有效工作。

==不太懂==
**1. 约束是 agent 的加速器，不是枷锁**

人类工程师写代码时，规则太严会压制创造力，所以通常保持一定灵活性。但 agent 不一样——严格的架构约束反而让它跑得更快、更稳，因为它不需要每次都"发明"结构，只需要在已知边界内填充实现。而且规则一旦编码进 linter，就自动对所有 agent 生效，是真正的乘数。

关键区分是：**约束"什么"（强制），但不约束"怎么做"（自由）**。比如规定必须在边界处解析数据，但用 Zod 还是别的库随 agent 自己决定。

**2. 高吞吐量下，工程哲学要反过来**

传统工程规范（严格的合并门槛、测试必须全绿才能合并）是为了在"修改成本高"的前提下设计的。但 agent 的吞吐量远超人类，修正成本极低，这时候"等待"反而是最大的浪费。所以他们反过来：门槛放宽，出问题快速修，而不是提前阻塞。

**一句话总结：** 给 agent 设计的工程体系和给人设计的是相反的——越严格的结构约束越好，越少的流程阻塞越好。


**熵与垃圾回收**

完全的 agent 自治也带来了新问题。Codex 会复制仓库中已有的模式——即使是不一致或次优的模式。久而久之，这不可避免地导致漂移。

起初，我们靠人工来处理这个问题。团队过去每周五都要花一整天（占全周 20%）来清理"AI 糟粕"。不出意外，这根本无法扩展。

于是我们开始把"黄金原则"直接编码进仓库，并建立了一套定期清理流程。这些原则是有主见的、机械化的规则，让代码库对未来的 agent 运行保持可读性和一致性。例如：（1）我们优先使用共享工具包，而不是手写 helper，以便集中管理不变量；（2）我们不"无脑"探测数据——我们在边界处做校验，或依赖有类型的 SDK，这样 agent 就不会在猜测出来的数据结构上意外继续构建。按照固定节奏，我们会运行一批后台 Codex 任务，扫描偏差、更新质量评分、开出针对性的重构 PR。这些 PR 大多数不到一分钟就能 review 完，并自动合并。

这就像垃圾回收机制。技术债务就像高息贷款：持续小额还款，几乎永远优于让它滚雪球、最后痛苦地集中处理。人类的品味只需捕获一次，然后在每一行代码上持续执行。这也让我们能每天发现并修复坏的模式，而不是任由它们在代码库里扩散数天乃至数周。


# Anthropic

[Anthropic](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)


Claude 的失败主要表现为两种模式。**第一种**，agent 倾向于一次性做太多事——本质上是试图一口气完成整个应用。这往往导致模型在实现到一半时耗尽上下文，让下一个会话面对一个功能半成品且没有文档的烂摊子。agent 随后不得不凭猜测搞清楚发生了什么，并耗费大量时间重新让基础应用跑起来。即使有压缩，这个问题也会出现，因为压缩并不总能向下一个 agent 传递足够清晰的指令。

**第二种失败模式**常常出现在项目后期。当一些功能已经构建完成后，后来的 agent 实例环顾四周，看到已经有所进展，便宣布任务完成。

为此，我们把问题拆解为两部分：第一，需要搭建一个初始环境，为给定 prompt 所需的所有功能奠定基础，让 agent 能够一步一步、一个功能一个功能地推进；第二，应该引导每个 agent 在取得增量进展的同时，在会话结束时将环境保持在干净的状态。所谓"干净状态"，指的是适合合并到主分支的代码：没有重大 bug，代码整洁有文档，开发者无需先收拾无关的烂摊子就能直接开始新功能的开发。


The key insight here was finding a way for agents to quickly understand the state of work when starting with a fresh context window, which is accomplished with the claude-progress.txt file alongside the git history. Inspiration for these practices came from knowing what effective software engineers do every day.


```text
{
    "category": "functional",
    "description": "New chat button creates a fresh conversation",
    "steps": [
      "Navigate to main interface",
      "Click the 'New Chat' button",
      "Verify a new conversation is created",
      "Check that chat area shows welcome state",
      "Verify conversation appears in sidebar"
    ],
    "passes": false
  }

```


**测试**

我们观察到的最后一个主要失败模式，是 Claude 倾向于在没有做充分测试的情况下就把功能标记为完成。如果没有明确的提示，Claude 往往会做代码变更，甚至用单元测试或对开发服务器的 curl 命令进行测试，但却无法识别出该功能端到端并不能正常工作。

在构建 Web 应用的场景下，一旦明确提示 Claude 使用浏览器自动化工具、并像真实用户一样进行所有测试，它在端到端功能验证方面的表现就好多了。


**Agent 失败模式与解决方案**

| 问题                          | 初始化 Agent 的处理                             | 编码 Agent 的处理                                                                   |
| --------------------------- | ----------------------------------------- | ------------------------------------------------------------------------------ |
| Claude 过早宣布整个项目完成           | 建立功能列表文件：根据输入规格，创建一个包含端到端功能描述的结构化 JSON 文件 | 在会话开始时读取功能列表文件，每次只选一个功能开始处理                                                    |
| Claude 将环境留在有 bug 或进度未记录的状态 | 初始化 git 仓库并创建进度记录文件                       | 会话开始时读取进度记录文件和 git commit 日志，并对开发服务器运行基本测试以发现未记录的 bug；会话结束时写入 git commit 和进度更新 |
| Claude 过早将功能标记为完成           | 建立功能列表文件                                  | 自我验证所有功能，只有经过仔细测试后才将功能标记为"通过"                                                  |
| Claude 需要花时间弄清楚如何运行应用       | 编写能启动开发服务器的 `init.sh` 脚本                  | 会话开始时读取 `init.sh`                                                              |