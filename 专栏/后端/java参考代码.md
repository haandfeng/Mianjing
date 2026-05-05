
单例模式
```java
public class Singleton {
    private Singleton() {}

    private static class Holder {
        static final Singleton INSTANCE = new Singleton();
    }

    public static Singleton getInstance() {
        return Holder.INSTANCE;
    }
}
```



生产者消费者模型
用java 实现生产者、消费者模型。 实现线程安全的Consumer、Producer类。 producer（生产）---》【队列】----》consumer（消费）

1）当缓冲区满时生产者阻塞，缓冲区空时消费者阻塞 2）实现线程安全的动态等待/唤醒机制 3）缓存冲与具体消费、生产数据的逻辑可以简化。 例如仅做数据计数。


```java
import java.util.concurrent.Semaphore;

public class ProducerConsumer {

    static final int CAPACITY = 5;
    static final Semaphore empty = new Semaphore(CAPACITY); // 空槽数
    static final Semaphore full = new Semaphore(0);          // 已用槽数
    static int count = 0;

    static class Producer implements Runnable {
        @Override
        public void run() {
            while (true) {
                try {
                    empty.acquire();
                    count++;
                    System.out.println(Thread.currentThread().getName() + " 生产 | buffer=" + count);
                    full.release();
                    Thread.sleep(200);
                } catch (InterruptedException e) { return; }
            }
        }
    }

    static class Consumer implements Runnable {
        @Override
        public void run() {
            while (true) {
                try {
                    full.acquire();
                    count--;
                    System.out.println(Thread.currentThread().getName() + " 消费 | buffer=" + count);
                    empty.release();
                    Thread.sleep(500);
                } catch (InterruptedException e) { return; }
            }
        }
    }

    public static void main(String[] args) {
        new Thread(new Producer(), "P-1").start();
        new Thread(new Producer(), "P-2").start();
        new Thread(new Consumer(), "C-1").start();
    }
}
```