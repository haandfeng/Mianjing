
# Java 中final、finally 和 finalize 各有什么区别？

1） final 是个修饰符，用来"锁死"类、方法或变量。类被 final 修饰就不能被继承，方法被 final修饰就不能被重写，变量被 final 修饰就不能重新赋值。

2） finally 是异常处理的一部分，和 try-catch 配合使用。不管 try 块里有没有抛异常，finally 块都会执行，通常用来释放资源、关闭连接这类收尾工作。

3） finalize（） 是 Object 类里的一个方法，JVM 在回收对象之前会调用它，让对象有机会做最后的清理。但这玩意儿已经被废弃了，JDK 9开始标记为 @Deprecated，JDK 18 直接标记为 forRemoval，别用它。



# string、stringbuffer、stringbuilder



三者都用来处理字符串，核心区别在于可变性和线程安全。

String 是不可变的，底层的 char 数组被 final 修饰，一旦创建就定死在那了。每次拼接、替换都会生成新对象，原来那个不会变。

StringBuffer 和 StringBuilder 都是可变的，底层用一个可扩容的数组存字符。区别在于 StringBuffer 的方法都加了synchronized，是线程安全的；StringBuilder 没加锁，单线程下性能更好。

实际选型很简单：1）字符串基本不变，或者只是少量拼接，直接用String 2）多线程环境下要频繁修改字符串，用StringBuffer 3） 单线程下大量拼接操作，用 StringBuilder


## 为什么 String 要设计成不可变

String 不可变不是拍脑袋决定的，背后有几个重要考量：

1）字符串常量池能生效。JVM 在堆里专门开辟了一块区域存字符串常量，相同内容的字符串只存一份。如果 String可变，你改了一个引用指向的内容，其他引用也跟着变了，这就乱套了。

2）哈希值可以缓存。String的 hashCode 算一次就存起来了，后面再调直接返回。HashMap 拿 String 做 key 的时候效率很高，不用每次都重新算。

3）天然线程安全。不可变对象压根不需要同步，多个线程随便读，不会有并发问题。


# 方法重载和重写的区别

方法重载发生在同一个类中，允许有多个同名方法，只要参数列表不同就行，参数个数、类型或顺序不一样都算。主要用于在同一类中定义不同场景下的行为。

方法重写发生在继承关系中，子类重写父类的某个方法，参数列表和方法名必须完全相同，从而为该方法提供新的实现。主要用于实现运行时多态。


## 哪些方法不能被重写？

Java 里**不能被重写（override）**的方法，核心就三类（再加一个“特殊情况”）：

1) final 方法：明确禁止子类重写
- 只要父类方法是 final，子类就不能 override。
```java
class A {
  public final void f() {}
}
class B extends A {
  // 编译错误：cannot override final method
  public void f() {}
}
```



 2) static方法：只能“隐藏”（hide），不能重写
- static 属于类，不属于对象；不存在动态绑定，所以不叫 override。
- 子类写同名同参的 static 方法只是 **方法隐藏**。

```java
class A { static void f() {} }
class B extends A { static void f() {} } // 这是 hide，不是 override
```

3) private方法：对子类不可见，谈不上重写
- private 方法不会被子类继承到可访问的层面。
- 子类写一个同名方法只是新方法，不是 override。
```java
class A { private void f() {} }
class B extends A { public void f() {} } // 这是新方法
```
4) 构造方法（constructor）：不能被继承，所以不能重写
- 构造器不是普通方法，只能通过 super(...) 调用父类构造器。

```java
class A { A() {} }
class B extends A { B() { super(); } } // 不能“override A()”
```


# 接口和抽象类的区别



接口和抽象类在设计动机上有所不同。

接口的设计是自上而下的。我们知晓某一行为，于是基于这些行为约束定义了接口，一些类需要有这些行为，因此实现对应的接口。

抽象类的设计是自下而上的。我们写了很多类，发现它们之间有共性，有很多代码可以复用，因此将公共逻辑封装成一个抽象类，减少代码冗余。

所谓的自上而下指的是先约定接口，再实现。而自下而上的是先有一些类，才抽象了共同父类。可能和学校教的不太一样，但是实战中很多时候都是因为重构才有的抽象。

其他区别：

1） 方法实现：接口中的方法默认是 public 和 abstract，但在 Java8之后可以设置 default 方法或者静态方法。抽象类可以包含 abstract方法和具体方法，允许子类继承并重用抽象类中的方法实现。

2）构造函数和成员变量：接口不能包含构造函数，接口中的成员变量默认为 public static final，也就是常量。抽象类可以包含构造函数，成员变量可以有不同的访问修饰符如 private、protected、public，并且可以不是常量。

3）多继承：抽象类只能单继承，接口可以有多个实现。

```java
interface Payable {
    // 默认：public abstract
    void pay(int amount);

    // Java 8：default 实例方法（有实现）
    default void log(String msg) {
        System.out.println("[Payable] " + msg);
    }

    // Java 8：static 方法（有实现）
    static boolean isValid(int amount) {
        return amount %3E 0;
    }
}
```



```java
abstract class AbstractPayment {
    // 抽象方法：子类必须实现
    protected abstract void doPay(int amount);

    // 具体方法：可以复用通用流程（模板方法）
    public final void pay(int amount) {
        validate(amount);
        doPay(amount);
        afterPay();
    }

    protected void validate(int amount) {
        if (amount <= 0) throw new IllegalArgumentException("amount");
    }

    protected void afterPay() {}
}
```

1）如果只是定义一组行为规范，不涉及状态和实现细节，优先用接口。比如 Comparable、Serializable、Runnable这些都是典型的接口使用场景。

2） 如果有公共代码需要复用，比如模板方法模式里的骨架逻辑，用抽象类更合适。像 AbstractList、AbstractMap这些就是抽象类的经典应用。

3）如果一个类需要具备多种能力，只能用接口，因为 Java 不支持多继承。比如一个类既要能排序又要能序列化，只能同时实现 Comparable 和 Serializable 两个接口。

## 为什么 Java 不支持多重继承？

![](https://pic.code-nav.cn/mianshiya/question_picture/1843904816956411905/Ttcue9B1_oxGD9BA4EX_mianshiya.webp)
Java 不支持多继承，核心原因是菱形继承问题。Java 之父James Gosling吸取了 C++多继承带来的坑，直接在语言层面把这条路堵死了。什么是菱形继承？假设有这样一个继承结构：类A 有一个方法 doSomething（），B和C都继承了A并各自重写了这个方法，然后D同时继承B和C。问题来了：当你调用D.doSomething（）时，到底该执行B的版本还是C的版本？编译器没法替你做决定，这就产生了歧义。



接口多实现能行，关键在于 Java 8 之前接口压根没有方法体，只有方法签名。不管你实现多少个接口，最终都得在子类里自己写实现逻辑，自然不存在"该调谁"的歧义。


## 函数式接口

**函数式接口（Functional Interface）是 Java 8 引入 Lambda 表达式后常用的一个概念：**

**它指的是只包含“一个抽象方法”的接口**（Single Abstract Method, SAM）。因为抽象方法只有一个，所以这个接口就能被 **Lambda 表达式 / 方法引用**“直接实现”。

一个接口满足下面条件，就叫函数式接口：

1. **有且只有 1 个抽象方法**（必须实现的那种方法）
2. 可以有：
    - 任意多个 default 方法
    - 任意多个 static 方法
    - Object 类里已有的方法（如 toString()）不算新增抽象方法
3. 通常会用注解 @FunctionalInterface 标记（不是必须，但强烈建议，用来让编译器帮你检查

```java
@FunctionalInterface
public interface Runnable {
    void run(); // 只有一个抽象方法
}

@FunctionalInterface
public interface Comparator<T> {
    int compare(T o1, T o2);
}

```



可以用 Lambda：

```java
Runnable r = () -> System.out.println("hello");
r.run();

Comparator<Integer> c = (a, b) -> a - b;
```




## jdk8之后接口的定义发生了哪些变动？
1) 允许在接口里写 default 方法（带方法体）
2) 允许在接口里写 static 方法（带方法体）
3) 引入“函数式接口”与 Lambda 生态（JDK 8）
4) 引入“函数式接口”与 Lambda 生态（JDK 8）

