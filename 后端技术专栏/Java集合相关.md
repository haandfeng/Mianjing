


 ![](https://cdn.nlark.com/yuque/0/2025/png/35797418/1740280307408-daeefff4-a9c4-4988-8f88-e480615829f4.png)
![](https://cdn.nlark.com/yuque/0/2025/png/35797418/1740280331602-74c08ca4-9376-4db8-9712-06c635411de7.png)
# HashMap
HashMap 底层就是一个数组，结合链表和红黑树来解决冲突。

它的工作原理其实很简单，主要说这3点：

1）怎么存

存一个 Key-Value 时，先算 key 的hashCode，然后用（table.length-1）& hash 算出应该放在数组的哪个下标位置。

2）冲突了怎么办

两个不同的 Key 算出来下标一样，就叫哈希冲突。HashMap 的解决办法是用链表把它们串起来，JDK 8 做了优化，如果同一个下标下的链表超过 8个节点，就转成红黑树，查找速度从 O（n） 变成 O（logn）。

3） 扩容机制

数组长度是有限的，存多了会挤。HashMap 有个负载因子默认 0.75，数组用了 75% 就自动扩容，把数组大小翻倍，然后把所有数据重新算位置放到新数组里。这个操作叫 rehash，比较耗性能，所以初始化时最好给个预估容量。



线程不安全，所以专程Concurrent HashMap

# ConcurrentHashMap 
往 ConcurrentHashMap 里插入数据时，先通过 hash 定位到桶的位置。如果桶是空的，用CAS原子操作把新节点设进去，不需要加锁。如果桶里已经有节点了，就用 synchronized 锁住头节点，然后遍历链表或红黑树找位置插入。
![](https://pic.code-nav.cn/mianshiya/question_picture/1843904816956411905/9SwqXYTh_Z5gXAh5x4J_mianshiya.webp)






提问：ConcurrentHashMap 的 get 操作需要加锁吗？

回答：不需要。Node 的 val 和 next 都用 volatile 修饰，保证了可见性。读线程能直接看到写线程的最新修改，不需要加锁就能读到正确的值。这也是 ConcurrentHashMap 读性能极高的原因，多线程读完全不会阻塞。

提问：ConcurrentHashMap 能保证复合操作的原子性吗？比如先判断再插入？

回答：不能。单个 get、put 操作是原子的，但 if-absent-then-put 这种复合操作不是。ConcurrentHashMap 提供了putlfAbsent、computelAbsent 这些原子方法来解决这个问题。如果业务逻辑更复杂，还是得自己加锁。