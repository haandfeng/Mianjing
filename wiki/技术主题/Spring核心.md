---
title: Spring核心
type: topic
updated: 2026-05-04
---

# Spring核心

> IOC = 把对象创建权交给容器；DI 是注入手段；AOP = 通过动态代理织入横切关注点；Bean 生命周期 + 作用域 + 注解一套理解清楚就能应付绝大多数 Spring 八股。

## 高频问法
- "什么是 IOC？为什么要用？" — 后端专栏 [[专栏/后端/Spring 相关]]
- "DI 三种注入方式，推荐哪个" — 后端专栏 [[专栏/后端/Spring 相关]]
- "AOP 是什么、底层原理（JDK 动态代理 vs CGLIB）" — 后端专栏 [[专栏/后端/Spring 相关]]
- "@Transactional 失效场景；同类方法内调不走代理" — 后端专栏 [[专栏/后端/Spring 相关]]
- "Bean 作用域 / 生命周期" — 后端专栏 [[专栏/后端/Spring 相关]]
- "@Autowired vs @Resource" — 后端专栏 [[专栏/后端/Spring 相关]]

## 答题骨架

### 1. IOC（控制反转）
- 对象的创建权 / 生命周期管理交给容器，业务代码只声明依赖
- 收益：
  - **解耦**：依赖接口而非具体实现，换实现不改代码（@Profile 切环境）
  - **统一加工**：容器在创建 Bean 后做 AOP 代理，@Transactional / @Async / @Cacheable 都靠这个
  - **统一生命周期管理**

### 2. DI（依赖注入）三种方式
| 方式 | 写法 | 优缺点 |
|---|---|---|
| 构造器注入（推荐） | 构造方法参数 | 依赖不可变；保证创建即可用；避免循环依赖 |
| Setter 注入 | `setXxx` + @Autowired | 可选依赖、可变；兼容旧代码 |
| 字段注入 | 字段上 @Autowired | 简单但不利于测试、不能 final |

- Spring 4.3+ 单构造器可省略 @Autowired

### 3. AOP（面向切面编程）
- 把日志、事务、权限等横切逻辑抽到切面，通过代理织入业务方法
- 核心概念：切点（Pointcut）、通知（Before / After / Around / AfterReturning / AfterThrowing）、切面（Aspect）、织入（Weaving）
- 通知顺序：`@Around` 前 → `@Before` → 目标方法 → `@AfterReturning / @AfterThrowing` → `@After` → `@Around` 后

### 4. JDK 动态代理 vs CGLIB
| | JDK 动态代理 | CGLIB |
|---|---|---|
| 基于 | 接口 | 继承 |
| 限制 | 必须实现接口 | 不能代理 final 类 / 方法 |
| 实现 | Proxy + InvocationHandler，反射调用 | ASM 生成子类 + FastClass，索引调用 |
| 创建速度 | 快（有内置缓存） | 慢（生成子类 + FastClass） |
| 调用速度 | 反射稍慢（高版本优化） | FastClass 直接调，更快 |
| 元空间风险 | 低（缓存好） | 较高（生成的类大） |

- Spring AOP 默认：实现接口用 JDK，不实现用 CGLIB
- Spring Boot 2.x+ 默认 CGLIB（统一行为，省去"注入具体类报错"的坑）

### 5. @Transactional 失效场景（高频踩坑）
- **同类方法内部调用**：`this.foo()` 走的是原对象，不经代理
  - 解法：注入自身（`@Autowired private OrderService self`）；或 `AopContext.currentProxy()`
- 方法非 public（默认要求 public）
- 异常被吞或不是 RuntimeException（默认只回滚 RuntimeException + Error，要回滚受检异常用 `rollbackFor`）
- 类没被 Spring 管理（没加 @Service）

### 6. Bean 作用域
- **Singleton**（默认）：单例，全局一份；线程不安全要小心
- **Prototype**：每次 getBean 都新建
- **Request / Session / Application / WebSocket**：仅 Web 应用

### 7. Bean 生命周期（简化版）
1. 实例化（构造器 / FactoryBean）
2. 属性注入（DI）
3. BeanNameAware / BeanFactoryAware / ApplicationContextAware 等 Aware 回调
4. BeanPostProcessor `postProcessBeforeInitialization`
5. `@PostConstruct` / InitializingBean.afterPropertiesSet / 自定义 init-method
6. BeanPostProcessor `postProcessAfterInitialization`（**AOP 代理在这里包装**）
7. 使用
8. 容器关闭时：`@PreDestroy` / DisposableBean.destroy / 自定义 destroy-method

### 8. @Autowired vs @Resource
- **@Autowired**：Spring 注解，先按类型，再按名字（@Qualifier 指定）
- **@Resource**：JSR-250，先按名字，再按类型
- 实战二选一统一即可

### 9. 工厂模式与 IOC 的关系
- 工厂模式是 IOC 的实现手段之一
- 工厂模式：业务主动调工厂取对象（拉模式）
- IOC：容器主动注入对象（推模式），解耦更彻底

## 易错点 & 追问
- "AOP 嵌套调用为什么不走代理" 是 Spring 最经典踩坑题
- @Transactional 默认只回滚 RuntimeException
- Spring 单例 Bean 默认线程不安全（成员变量共享），尽量无状态
- `BeanFactory` vs `ApplicationContext`：后者是前者超集，扩展了事件、国际化等
- AOP 切面执行顺序用 `@Order` 控制，数字越小优先级越高

## 深入阅读
- 原始专栏 [[专栏/后端/Spring 相关]]
- 原始专栏 [[专栏/后端/Spring注解详解]]
- 真题来源 [[字节/我的字节一面]]、[[小红书/小红书产品工程师一面面经]]
