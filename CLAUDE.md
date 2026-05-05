 # 面经项目配置

## 参考文件
- 面经格式参考本仓库中的 `/Users/ha/Documents/study/面经/快手/大数据平台方向/快手一面面经.md`
- 简历参考本仓库中的 `/Users/ha/Documents/study/面经/简历_谭演锋_四月初可到岗.pdf`

## 工作规则
1. 生成面经时，模仿快手一面面经.md的格式
2. 讨论实习内容时，参考简历
3. 面经文件直接写入本仓库对应分区
4. 把相关问题通过双链连接到 Agent技术专栏 和 后端技术专栏
5. 查看已有面经，把常问的、已回答过的问题通过双链互相连接
6. 发现冗余废话或不同文档描述同一件事时，删除或用双链连接
7. 约10轮对话 commit 一次，自行决定频率
8. 八股问题更新到对应专栏的 markdown 文档里，或新建文档存储

## 代码风格
When helping me with code-related tasks, strictly avoid over-engineering.
Do not introduce unnecessary abstractions, fallback mechanisms, excessive error handling, configuration layers, or speculative extensibility.

The code must be:
	•	Simple
	•	Minimal
	•	Direct
	•	Easy to read
	•	Strictly aligned with my stated requirements

Do not add extra features, optimizations, defensive programming patterns, or architectural generalizations unless I explicitly request them.

After writing the code, re-read it carefully and reflect:
	•	Did I introduce unnecessary complexity?
	•	Did I add fallback logic that was not requested?
	•	Did I abstract something that did not need abstraction?
	•	Did I generalize beyond the concrete requirement?

If any over-design or unnecessary complexity exists, simplify the code before presenting the final answer.

Only provide the final simplified version.
No extra commentary.
No justification unless I ask for it.