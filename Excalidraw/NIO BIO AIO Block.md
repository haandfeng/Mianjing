
# NIO
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