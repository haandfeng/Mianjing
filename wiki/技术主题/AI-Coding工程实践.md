---
title: AI Coding 工程实践（日常怎么干）
type: topic
updated: 2026-08-14
note: 三篇一组 —— 日常工程看本篇，面试看 [[AI-Coding面试题]]，笔试看 [[AI-Coding笔试题]]。本篇是「明天坐下来怎么操作」，不是「面试怎么答」。
---

# AI Coding 工程实践（日常怎么干）

> **一句话：软约束是 prompt 和文档，agent 可以无视；硬约束是 CI 里会 fail build 的检查，不管代码是谁写的都拦得住。所有工程手段都在这条线上排位。**

> 📌 全篇查证于 2026-08-14，一手来源为主（Anthropic / OpenAI / Cursor / GitHub 官方文档 + Linux 内核 process 文档 + 开源项目源码）。

---

## 一、一个任务怎么走

### 四阶段（Anthropic 官方）

`Explore → Plan → Implement → Commit`

**跳过 Plan 的判据只有一句**（官方原文）：
> **「If you could describe the diff in one sentence, skip the plan.」**

**该走 Plan 的三种场景**：方案不确定 / 改动跨多文件 / **你对被改的代码不熟**。

**动作**：用 `claude --permission-mode plan` 启动而不是裸 `claude`。先只读不写，出计划，**Ctrl+G 把计划拉进编辑器自己改**，改到认可才 Shift+Tab 放它写。

> Cursor 把这件事产品化得最彻底：Plan Mode 五步，**计划落成一个可编辑的 markdown 文件**。

### 说清楚要什么（OpenAI 官方的四要素，每条是个问句）

任务是什么 / 约束是什么 / 什么算成功 / 什么明确不要做。

### 让它先写测试——但有一步不能省

Cursor 官方三步：① 按期望的输入输出对写测试 ② **在实现之前先确认这些测试是失败的** ③ 让它写代码去过测试。

> 🔑 **第②步是防作弊的关键**：不先看到红色，你分不清是实现对了还是测试根本没断言到东西。
> **动作**：让它写完测试后，**你自己（不是它）跑一遍，亲眼看到失败**，再放它写实现。

### 给它一个能自己跑的检查（最高杠杆的一招）

官方论点：**Claude 在「看起来做完了」时就停。没有可运行的检查，"looks done" 就是唯一信号，而你本人变成了验证循环里的一环。**

**四档 gating，按需升级：**

| 档 | 手段 | 成本 |
|---|---|---|
| ① | prompt 里要求它跑检查并迭代 | 0 |
| ② | `/goal` 设成会话级条件，每轮独立评估器复检 | 低 |
| ③ | **Stop hook 确定性闸门**——脚本不过就不让这轮结束（连续 block 8 次后强制放行） | 中 |
| ④ | **验证 subagent**——`so the agent doing the work isn't the one grading it` | 中 |

**今天就能加的零成本动作**：每个实现类 prompt 结尾固定加一句「**跑 `<具体命令>`，把输出贴出来，失败就修到过为止**」——**要证据不要断言**。

### 收尾前来一道对抗式 review（但要防它的副作用）

官方示例 prompt（照抄，把 PLAN.md 换成你的计划文件）：
> 「Use a subagent to review the diff against PLAN.md. Check that every requirement is implemented, the listed edge cases have tests, and nothing outside the task's scope changed. **Report gaps, not style preferences.**」

> ⚠️ **官方紧跟的警告**：被要求找 gap 的 reviewer **通常总会报一些出来，即使工作是没问题的**——因为那就是它被要求做的事。追着每条改会导致**过度设计**（多余抽象层、防御性代码、给不可能发生的情况写测试）。
> **对策**：收到 findings 先分类，**影响正确性的改，其余默认不改**。这是官方明说的，不是加戏。

---

## 二、长任务：核心不是压上下文，是把状态写进文件

### 大需求先让它反过来面试你

官方 prompt 大意：
> 「I want to build [简述]. **Interview me in detail.** Ask about technical implementation, UI/UX, edge cases, concerns, and tradeoffs. **Don't ask obvious questions, dig into the hard parts I might not have considered.** Keep interviewing until we've covered everything, then write a complete spec to SPEC.md.」

**写完 spec 要开一个全新会话去执行。** 好 spec 的特征：点名涉及的文件和接口、**写明什么是 out of scope**、结尾有一条端到端验证步骤。

> 官方判断：**「Time spent making the spec precise pays off more than time spent watching the implementation.」**

### 两个文件今天就建

| 文件 | 内容 |
|---|---|
| `PLAN.md` | 里程碑清单，**每条后面跟一条验证命令** |
| `PROGRESS.md` | 做完什么、当前卡在哪、下一步 |

然后在 AGENTS.md 里加硬规则：**每个会话开头先读这两个文件，结束前必须更新 PROGRESS.md 并 commit。**

> 🔑 **切里程碑的标准只有一条：这个里程碑结束时，有没有一条命令能证明它成了？没有就继续拆。**
> OpenAI 公开的实测量级：一个项目 ~25 小时、~1300 万 token、~3 万行代码，**靠里程碑切分不是一个大 prompt**。原文：「Less about one giant prompt and more about the agent loop.」

### 🔴 什么时候 /clear（最反直觉也最实用的一条）

官方原文：
> **「If you've corrected Claude more than twice on the same issue in one session, the context is cluttered with failed approaches. Run /clear and start fresh...」**
> 「A clean session with a better prompt **almost always outperforms** a long session with accumulated corrections.」

**贴在显示器上：同一个问题纠正到第二次还不对，不许纠正第三次——直接 /clear，把学到的写进新 prompt 重开。**

Cursor 的三个信号：换任务 / **agent 开始困惑或重复** / 完成了一个逻辑工作单元。

### 调研外包给 subagent（省上下文最有效的一招）

官方示例数字：subagent 读了 **6100 token** 的文件，**回传主会话只有 420 token**。

**句式固定成**：`use a subagent to investigate 我们的 X 是怎么处理 Y 的，有没有现成的 Z 可以复用`

> ⚠️ 官方把「**infinite exploration**」（不划范围地让它 investigate，读了几百个文件把上下文塞满）列为五大失败模式之一。
> 相关概念：**context rot** —— 上下文 token 越多，模型从中准确召回信息的能力越差。

### 上下文的确切数字（Claude Code）

启动时就已占用：system prompt ~4200 token、auto memory ~680、环境信息 ~280、MCP 工具名清单 ~120，**加上 CLAUDE.md 和 skill 清单**——你还没打第一个字就占掉一块了。单次读一个中等文件约 2400 token。

**两个动作**：① 配 statusline 把占用显示出来（`/statusline`），不然你不知道什么时候该清 ② 在 CLAUDE.md 里加一行压缩指令，例如「When compacting, always preserve the full list of modified files and any test commands」——**这是压缩后最容易丢的两样**。

### 批量任务（大迁移）：先小样本调 prompt 再放量

1. 让它把文件清单写进文件（`list all 2,000 files that need migrating and save to files.txt`）
2. 写脚本循环 `claude -p "..." --allowedTools "Edit,Bash(git commit *)"`
3. 🔑 **先在前 2–3 个文件上跑，根据问题改 prompt，再放全量**

**无人值守一定加 `--allowedTools` 白名单。** 并行用 git worktree：`claude --worktree feature-auth`。

---

## 三、什么时候不该交给 AI

**GitHub 官方清单**：① 跨仓库知识的大范围重构 ② 需要深领域知识或大量业务逻辑 ③ **生产关键或安全敏感** ④ 定义模糊、需要在不确定性中摸索 ⑤ **你自己需要通过做它来加深理解的学习型任务**

**OpenAI 官方清单**：① 需要你还没编码进去的深领域专长 ② 需要人的判断或干系人输入的首次决策 ③ 你还没摸清 workflow 就给全权限 ④ **没有清晰成功标准**

**Anthropic 的底线一句**：**「If you can't verify it, don't ship it.」**

> 🔑 **第 ⑤ 条要单独记住**——它是唯一一条跟质量无关、跟你个人有关的排除条件，也**最容易被效率冲动碾过去**。
> **判断动作：动手前问自己「三个月后线上出问题，我能不能不看 AI 解释就 debug 这段」，不能就自己写，或至少自己逐行过一遍。**

---

## 四、项目该配什么

### AGENTS.md 是事实标准，CLAUDE.md 应退化成它的软链接

2025-08 由 OpenAI/Google/Cursor/Factory/Sourcegraph 联合定形，60k+ 项目在用，20+ 工具都读。

```bash
ln -s AGENTS.md CLAUDE.md
```

顶部写一句「**本文件是 AI agent 规则的唯一事实源**」——getsentry/sentry 的做法，避免 CLAUDE.md / .cursorrules / AGENTS.md 三份规矩互相打架。**monorepo 用嵌套 AGENTS.md，就近优先。**

### 骨架直接抄 Airflow

`apache/airflow/AGENTS.md` 是目前最完整的公开范例。**最低限度先落三段：**

1. **Commands** —— 每条是能复制粘贴的完整命令
2. **Architecture Boundaries** —— 编号的硬约束（如「Scheduler 读序列化 DAG，**绝不执行用户代码**」）
3. **Boundaries** —— 两个清单：**Ask first**（大重构、引入广泛影响的新依赖、破坏性迁移）/ **Never**（提交密钥、手改生成文件、未经要求做破坏性 git 操作）

其它可参考：`openai/codex`（含「Rust 模块控制在 500 LoC 以内」这类**有界复杂度规则**）、`cloudflare/workers-sdk`（**按爆炸半径排序**，包管理器/lockfile 规则放最前）。

### 长度：40–80 行，300+ 行是异类不是模板

**逐行删除判据（官方原文）：「Would removing this cause Claude to make mistakes?」否则删掉。**

官方警告：**「Bloated CLAUDE.md files cause Claude to ignore your actual instructions!」**

**两个诊断信号：**
- **明明写了规则它还是不照做** → 文件太长，规则被淹没了
- **它问的问题文件里明明写了** → 那句话表述有歧义

| 该写 | 不该写 |
|---|---|
| 猜不到的 bash 命令 | 读代码就能知道的 |
| 与默认不同的代码风格 | 语言标准约定 |
| 测试运行方式 | 详细 API 文档（给链接） |
| 仓库礼仪（分支命名、PR 约定） | 经常变的信息 |
| 项目特有的架构决策 | 逐文件的代码库描述 |
| 环境的坑（必需的环境变量） | 「写干净代码」这类自明废话 |

**删下来的领域知识别丢**——转成 `.claude/skills/<name>/SKILL.md`，**按需加载而不是每轮都塞进上下文**。

### 🔴 最重要的反模式：写「不许做 X」基本无效

arXiv 2607.26819 分析 102 个开源社区的 455 条 AI 贡献规则，49 个仓库实测 106 个 case：

| 规则类型 | 无提示遵守率 | 给反馈后 |
|---|---|---|
| **Refuse**（禁止 AI 贡献） | **4 个模型全部 0%** | 最多 23% |
| **Handoff**（关键步骤必须交人） | **0%** | 最多 23% |
| Disclose（披露用了 AI） | 17–40% | 77–97% |
| Verify（提交前自验） | 4–92% | 90–100% |

> **论文结论：agent 会遵守「让它多干活」的指令，抵制「让它撤销自己工作」的指令。**
> **作者给维护者的建议：真想让禁令生效，控制必须放在 agent 外面——CI 卡合并、强制人审、或者 bot。**

**动作**：把 AGENTS.md 里每条「禁止 / 必须停下来问人」拉出来，逐条问**「这条有没有对应的 CI 检查或 branch protection？」没有的话它就是装饰品。**

优先配闸门的四类：**改 migrations 目录 / 改 auth 或 billing 代码 / 新增第三方依赖 / 删测试。**

> 💡 Claude Code 侧用 **hooks（确定性执行）** 而不是 CLAUDE.md 文本（**仅建议性**）——官方原文：「Unlike CLAUDE.md instructions which are advisory, **hooks are deterministic and guarantee the action happens.**」

---

## 五、CI 该加什么闸门（硬约束在这一节）

### ① 增量覆盖率——必须是「新代码」不是「总覆盖率」

```bash
pip install diff-cover
coverage xml
diff-cover coverage.xml --compare-branch=origin/main --fail-under=80
```

Java 同一条命令改成吃 `jacoco.xml`。**阈值从 80 起步，别上 100**（官方口径 80–90，100 会被边角 case 卡死）。

> 🔑 **为什么必须是新代码**：AI 大量加代码时**总覆盖率变化迟钝，看不出问题**。
> 有 SonarQube 的话直接用 Sonar way 质量门：新代码覆盖率 ≥ 80%、**新代码重复行 ≤ 3%**。
> ⚠️ diff-cover 按相对路径匹配源文件，**CI 里工作目录不对会全 0%**。

### ② 增量变异测试——抓「覆盖率高但断言全是摆设」

**变异测试** = 工具故意改坏产品代码（`>` 改 `>=`），跑测试；**测试还全绿就说明这段测试是摆设**。它抓的正是增量覆盖率抓不到的漏洞，也正是 AI 最爱写的假测试。

- **Java**：`mvn ... org.pitest:pitest-maven:scmMutationCoverage -Dinclude=ADDED,MODIFIED`（免费起步）
- **JS/TS**：StrykerJS `--incremental`

> **动作**：**先别上门禁**。只在 PR 上跑并把 survived mutant 数量贴成评论，**跑两周看基线**，稳定后再把「新增 survived mutant > 0 就 fail」设成必需检查。

### ③ 架构规则 + 棘轮（这是唯一真正的硬约束）

**ArchUnit（Java）** 把架构约束写成单元测试。关键是 **FreezingArchRule 棘轮**：首次运行把现存违规记进 store，之后**只对新增违规 fail**；修好一个自动从 store 删一个，**基线只缩不涨**。

> ⚠️ **CI 上必须把 `allowStoreUpdate` 设成 false**（本地 true、CI false），否则 agent 跑一遍就把自己制造的违规写进基线，**棘轮直接失效**。
> <!-- 这条是调研 agent 的推断，文档没明说，配之前自己验一下 -->

**JS/TS 用 dependency-cruiser**：`npx depcruise --init`，三条起步——`no-circular` / 层边界 / 测试隔离，**severity 一律 `error`**（设 `warn` 就只是打印，拦不住）。

### ④ 复杂度与重复率——先看基线别急着卡

```bash
pip install lizard && lizard src/ -C 15 -w        # CCN 默认 15
npx jscpd src --threshold 3 --reporters console   # 3% 抄 Sonar way
```

> ⚠️ **圈复杂度不要当核心指标**——它跟代码行数的 adjusted R² = **0.9251**，跟缺陷数的相关性只有 **0.06 量级**。**用它做门禁本质上是在限制函数长度。**
> **对 AI 代码真正该看的是重复率**（理由见 §七）。

### ⑤ PR 体积自动拦

`codelytv/pr-size-labeler`，设 `fail_if_xl: 'true'` 直接卡合并。参考阈值：xs 10 / s 100 / m 500 / l 1000。

**理由一句话：review 成本是超线性的，PR 一大大家就只会点 approve。** 社区收敛出的门槛是**单 PR ≤ 500 行**；DORA 2025 的能力模型里「**working in small batches**」独立成条。

---

## 六、团队规范

### AI 参与怎么标注

**Linux 内核（唯一有官方文档的格式）**：
```
Assisted-by: AGENT_NAME:MODEL_VERSION [coccinelle] [sparse]
```
硬规则两条：**AI agent 绝不能自己加 `Signed-off-by`**（DCO 只有人类有法律资格签）、**agent 不得直接把补丁发给维护者**。

**Airflow 的 `Drafted-by` 更值得抄**（针对 agent 发的**文字**而非代码）：
```
Drafted-by: <Agent Name> (no human review before posting)
Drafted-by: <Agent Name>; reviewed by @<handle> before posting
```
> 🔑 **「有没有人过目」这个区分，比「是不是 AI 写的」有用得多。**

光谱另一端：**QEMU 拒收任何含 AI 生成内容的贡献；Gentoo Council 2024 年全票禁止；curl 因 AI 漏洞报告有效率跌破 5% 直接关停 bug bounty。**

### review 分工的现实边界

**AI review 抓得住局部缺陷，抓不住架构与跨系统影响。** 所以：
- **人审保留给两类**：安全权限相关的路径、以及「**它做了我没让它做的事**」（AI 特别爱顺手加 fallback、加吞异常的 try-except、加没要求的配置层）
- **防橡皮图章**：批准人必须写明**自己验了哪一条**；高风险路径强制人审

---

## 七、该看哪些指标才知道「我们的代码在变烂」

| 指标 | 为什么 |
|---|---|
| **重复块率 / copy-paste 与 moved 之比** | GitClear 的核心发现：**AI 时代烂掉的首要形态是复制粘贴取代重构** |
| **两周内 churn** | 刚写的代码马上被改掉 = 一次没写对 |
| **变更失败率 / 交付稳定性** | DORA 2024：**AI 采用率每 +25%，交付稳定性 -7.2%** |
| 🔑 **逃逸缺陷率**（CI 全绿但线上出问题的比例） | **唯一的终极指标，前面全是它的代理** |

**DORA 2025 的官方结论（比罗列风险成熟）**：吞吐量转正了，**但稳定性仍是负相关**。机制解释是「**AI as amplifier**」——
> 「AI accelerates software development, but that acceleration can **expose weaknesses downstream**. Without robust control systems... **an increase in change volume leads to instability**.」

**翻译成人话：你原来测试、版本控制、反馈回路弱，AI 只会让你更快地把烂东西推到线上。**

---

## 八、AI 代码的错误形状跟人不一样

**核心因果**：**模型优化的目标是「输出像不像对的」，不是「对不对」**（原理见 [[幻觉与事实性评测]]）。**所以它的错误天生是「读起来很顺、命名很合理」的那一类——正好是人工 review 最容易放过的。**

| 现象 | 数字 |
|---|---|
| 🔑 **深浅缺陷倒挂** | 语法错误 **-76%**、逻辑 bug **-60%**，但**权限提升路径 +322%、架构设计缺陷 +153%** |
| 「差一点点对」是最大痛点 | Stack Overflow 2025：**66%** 说最大痛点是 "almost right, but not quite"——**比明显错的更耗时** |
| 验证缺口 | 96% 不完全信任 AI 代码，**但只有 48% 说提交前「总是」验证** |
| 安全没随能力涨 | Veracode：**45% 的生成代码含 OWASP Top 10 漏洞，而且更大更新的模型并不更安全** |

> ⭐ **深浅缺陷倒挂那行最值钱**：浅层缺陷是编译器和 linter 抓的，深层缺陷是人和架构评审抓的——**AI 恰好把工作量从机器能抓的那类，转移到了机器抓不住的那类。**

### AI 特有的四个坑

| 坑 | 表现 | 怎么防 |
|---|---|---|
| **假设理想输入** | 不写边界检查 | 让它先列 edge case 再写实现 |
| **局部视角** | 只看读到的那几个文件就改 | 先自己划范围，改完全局搜受影响点 |
| **过度设计** | 主动加抽象层、fallback、吞异常的 try-except | prompt 明确禁止；**diff 里逐条砍** |
| **大 diff 不可 review** | 一次几百上千行，能跑但结构不统一 | 强制小步；先要方案再要代码 |

**后端特别容易漏的**：幂等性缺失 → 重试重复扣款；并发竞态 → 库存超卖；分布式事务边界模糊；超时降级缺失 → 级联故障；连接池泄漏 → 服务假死。

### 一条 AI 独有、通用扫描覆盖不到的：依赖存在性

> **slopsquatting**：攻击者抢注 AI 反复幻觉出来的、实际不存在的包名，等着开发者照抄安装。

USENIX Security 2025：16 个模型、**19.7% 被引用的包根本不存在**；20 万个独特幻觉包名中 **43% 在同一提示词重跑 10 次里每次都复现**——**这个可复现性正是攻击者能提前抢注的原因**。

---

## 九、三条反直觉

**① 「多写测试」并不能防屎山。**
AI 写的测试是「**实现的镜子**」不是「规格的断言」——它看得到实现，断言会系统性耦合到实现上。**实现把 `>` 误写成 `>=`，AI 生成的测试会照着这个行为写断言，bug 被固化成契约。** 这类叫 **paper tests**：看起来在测，实际在掩盖。
更严重的是：被要求「让测试通过」时，agent 经常**直接改测试**——记录到的行为包括「加 sleep 而不是修竞态、重写测试去接受错误行为」。

**② 覆盖率和故障检出能力是脱钩的。**
ULT benchmark：LLM 生成的测试在较容易的数据集上语句覆盖 **92.18%**，**变异分数只有 49.69%**——**一半的注入缺陷抓不到**。
Thoughtworks Radar Vol.34（2026-04）把变异测试放 **Trial** 环，原文：「**high coverage percentages can mask logically hollow tests**」。

**③ 更强的模型不会自动解决这个问题。**
Veracode 最关键的一条不是「45% 有漏洞」，是**更新更大的模型并没有产出更安全的代码**——**说明这是生成机制层面的结构性问题，不是能力问题，所以工程手段不能省。**

---

## 十、引用红线（这些说法别用）

| 别说 | 为什么 |
|---|---|
| 「property-based testing **专治** AI 代码」 | ⚠️ **已收回。** 论文设定都是「让 LLM 自己用 PBT 迭代」，不等于「人用 PBT 验收 AI 代码更有效」；Thoughtworks Radar 里**没有 PBT 的 blip**（变异测试有）。正确说法：「变异测试有官方背书；**PBT 抗测试过拟合是我自己的判断**」 |
| 「METR 承认 19% 是错的」 | 原文没这意思。2026-02 换了实验设计（57 人 / 800+ 任务，-4% 与 -18%，**置信区间都跨 0**），官方自评「**unreliable signal**」，但**没有撤回 19%**。**唯一稳固的发现是：主观感受和实测差了 39 个百分点——所以别凭感觉判断 AI 有没有帮上忙，记时间戳** |
| 「Google 75% 的新代码由 AI 生成」 | 高管口径，**从未公开操作性定义**（按字符？按行？含不含补全） |
| GitClear 2026 的 -35% / -74% / +47% | 原页面 403 抓不到，**全是二手转述且和 2025 年报口径对不上**。只用 2025 版那几个 |
| 「Meta 的 rubric 是 Problem Solving / Code Quality / Verification / Communication」 | 不是官方的，是备考机构转述。带百分比权重的版本**判定为编造** |
| 「大家都用『门禁』这个说法」 | 词可以用，**别说「大家都这么讲」** |

### 调研盲区（被追到这里就直说是行业空白）

1. **没有任何厂商给出「agent 产出质量」的量化标准**——没人写 agent PR 的合理合并率、逃逸缺陷率的合理区间
2. 🔑 **「AI 写代码 + AI 写测试」vs「AI 写代码 + 人写测试」，逃逸缺陷率差多少——零数据**
3. **「长期怎么度量」是空白**——各家都只讲单次任务怎么验证

---

## 深入阅读

- 姊妹篇：[[AI-Coding面试题]]（现场怎么走）· [[AI-Coding笔试题]]（投递前看）
- 相邻主题：[[幻觉与事实性评测]]（为什么它的错误长这样）· [[测试设计方法论]]（用例怎么推导）· [[Agent上下文压缩链路]] · [[Agent设计模式与MCP]]
- 一手素材：[[资料/面经/其他/PingCAP/面试问题总结]] · [[项目追问/字节答疑Bot]]（harness 视角 + 评测飞轮）
- 厂商一手（**用前重核，这块变化快**）：[Claude Code best practices](https://code.claude.com/docs/en/best-practices) · [OpenAI Codex best practices](https://learn.chatgpt.com/guides/best-practices) · [Cursor agent best practices](https://cursor.com/blog/agent-best-practices) · [GitHub Copilot agent best practices](https://docs.github.com/copilot/how-tos/agents/copilot-coding-agent/best-practices-for-using-copilot-to-work-on-tasks) · [apache/airflow AGENTS.md](https://github.com/apache/airflow/blob/main/AGENTS.md)
