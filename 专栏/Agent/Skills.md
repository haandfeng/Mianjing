一个skill：
一个给AI装备的技能包，里面有提示词(skill.md)，代码脚本，资源文件
他有一个通用标准


```bash
skills/pptx/
|---SKILL.md # 核心说明书。Claude 会直接阅读这个文件，里面包含创建该类型文件的具体步骤、注意事项、推荐库和代码模板等。这是整个 skill 的入口。
|---scripts/ # 可复用的处理脚本。存放实际执行任务的 Python/Shell 脚本，SKILL.md 会指导 Claude 调用这些脚本，而不是每次都从头写代码。
|---reference/ # 参考资源。通常存放示例文件、模板、格式规范等，Claude 可以参照这些资源来理解"好的输出长什么样"。
|---asserts/ # 静态资源。字体、图片、Logo、配色方案等素材文件，在生成文档时可以直接引用，确保输出风格统一、专业。
```


Skill格式：

**头部（Front Matter）** 是 YAML 格式的元数据，包含 `name`、`description`（这段描述正是 Claude 用来判断"是否触发此 skill"的依据）和 `license`。

**正文** 就是普通的 Markdown，没有任何特殊约束，核心原则是"对 Claude 有用"