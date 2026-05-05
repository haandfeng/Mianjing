---
title: Java语法基础速查
type: topic
updated: 2026-05-04
---

# Java语法基础速查

> final / finally / finalize、String 系列、重载重写、接口抽象类、HashMap、单例、生产者消费者—— Java 入门高频面试速查。

## 高频问法
- "final / finally / finalize 区别" — 后端专栏 [[专栏/后端/Java语法基础]]
- "String / StringBuffer / StringBuilder 区别；String 为什么不可变" — 后端专栏 [[专栏/后端/Java语法基础]]
- "重载 vs 重写；哪些方法不能被重写" — 后端专栏 [[专栏/后端/Java语法基础]]
- "接口 vs 抽象类；jdk8 接口能写什么" — 后端专栏 [[专栏/后端/Java语法基础]]
- "Java 不支持多继承的原因（菱形继承）" — 后端专栏 [[专栏/后端/Java语法基础]]
- "HashMap 工作原理（存 / 冲突 / 扩容）" — 后端专栏 [[专栏/后端/Java集合相关]]
- "单例模式怎么写，为什么 DCL 要 volatile" — [[小鹅通/我的/小鹅通一面面经（带答案已OC）]]
- "生产者消费者模型实现" — 后端专栏 [[专栏/后端/java参考代码]]
- "函数式接口、Lambda" — 后端专栏 [[专栏/后端/Java语法基础]]

## 答题骨架

### 1. final / finally / finalize
- **final**：修饰类（不可继承）/ 方法（不可重写）/ 变量（不可重新赋值）
- **finally**：与 try-catch 配合，无论是否异常都会执行（除 `System.exit` / JVM 崩溃 / 守护线程退出）
- **finalize()**：Object 方法，GC 前调用，已废弃（JDK 9 @Deprecated，JDK 18 forRemoval）。用 `Cleaner` / try-with-resources 替代

### 2. String 不可变 + 三者对比
| | String | StringBuffer | StringBuilder |
|---|---|---|---|
| 可变 | ✗ | ✓ | ✓ |
| 线程安全 | 自动 | synchronized | ✗ |
| 场景 | 少量、不变 | 多线程拼接 | 单线程拼接 |

- String 不可变的好处：常量池能生效（同内容只存一份）；hashCode 缓存；天然线程安全

### 3. 重载 vs 重写
- **重载（Overload）**：同类、同名、参数列表不同（个数 / 类型 / 顺序）；**编译期**多态
- **重写（Override）**：子类重写父类方法，签名一致；**运行期**多态

不能被重写：
- `final` 方法（明确禁止）
- `static` 方法（属于类，不存在动态绑定 → 同名只是隐藏，不是 override）
- `private` 方法（子类不可见）
- 构造方法（不能继承）

### 4. 接口 vs 抽象类
| | 接口 | 抽象类 |
|---|---|---|
| 设计动机 | 自上而下定义行为契约 | 自下而上抽出共性 |
| 多继承 | 多实现 | 单继承 |
| 字段 | public static final 常量 | 任意修饰符 |
| 方法 | 默认 abstract；JDK 8 可 default / static | 抽象 + 具体方法 |
| 构造 | 不能 | 可以 |

- JDK 8 接口新增：`default` 方法 / `static` 方法 / 函数式接口（Lambda 落地）
- 函数式接口：有且仅有一个抽象方法，可加 `@FunctionalInterface` 让编译器检查

### 5. Java 为什么不支持多继承
- 菱形继承问题：B、C 都继承 A 并重写 doSomething，D 同时继承 B 和 C → D.doSomething() 走哪个？编译器无法决定
- 接口多实现没问题：JDK 8 之前接口无方法体，子类必须自己实现，无歧义；JDK 8 默认方法冲突需要子类显式 override

### 6. HashMap 工作原理
- 数组 + 链表 / 红黑树
- 存：算 hashCode → `(table.length-1) & hash` 算下标
- 冲突：链表挂；JDK 8 链长 > 8 且数组 ≥ 64 转红黑树
- 扩容：负载因子 0.75，超过则 2 倍 + rehash

### 7. 单例模式（推荐写法）
**静态内部类（线程安全 + 懒加载）**：
```java
public class Singleton {
    private Singleton() {}
    private static class Holder { static final Singleton INSTANCE = new Singleton(); }
    public static Singleton getInstance() { return Holder.INSTANCE; }
}
```
- DCL 写法记得 `volatile`，防止 new 指令重排（详见 [[wiki/技术主题/Java锁体系]]）

### 8. 生产者-消费者（Semaphore 写法）
- `Semaphore empty(N)` / `Semaphore full(0)`
- Producer：`empty.acquire()` → 入 buffer → `full.release()`
- Consumer：`full.acquire()` → 出 buffer → `empty.release()`
- 也可用 `BlockingQueue` 一行解决

### 9. 基础数据类型
- 8 种：byte(1) / short(2) / int(4) / long(8) / float(4) / double(8) / char(2) / boolean
- int 范围 `-2^31 ~ 2^31-1`，原因：补码表示，0 对应 0...0，最小负数 -2^31 没正数对应

### 10. Comparator / Comparable
- Comparable：实体内部 `compareTo`，自然顺序
- Comparator：外部独立比较器，`compare(a, b)`，灵活定制

## 易错点 & 追问
- finalize 已废弃，不要在面试里说还在用
- `String s = "a" + "b"` 编译期已优化为 `"ab"` 进常量池
- 接口的 default 方法允许实现类不重写，但出现"菱形 default" 时必须显式 override
- HashMap 不是线程安全的，多线程用 `ConcurrentHashMap`

## 深入阅读
- 原始专栏 [[专栏/后端/Java语法基础]]
- 原始专栏 [[专栏/后端/Java集合相关]]
- 原始专栏 [[专栏/后端/java参考代码]]
- [[wiki/技术主题/Java并发集合]]
- [[wiki/技术主题/Java锁体系]]
