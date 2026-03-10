---

excalidraw-plugin: parsed
tags: [excalidraw]

---
==⚠  Switch to EXCALIDRAW VIEW in the MORE OPTIONS menu of this document. ⚠== You can decompress Drawing data with the command palette: 'Decompress current Excalidraw file'. For more info check in plugin settings under 'Saving'



# NIO

```import java.nio.ByteBuffer;
import java.nio.channels.*;
import java.net.InetSocketAddress;

public class NIOServer {
    public static void main(String[] args) throws Exception {
        Selector selector = Selector.open();                          // 创建选择器
        ServerSocketChannel serverChannel = ServerSocketChannel.open(); 
        serverChannel.bind(new InetSocketAddress(8080));
        serverChannel.configureBlocking(false);                       // 非阻塞模式
        serverChannel.register(selector, SelectionKey.OP_ACCEPT);     // 注册感兴趣事件

        System.out.println("NIO 服务器启动，等待连接...");

        while (true) {
            selector.select();                                        // 阻塞等待就绪事件（非阻塞IO非指这里不阻塞，而是通道不阻塞）
            for (SelectionKey key : selector.selectedKeys()) {
                if (key.isAcceptable()) {
                    SocketChannel sc = serverChannel.accept();
                    sc.configureBlocking(false);
                    sc.register(selector, SelectionKey.OP_READ);
                    System.out.println("客户端连接成功");
                } else if (key.isReadable()) {
                    SocketChannel sc = (SocketChannel) key.channel();
                    ByteBuffer buffer = ByteBuffer.allocate(1024);
                    int len = sc.read(buffer);                        // 非阻塞读取
                    if (len > 0) {
                        System.out.println("收到数据: " + new String(buffer.array(), 0, len));
                    }
                }
            }
            selector.selectedKeys().clear();                          // 处理完清空
        }
    }
}



# NIO 1

```java
import java.nio.ByteBuffer;
import java.nio.channels.*;
import java.net.InetSocketAddress;

public class NIOServer {
    public static void main(String[] args) throws Exception {
        Selector selector = Selector.open();                          // 创建选择器
        ServerSocketChannel serverChannel = ServerSocketChannel.open(); 
        serverChannel.bind(new InetSocketAddress(8080));
        serverChannel.configureBlocking(false);                       // 非阻塞模式
        serverChannel.register(selector, SelectionKey.OP_ACCEPT);     // 注册感兴趣事件

        System.out.println("NIO 服务器启动，等待连接...");

        while (true) {
            selector.select();                                        // 阻塞等待就绪事件（非阻塞IO非指这里不阻塞，而是通道不阻塞）
            for (SelectionKey key : selector.selectedKeys()) {
                if (key.isAcceptable()) {
                    SocketChannel sc = serverChannel.accept();
                    sc.configureBlocking(false);
                    sc.register(selector, SelectionKey.OP_READ);
                    System.out.println("客户端连接成功");
                } else if (key.isReadable()) {
                    SocketChannel sc = (SocketChannel) key.channel();
                    ByteBuffer buffer = ByteBuffer.allocate(1024);
                    int len = sc.read(buffer);                        // 非阻塞读取
                    if (len > 0) {
                        System.out.println("收到数据: " + new String(buffer.array(), 0, len));
                    }
                }
            }
            selector.selectedKeys().clear();                          // 处理完清空
        }
    }
}
```


# Code Block

```java
import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.ByteBuffer;
import java.nio.channels.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Iterator;
import java.util.Set;

public class NioEchoServer {

    public static void main(String[] args) throws IOException {
        // 1. 创建 Selector
        Selector selector = Selector.open();

        // 2. 创建 ServerSocketChannel，配置为非阻塞，绑定端口
        ServerSocketChannel serverChannel = ServerSocketChannel.open();
        serverChannel.configureBlocking(false);
        serverChannel.bind(new InetSocketAddress(8080));

        // 3. 把“接收连接事件”注册到 Selector 上
        serverChannel.register(selector, SelectionKey.OP_ACCEPT);
        System.out.println("NIO Echo 服务器启动，监听端口 8080...");

        // 4. 主事件循环
        while (true) {
            // 阻塞等待至少一个事件就绪
            selector.select();

            // 拿到所有就绪的 key
            Set<SelectionKey> selectedKeys = selector.selectedKeys();
            Iterator<SelectionKey> iter = selectedKeys.iterator();

            while (iter.hasNext()) {
                SelectionKey key = iter.next();
                iter.remove(); // 及时移除，避免重复处理

                try {
                    // 4.1 有新的客户端连接进来
                    if (key.isAcceptable()) {
                        handleAccept(key, selector);
                    }

                    // 4.2 某个客户端有数据可读
                    if (key.isValid() && key.isReadable()) {
                        handleRead(key);
                    }

                    // 4.3 某个客户端可以写数据（发送消息）
                    if (key.isValid() && key.isWritable()) {
                        handleWrite(key);
                    }
                } catch (IOException e) {
                    // 出现异常：取消 key，关闭 channel
                    key.cancel();
                    Channel channel = key.channel();
                    if (channel != null) {
                        channel.close();
                    }
                }
            }
        }
    }

    /**
     * 处理 OP_ACCEPT：有新连接进来
     */
    private static void handleAccept(SelectionKey key, Selector selector) throws IOException {
        ServerSocketChannel serverChannel = (ServerSocketChannel) key.channel();

        // 接受连接，生成 SocketChannel
        SocketChannel clientChannel = serverChannel.accept();
        clientChannel.configureBlocking(false);

        System.out.println("客户端连接成功：" + clientChannel.getRemoteAddress());

        // 注册到 Selector，关心“读事件”，并且不带 attachment（先不用）
        clientChannel.register(selector, SelectionKey.OP_READ);
    }

    /**
     * 处理 OP_READ：有数据可读
     * 这里读取客户端数据并生成响应内容，然后切换到 OP_WRITE 来发送
     */
    private static void handleRead(SelectionKey key) throws IOException {
        SocketChannel clientChannel = (SocketChannel) key.channel();

        ByteBuffer buffer = ByteBuffer.allocate(1024);
        int len = clientChannel.read(buffer);

        if (len == -1) {
            // 客户端正常关闭连接
            System.out.println("客户端断开连接：" + clientChannel.getRemoteAddress());
            clientChannel.close();
            key.cancel();
            return;
        }

        if (len == 0) {
            // 没有读到数据，忽略（非阻塞模式下很正常）
            return;
        }

        // 把 buffer 里的数据转成字符串
        buffer.flip();
        byte[] bytes = new byte[buffer.remaining()];
        buffer.get(bytes);
        String msg = new String(bytes);

        System.out.println("收到客户端(" + clientChannel.getRemoteAddress() + ")：" + msg.trim());

        // 构造要返回给客户端的消息
        String response = "[服务器时间 " +
                LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")) +
                "] 已收到：" + msg;

        // 将响应写入 ByteBuffer
        ByteBuffer writeBuffer = ByteBuffer.wrap(response.getBytes());

        // 把要写的数据 buffer 挂在 key 上（attachment），稍后在 OP_WRITE 里用
        key.attach(writeBuffer);

        // 关键：把这个 key 的兴趣操作改为“可写”（发送消息）
        key.interestOps(SelectionKey.OP_WRITE);
    }

    /**
     * 处理 OP_WRITE：向客户端发送数据
     */
    private static void handleWrite(SelectionKey key) throws IOException {
        SocketChannel clientChannel = (SocketChannel) key.channel();

        // 拿回刚刚挂在 key 上的写缓冲区
        ByteBuffer writeBuffer = (ByteBuffer) key.attachment();
        if (writeBuffer == null) {
            // 没有要写的数据，切回读事件
            key.interestOps(SelectionKey.OP_READ);
            return;
        }

        // 尝试写出数据到客户端（可能一次写不完）
        clientChannel.write(writeBuffer);

        if (writeBuffer.hasRemaining()) {
            // 说明数据还没写完，下次 OP_WRITE 就绪时继续写
            key.attach(writeBuffer);
            key.interestOps(SelectionKey.OP_WRITE);
        } else {
            // 数据写完了，清理 attachment，切回“只关心读取”
            key.attach(null);
            key.interestOps(SelectionKey.OP_READ);
        }
    }
}
```


# java

```java
import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.ByteBuffer;
import java.nio.channels.AsynchronousServerSocketChannel;
import java.nio.channels.AsynchronousSocketChannel;
import java.nio.channels.CompletionHandler;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

public class AioEchoServer {

    public static void main(String[] args) throws Exception {
        // 1. 打开异步服务器通道并绑定端口
        AsynchronousServerSocketChannel serverChannel =
                AsynchronousServerSocketChannel.open().bind(new InetSocketAddress(8080));

        System.out.println("AIO Echo 服务器启动，监听端口 8080...");

        // 2. 开始异步接收连接
        serverChannel.accept(null, new CompletionHandler<AsynchronousSocketChannel, Object>() {

            @Override
            public void completed(AsynchronousSocketChannel clientChannel, Object attachment) {
                try {
                    System.out.println("有客户端连接：" + clientChannel.getRemoteAddress());
                } catch (IOException e) {
                    e.printStackTrace();
                }

                // ⚠️ 非常关键：再次调用 accept，准备接收下一个连接
                serverChannel.accept(null, this);

                // 为这个客户端准备读缓冲区，并发起第一次异步 read
                ByteBuffer buffer = ByteBuffer.allocate(1024);
                clientChannel.read(buffer, buffer, new CompletionHandler<Integer, ByteBuffer>() {

                    @Override
                    public void completed(Integer bytesRead, ByteBuffer buf) {
                        if (bytesRead == -1) {
                            // 客户端关闭连接
                            try {
                                System.out.println("客户端断开：" + clientChannel.getRemoteAddress());
                                clientChannel.close();
                            } catch (IOException e) {
                                e.printStackTrace();
                            }
                            return;
                        }

                        buf.flip();
                        byte[] data = new byte[buf.remaining()];
                        buf.get(data);
                        String msg = new String(data).trim();
                        try {
                            System.out.println("收到客户端(" + clientChannel.getRemoteAddress() + ")：" + msg);
                        } catch (IOException e) {
                            e.printStackTrace();
                        }

                        // 构造响应消息
                        String response = "[服务器时间 "
                                + LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"))
                                + "] 已收到：" + msg + "\n";

                        ByteBuffer writeBuffer = ByteBuffer.wrap(response.getBytes());

                        // 3. 发起异步写操作
                        clientChannel.write(writeBuffer, writeBuffer,
                                new CompletionHandler<Integer, ByteBuffer>() {
                                    @Override
                                    public void completed(Integer result, ByteBuffer wb) {
                                        // 如果没写完，继续写
                                        if (wb.hasRemaining()) {
                                            clientChannel.write(wb, wb, this);
                                        } else {
                                            // 写完后，继续等下一条消息：再发起一次 read
                                            ByteBuffer newBuf = ByteBuffer.allocate(1024);
                                            clientChannel.read(newBuf, newBuf, thisReadHandler());
                                        }
                                    }

                                    @Override
                                    public void failed(Throwable exc, ByteBuffer wb) {
                                        System.out.println("写入失败: " + exc.getMessage());
                                        try {
                                            clientChannel.close();
                                        } catch (IOException e) {
                                            e.printStackTrace();
                                        }
                                    }

                                    // 为了让 read 的回调可以复用，把它封装成一个方法返回
                                    private CompletionHandler<Integer, ByteBuffer> thisReadHandler() {
                                        return thisReadHandler; // 这里只是占位，见下方真正实现
                                    }
                                });

                        // 上面的 thisReadHandler 是占位，真正的 read 回调在下面定义:
                    }

                    // 把 read 的逻辑抽成一个成员，方便“写完之后继续读”时复用
                    private final CompletionHandler<Integer, ByteBuffer> thisReadHandler =
                            this;

                    @Override
                    public void failed(Throwable exc, ByteBuffer buf) {
                        System.out.println("读取失败: " + exc.getMessage());
                        try {
                            clientChannel.close();
                        } catch (IOException e) {
                            e.printStackTrace();
                        }
                    }
                });
            }

            @Override
            public void failed(Throwable exc, Object attachment) {
                System.out.println("接受连接失败: " + exc.getMessage());
            }
        });

        // 3. 主线程为了不退出，一般阻塞住（生产中通常是放到独立服务里一直跑）
        Thread.sleep(Long.MAX_VALUE);
    }
}
```

# Excalidraw Data

## Text Elements
NIO ^Bf2PUwSl

BIO ^8NZEXaaH

AIO ^QhazfOTz

accept() 和 read() 都阻塞 ^W2FbUr15

一连接一线程 ^qHNLNEUB

Channel 可非阻塞；select() 可阻塞等待事件 ^fbHpFQhq

少量线程 + 多路复用 ^7juDZ8aD

•        accept() 调用时，如果没有连接，不会卡死，而是直接返回 null ^aEHSjaj9

•        读写同理：没有数据时 read() 会返回 0，而不会阻塞 ^q3ee8FAr

// 4. read() 也是阻塞的：没有数据时，会一直等待 ^Jhq9dHsC

while ((len = in.read(buffer)) != -1) { ^4nJyRMvz

// 2. accept() 是阻塞的：没有客户端连接时，这里会一直卡着 ^A1QE3AYr

Socket socket = serverSocket.accept(); ^ZK7XgVAh

•        serverChannel.register(selector, SelectionKey.OP_ACCEPT); ^aDGFfCm1

把 serverChannel 注册到 selector，并且告诉 selector：我关心“接受连接”事件（即 OP_ACCEPT） ^KvMAaeZe

   Selector       
  (负责轮询哪些 Channel 有事件)   ^lvT6Rpaz

OP_ACCEPT ^OFnq5oXa

register ^ItQR86sB

ServerSocketChannel(监听端口) 
 等待客户端连接 accept()，返回SocketChannel客户端，注册到selector ^6ATh60km

当有客户端连接时生成register OP_READ ^qoY5IuLo

SocketChannel(客户端1)  用于读写数据 read/write。有数据可以读，就读 ^oSqkXNJS

SelectionKey = Channel 在 Selector 中的注册凭证

作用：
        •        代表某个通道在 Selector 上的一次注册
        •        记录通道对哪些事件感兴趣（ops）
        •        告诉你当前事件类型（read/accept/write/connect）
        •        可通过 key 拿到 channel → key.channel()

可理解为：

Selector 给每个注册的 Channel 发了一个“号牌 (SelectionKey)”，
当这个 channel 有事件发生时，Selector 把牌子放到选中集合里通知你 ^A3iH8Ky0

CompletionHandler<V, A> ^3TuisuT0

•        AIO的核心接口 ^VyNCiDLq

•        所有异步操作（accept/read/write）完成后，系统会自动调用它 ^zpTmOooo

•        内含两个回调方法： ^LrFwGOPT

completed(V result, A attachment)  // 成功时调用 ^kCiUakc2

failed(Throwable exc, A attachment) // 失败时调用 ^ZPyFG152

你无需轮询，不用while循环，不用selector —— CompletionHandler 会接管流程。 ^3n5MSTWY

accept成功 → completed(AsynchronousSocketChannel channel, attachment) ^o0MUlNMy

当有客户端连接时触发 ^fpDTuofl

read成功 → completed(Integer bytesRead, ByteBuffer buffer) ^tteFytM2

当收到数据时触发 ^FMHvYmWK

write成功 → completed(Integer bytesWritten, ByteBuffer buffer) ^eiL1jrih

写回完成时触发 ^dljHQd54

## Element Links
AIrd22oR: [[NIO#Code Block]]

rumqUUL1: [[NIO#java]]

%%
## Drawing
```compressed-json
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
```
%%