
#  Spring IOC

IOC 即控制反转，指的是将对象的控制权 交给了Spring容器，容器负责创建和管理对象，我们只需要接受容器注入的对象。



==IOC 最核心的好处就是解耦，让代码不再绑死具体实现。==

没有IOC的时候，A依赖B，就得在A里面 new B（），A和B 的实现类紧紧耦合在一起。用了IOC之后，A只声明依赖一个接口，至于用哪个实现类，配置文件或注解里定义就行。换实现的时候，A的代码一行不改，配置里把B换成B1 就完事了。



举个实际例子：OrderService 依赖 PaymentService，代码里只写 @Autowired PaymentService paymentService，用的是接口。

- ﻿﻿开发环境用 MockPaymentService 模拟支付
- ﻿﻿生产环境换成 AlipayPaymentService 真实调用支付宝

业务代码完全不用动，@Profile 注解切一下就行。

```java
public interface PaymentService {
    void pay(Order order);
}

@Service
@Profile("dev")
public class MockPaymentService implements PaymentService {
    public void pay(Order order) {
        log.info("模拟支付成功，订单号：{}", order.getId());
    }
}

@Service
@Profile("prod")
public class AlipayPaymentService implements PaymentService {
    public void pay(Order order) {
        // 真实调用支付宝 API
    }
}

```



==另一个大好处是容器能自动"加工"对象。创建完 Bean 之后，容器会检查这个 Bean 需不需要做AOP 代理，需要的话直接包一层代理对象返回。@Transactional 事务、@Async异步、@Cacheable 缓存这些功能都是这么实现的，业务代码加个注解就有效果，不用自己写代理逻辑。==



==统一的生命周期管理，IOC容器统一管理 Bean的生命周期，开发者不用操心对象什么时候创建、什么时候销毁。==

## **依赖注入（Dependency Injection, DI）** 的意思是：

> 一个类要用到的“外部对象”（依赖），**不要在类里面自己 new**，而是**由外部把它传/塞进来**。


==依赖注入DI 是IOC的具体实现方式，通过构造器注入、Setter 注入或字段注入，把依赖对象传递进来。==

依赖注入（Dependency Injection, DI） 的常见方式：


你写了 @Service 之后，Spring 会：
1. 扫描到这个类 → **创建这个类的 Bean**
2. 发现它需要某些依赖（比如 UserRepository、PaymentService）
3. 去容器里找对应的 Bean
4. **把依赖塞进去**（通过构造器 / setter / 字段 其中一种）

  

所以你看到的三种“注入方式”，区别只是：
> Spring 把依赖“塞进去”的入口不一样：
> **构造器参数 / setter 方法 / 字段反射赋值**

1. ﻿﻿构造函数注入：通过类的构造函数来注入依赖项。
构造器注入：通过构造函数传入依赖，Spring官方首推的方式。好处是注入的依赖不可变，而且能保证对象创建出来就是完整可用的状态，不会出现“半初始化"的情况。
```java
@Service
public class OrderService {
    private final UserService userService;
    private final PaymentService paymentService;

    // Spring 4.3+ 单构造器可以省略 @Autowired
    public OrderService(UserService userService, PaymentService paymentService) {
        this.userService = userService;
        this.paymentService = paymentService;
    }
}

```
2. ﻿﻿﻿Setter 注入：通过类的 Setter 方法来注入依赖项。
Spring 直接通过反射，把容器里的 Bean 塞到这个字段里。
```java
@Service
public class UserService {

    private UserRepository userRepository;

    // 在 Spring 4.3 及以后的版本，特定情况下 @Autowired 可以省略不写
    @Autowired
    public void setUserRepository(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    //...
}
```
3. ﻿﻿﻿Field（字段）注入：直接在类的字段上使用注解（如 CAutowired 或 @Resource）来注入依项。
```java
@Service
public class UserService {

    @Autowired
    private UserRepository userRepository;

    //...
}
```


## @Autowired 和 @Resource 的区别是什么？


回答：@Autowired 是Spring的注解，默认按类型匹配，找到多个同类型 Bean 再按名称匹配，配合 @Qualifier 可以指定具体的 Bean 名称。

@Resource 是JSR-250规范的注解，默认按名称匹配，找不到再按类型匹配。实际用哪个都行，团队统一就好，@Autowired 用得更多一些因为它是 Spring原生的。



## Bean 的作用域

- ﻿﻿Singleton:Spring 中的Bean 默认都是单例的，是对单例设计模式的应用，有线程安全问题。
- ﻿﻿Prototype：每次获取都会创建一个新的 Bean 实例。没有线程安全问题。
- ﻿Request：（仅 Web 应用可用）：每一次 HTTP 请求都会产生一个新的 Bean（请求 Bean），该 Bean 仅在当前HTTP request 内有效。
- ﻿﻿Session：（仅 Web 应用可用）：每一次来自新 session 的 HTTP 请求都会产生一个新的 Bean（会话 Bean），该 Bean仅在当前 HTTP session 内有效。
- ﻿Application：（仅 Web 应用可用）：每个 Web 应用在启动时创建一个 Bean（应用Bean），该 Bean 仅在当前应用启动时间内有效。
- ﻿﻿Websocket：（仅 Web 应用可用）：每一次 WebSocket 会话产生一个新的 Bean。


## Bean 的生命周期


![](https://pic.code-nav.cn/mianshiya/question_picture/1772087337535152129/zNxXrxM1_60913d46-9305-41c6-adc6-7787e078b188_mianshiya.webp)


==TODO，暂时懒得做了 ==



提问：工厂模式和IOC 有什么关系？

回答：工厂模式是实现I0C的一种手段。IOC 容器本质上就是一个大工厂，根据配置生产各种 Bean。区别在于传统工厂模式需要业务代码主动调用工厂方法获取对象，而IOC容器是主动把对象推给你，业务代码完全被动接收。从控制权角度看，工厂模式是"我去找容器要"，IOC是"容器主动给我"，后者解耦更彻底。Spring 内部也大量使用工厂模式，比如 FactoryBean 接口就是让用户自定义复杂对象的创建逻辑。



# AOP


AOP是面向切面编程，核心思想是把跨越多个模块的通用逻辑抽取出来，通过代理机制动态织入到目标方法上，避免在业务代码里到处复制粘贴。

最典型的场景就是日志、事务、权限校验。比如你有100个 Service 方法都要记录调用日志，不可能每个方法里都写一遍 log.info（），用 AOP定义一个切面，一行配置搞定全部。

AOP 的代理原理：

1. ﻿﻿﻿调用方调用的是代理对象，不是原始对象
2. ﻿﻿﻿代理对象拦截方法调用，先执行前置通知
3. ﻿﻿﻿代理对象调用目标对象的真实方法
4. ﻿﻿﻿方法执行完成后，代理对象执行后置通知
5. ﻿﻿最终结果返回给调用方

**1）类上的三个注解分别干嘛**
 **@Aspect**
告诉 Spring：这个类是一个 **切面**（包含切点 + 通知），要参与 AOP 织入。
 **@Component**
把它注册成 Spring Bean，让 Spring 能扫描到并管理它（否则切面不会生效）。
 **@Order(1)**
当你有多个切面同时拦截同一方法时，用 @Order 控制执行顺序：
- 数字越小，优先级越高
- 对 @Around 来说：优先级高的切面“包在外层”，像洋葱一样一层层套起来

```java
@Aspect
@Component
@Order(1)
public class LoggingAspect {
	//所以它会拦截：com.example.service 这个包里所有类的所有方法。
    @Pointcut("execution(* com.example.service.*.*(..))")
    public void serviceMethods() {}

    @Around("serviceMethods()")
    public Object logAround(ProceedingJoinPoint pjp) throws Throwable {
        String methodName = pjp.getSignature().getName();
        long start = System.currentTimeMillis();
        
        try {
            Object result = pjp.proceed();
            long cost = System.currentTimeMillis() - start;
            log.info("方法 {} 执行成功，耗时 {}ms", methodName, cost);
            return result;
        } catch (Throwable e) {
            log.error("方法 {} 执行异常: {}", methodName, e.getMessage());
            throw e;
        }
    }
}

```


 SpringAOP： 是 Spring 框架中的AOP 实现，基于动态代理实现。Spring AOP 主要用于解决 Spring 容器中 Bean的横切关注点问题。由于它使用了动态代理，所以只支持方法级别的切面（即横切关注点只能织入方法的执行）。Spring AOP 的性能略逊于 AspectJ，但对于大部分应用来说，性能影响不大。

Spring AOP 默认的策略是：目标类实现了接口就用JDK 动态代理，没实现就用CGLIB。


主要出现这种问题的愿意就是一个JDK基于接口，再上下文中调用别的东西。
CGLIB基于继承，会改写函数

| **对比项**  | **JDK 动态代理** | **CGLIB 代理**   |
| -------- | ------------ | -------------- |
| 前提条件     | 目标类必须实现接口    | 不需要接口          |
| 实现方式     | 基于接口生成代理类    | 通过继承目标类生成子类    |
| 性能       | 生成代理快，调用稍慢   | 生成代理慢，调用快      |
| final 方法 | 能代理          | 无法代理，因为不能被子类重写 |


## 代理失效的常见坑

Spring AOP 有个很容易踩的坑：同类方法内部调用不走代理。

```java
@Service
public class OrderService {
    
    @Transactional
    public void createOrder() {
        // 业务逻辑...
        this.sendNotification();  // 这里的事务注解不生效！
    }
    
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void sendNotification() {
        // 发送通知...
    }
}

```



上面代码里 sendNotification 的事务注解不会生效，因为 this.sendNotification（）调用的是原始对象的方法，不是代理对象。

解决方案有3种：

1） 注入自身：@Autowired private OrderService self； 然后用 self.sendNotification（）

2） 从 ApplicationContext 获取代理对象

3） 使用 AopContext.currentProxy（）获取当前代理




@Transactional 注解底层就是用AOP 实现的

提问：AOP的通知执行顺序是什么？如果有多个切面呢？

回答：单个切面的执行顺序：@Around 前半部分-> @Before -> 目标方法 ->@After Returning / @After Throwing - >@After -> @Around 后半部分。