# System Design 学习资料汇总

> 整理自小红书多位博主推荐 + 补充推荐，涵盖平台、书籍、视频、博客、工具等多维度资源，并附学习路径建议。

---

## 一、在线平台 / 课程

| 资源 | 说明 | 适合阶段 |
|---|---|---|
| **[HelloInterview](https://www.hellointerview.com)** | 系统设计面试专项平台，有 Guided Practice 引导式练习和题目拆解，由 FAANG 面试官出品 | 刷题实战 |
| **[System Design Primer](https://github.com/donnemartin/system-design-primer)**（GitHub） | GitHub 上的开源仓库，教科书级别的概念入门，涵盖系统设计核心知识点 | 快速了解概念 |
| **[Educative - Grokking System Design Interview](https://www.educative.io/courses/grokking-the-system-design-interview)** | 老牌付费互动课程，很多人的入门首选 | 系统学习 |
| **[Educative - Grokking Modern System Design](https://www.educative.io/courses/grokking-modern-system-design-interview-for-engineers-managers)** | 上面那个的升级版，内容更新更全 | 系统学习 |
| **[Exponent](https://www.tryexponent.com)** | 提供 Mock Interview 视频，可以看别人怎么做系统设计面试，学习表达和思路 | 模拟面试 |
| **LeetCode Discuss** | LeetCode 论坛的 System Design 板块，有很多面经和讨论 | 面经参考 |

---

## 二、书籍

| 资源 | 说明 |
|---|---|
| **Alex Xu - System Design Interview Vol.1** | 经典系统设计面试书，覆盖常见面试题，配有清晰的架构图和讲解 |
| **Alex Xu - System Design Interview Vol.2** | 续集，题目更多更深，覆盖支付系统、搜索引擎、实时游戏排行榜等 |
| **DDIA（Designing Data-Intensive Applications）** | 经典之作，主要讲数据库、数据模型和分布式系统。内容较多，时间有限可有重点地看 |
| **Understanding Distributed Systems**（Roberto Vitillo） | 比 DDIA 更轻量，适合快速了解分布式核心概念 |
| **[Google SRE Book](https://sre.google/sre-book/table-of-contents/)**（免费在线） | Google 官方 SRE 实践，了解大规模系统的可靠性设计和运维思路 |
| **[AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)**（免费） | 云架构最佳实践，面试中很多系统设计题可以用 AWS 服务来回答 |

---

## 三、YouTube 博主 / 视频频道

| 博主 | 特点 | 推荐理由 |
|---|---|---|
| **s09g** | ex-Google Senior/TL，小红书 1.2 万粉丝 | **强烈推荐**。Google 前工程师，思路清晰，**中文讲解**。内容包括：支付系统、聊天系统、广告事件聚合系统、云盘设计、任务调度系统等 |
| **System Design Interview**（YouTube） | 也叫"毛子哥" | 口音略重但讲得很好，主要涵盖分布式设计内容 |
| **Jordan has no life** | 广度和深度都很优秀 | 内容比较新，不会 outdated |
| **Byte Byte Go** | 用简单语言快速了解 SD 概念和组件 | 对小白了解新概念十分友好 |
| **DDIA 作者（Martin Kleppmann）** | YouTube 分布式系统系列课程 | 适合作为了解分布式系统的辅助材料 |
| **Gaurav Sen** | 印度小哥，系统设计入门级讲解 | 非常清晰，适合从零理解概念，如一致性哈希、消息队列等 |
| **Tech Dummies / Narendra L** | 讲解偏实战 | 覆盖很多真实面试题目（设计 Uber、设计 WhatsApp 等） |
| **Hussein Nasser** | 深入网络层和数据库层 | 想搞懂 L4/L7 负载均衡、数据库内部原理的首选 |

---

## 四、公开课

| 资源 | 说明 |
|---|---|
| **MIT 6.824 分布式系统** | MIT 经典课程，讲 Raft、MapReduce、GFS 等，适合想打深基础的人 |

---

## 五、文章 / 博客

| 资源 | 说明 |
|---|---|
| **Company Engineering Blogs** | 阅读你要面试的公司的工程博客文章，了解其真实系统架构和技术选型 |
| **Real World Architectures** | 现实中真实系统的架构案例，了解工业界实际是怎么设计的 |

---

## 六、实用工具

| 工具 | 说明 |
|---|---|
| **[Excalidraw](https://excalidraw.com)** | 免费在线画图工具，面试中画架构图的首选，支持手绘风格 |
| **[draw.io](https://app.diagrams.net)** | 更正式的架构图工具，适合做笔记和文档 |

---

## 七、学习路径建议

根据面试时间线（短期 / 中期 / 长期），建议的学习优先级如下：

| 资源 | 短期 | 中期 | 长期 |
|---|---|---|---|
| System Design Topics（各主题摘要） | ✅ | ✅ | ✅ |
| Company Engineering Blogs | ✅ | ✅ | ✅ |
| Real World Architectures | ✅ | ✅ | ✅ |
| How to Approach a SD Question | ✅ | ✅ | ✅ |
| SD Interview Questions with Solutions | Some | Many | Most |
| OOD Questions with Solutions | Some | Many | Most |
| Additional SD Interview Questions | Some | Many | Most |

**时间线策略：**

- **短期**：Aim for **Breadth**（追求广度）
- **中期**：Aim for **Breadth + Some Depth**（广度 + 部分深度）
- **长期**：Aim for **Breadth + More Depth**（广度 + 更多深度）

> 一般来说面试官对越 Senior 的 candidate，系统设计的要求会越高。

---

## 八、从零开始的学习顺序建议

```
第一阶段：建立框架（1-2 周）
├── Byte Byte Go / Gaurav Sen 视频了解核心组件
├── System Design Primer 通读一遍
└── 掌握面试答题框架（需求 → 高层设计 → 深入设计 → 扩展讨论）

第二阶段：系统学习（2-4 周）
├── Alex Xu SDI Vol.1 + Vol.2 刷题
├── s09g / Jordan has no life 视频配合学习
├── HelloInterview / Educative Guided Practice 练习
└── 目标公司 Engineering Blog 研究

第三阶段：深入理解（4+ 周，时间充裕时）
├── DDIA 重点章节精读
├── MIT 6.824 / Martin Kleppmann 分布式课程
├── Hussein Nasser 深入网络和数据库
└── Mock Interview 对练（Exponent / 找人对练）
```

**核心建议**：System Design 面试考的不只是知识，更重要的是**沟通能力**和**权衡取舍（trade-offs）**的思维方式。多看 mock interview 视频、多跟人对练，比闷头看书效果更好。

---

## 九、快速行动指南

| 目标 | 推荐资源 |
|---|---|
| 🎯 **实战做题** | s09g + Jordan has no life + HelloInterview |
| 💡 **快速了解概念** | Byte Byte Go + Gaurav Sen + System Design Primer |
| 📚 **深入学习** | DDIA + Alex Xu SDI + MIT 6.824 |
| 🏋️ **模拟面试** | Exponent + 找人对练 |
| 🛠️ **画架构图** | Excalidraw + draw.io |

---

*整理自小红书博主：我们不生产代码、超级小龙卷、南北绿豆 等分享内容，以及社区补充推荐。*
