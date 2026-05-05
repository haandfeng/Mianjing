---
title: DP模板
type: algo-template
updated: 2026-05-04
---

# DP 模板

## 思考框架

1. 状态定义：`dp[i]` 或 `dp[i][j]` 是什么？
2. 转移方程：从哪些子问题转移过来？
3. 边界：`dp[0]` / `dp[0][j]` / `dp[i][0]`
4. 顺序：i 从小到大 / 从大到小？
5. 空间优化：能否滚动数组？

## 1D DP 骨架

```java
int[] dp = new int[n + 1];
dp[0] = base;
for (int i = 1; i <= n; i++) {
    dp[i] = f(dp[i-1], dp[i-2], ...);
}
return dp[n];
```

## 2D DP 骨架

```java
int[][] dp = new int[m + 1][n + 1];
for (int i = 1; i <= m; i++)
    for (int j = 1; j <= n; j++)
        dp[i][j] = f(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]);
```

## 1. 零钱兑换（LC 322）

出处：[[字节-今日头条-财经业务/字节-国际广告and中国广告/10.13 字节 国际化广告 后端]]

```java
int[] dp = new int[amount + 1];
Arrays.fill(dp, amount + 1);
dp[0] = 0;
for (int i = 1; i <= amount; i++)
    for (int c : coins)
        if (i >= c) dp[i] = Math.min(dp[i], dp[i-c] + 1);
return dp[amount] > amount ? -1 : dp[amount];
```

## 2. 01 背包

出处：[[快手/支付方向/快手日常实习面经]]

```java
int[] dp = new int[W + 1];
for (int i = 0; i < n; i++)
    for (int w = W; w >= weight[i]; w--) // 倒序：每个物品只用一次
        dp[w] = Math.max(dp[w], dp[w - weight[i]] + value[i]);
```

完全背包则正序遍历 w。

## 3. 丑数 II（LC 264）

出处：[[面经较少公司/老虎国际二面面经（资讯组）]]

```java
int[] dp = new int[n];
dp[0] = 1;
int p2 = 0, p3 = 0, p5 = 0;
for (int i = 1; i < n; i++) {
    int next = Math.min(dp[p2]*2, Math.min(dp[p3]*3, dp[p5]*5));
    dp[i] = next;
    if (next == dp[p2]*2) p2++;
    if (next == dp[p3]*3) p3++;
    if (next == dp[p5]*5) p5++;
}
```

## 4. 买卖股票（LC 121 / 188）

出处：[[TT/TT SRE 牛客]]

一次：维护历史最小价格 + 最大利润。
```java
int min = Integer.MAX_VALUE, ans = 0;
for (int p : prices) { min = Math.min(min, p); ans = Math.max(ans, p - min); }
```

K 次：`dp[i][k][0/1]`，0=不持有 1=持有。
```java
dp[i][k][0] = max(dp[i-1][k][0], dp[i-1][k][1] + prices[i]);
dp[i][k][1] = max(dp[i-1][k][1], dp[i-1][k-1][0] - prices[i]);
```

## 易错点

- 01 背包内层倒序，完全背包正序
- 状态定义一定先写注释
- 边界单独写出来再进循环

> 完整真题清单见 [[算法/README]]
