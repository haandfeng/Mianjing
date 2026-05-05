

消息到 MQ 的过程中搞去，MQ 自己搞丟，MQ到消费过程中搞丢。

•生产者到 RabbitMIQ：事务机制和 Confirm 机制，注意：事务机制和 Confirm机制是互斥的，两者不能共存，会导致 RabbitMQ 报错。
•RabbitMQ 自身：持久化、集群、普通模式、镜像模式。
• RabbitMIQ 到消费者：basicAck 机制、死信队列、消息补偿机制。
## 生产者到 RabbitMIQ
事务机制和 Confirm 机制，注意：事务机制和 Confirm机制是互斥的，两者不能共存，会导致 RabbitMQ 报错。
#### **A. 事务机制（Tx）**
- 发送前 txSelect，发送后 txCommit；失败 txRollback
- 语义：**保证这一批消息“要么都发成功，要么都不发”**
- 缺点：**性能非常差**（同步阻塞、吞吐下降明显），高并发场景一般不用
#### **B. Confirm 机制（Publisher Confirm，推荐）**
- 开启 confirm 模式后，每条消息会收到 broker 的 **ack/nack**
- 生产者只有收到 ack 才认为“消息已到 broker（并按其策略持久化）”
- 失败/超时：重发（可能产生重复，所以要配合 message_id/biz_key）
- 适用：高吞吐、可靠投递的主流方案

## ﻿RabbitMQ 自身：持久化、集群、普通模式、镜像模式。

### **会怎么丢？**
- broker 重启/宕机：内存消息直接消失
- 单点节点故障：队列在那台机器上，机器挂了就不可用甚至丢数据
- 磁盘写满/内存水位触发：可能导致连接阻塞、超时，业务侧误判“丢了”
### **机制怎么做？**
#### **A. 持久化（Durable + Persistent）**
要形成“落盘链路”需要三件套：
- **Exchange durable**
- **Queue durable**
- **Message persistent（delivery_mode=2）**
> 注意：持久化解决的是“broker 掉电后消息还在”，**不等于你发送一定成功**（发送必达还得靠 Confirm）。
#### **B. 集群高可用（避免单点）**
你提到“普通模式、镜像模式”，我帮你补充它们的含义与差别：
- **普通模式（Classic / 非镜像）**
    - 元数据在集群，但队列实体通常只在某个节点上
    - 节点挂了：队列不可用（需要迁移/重建），可靠性一般
- **镜像模式（Mirrored Queue，经典 HA）**
    - 队列在多个节点做镜像复制
    - leader 挂了可切换到 mirror 节点，可靠性更高
    - 缺点：维护成本、性能/一致性开销更大（老方案）

- ﻿﻿RabbitMIQ 到消费者：basicAck 机制、死信队列、消息补偿机制。

## RabbitMQ → 消费者：防止“投递后处理失败/消费者挂了导致丢
#### **A. basicAck（手动确认，核心）**
- **autoAck=false**
- 只有当“业务处理成功（DB 提交/下游成功）”才 basicAck
- 失败则 basicNack / reject：
    - requeue=true：放回队列重投（不丢，但会重复）
    - requeue=false：进入死信/丢弃（需配合 DLX）
#### **B. 死信队列 DLQ（异常隔离 + 可追踪）**
- 配置 DLX（死信交换机）把：
    - 被 reject/nack 且 requeue=false 的
    - TTL 过期的
    - 队列满被丢弃的
        统一导入死信队列
- 作用：失败不“黑洞”，可告警、可人工处理、可补偿