# Spring、SpringMVC、SpringBoot 注解详解

## 目录
1. [Spring 核心注解](#spring-核心注解)
2. [SpringMVC 注解](#springmvc-注解)
3. [SpringBoot 注解](#springboot-注解)
4. [注解使用示例](#注解使用示例)

---

## Spring 核心注解

### 1. 组件注册注解

#### @Component
**作用**：通用的组件注解，标识一个类为Spring管理的Bean

**使用场景**：普通组件类

**代码示例**：
```java
@Component
public class UserService {
    public void saveUser() {
        System.out.println("保存用户");
    }
}
```

**等价于**：
```xml
<bean id="userService" class="com.example.UserService"/>
```

#### @Controller
**作用**：标识一个类为控制器组件，通常用于MVC架构中的Controller层

**使用场景**：处理HTTP请求的控制器

**代码示例**：
```java
@Controller
@RequestMapping("/user")
public class UserController {
    @Autowired
    private UserService userService;
    
    @RequestMapping("/list")
    public String list() {
        return "user/list";
    }
}
```

#### @Service
**作用**：标识一个类为服务层组件，用于业务逻辑处理

**使用场景**：业务逻辑层

**代码示例**：
```java
@Service
public class UserService {
    @Autowired
    private UserDao userDao;
    
    public User findById(Long id) {
        return userDao.findById(id);
    }
}
```

#### @Repository
**作用**：标识一个类为数据访问层组件，用于数据库操作

**使用场景**：DAO层、数据访问层

**代码示例**：
```java
@Repository
public class UserDao {
    @Autowired
    private JdbcTemplate jdbcTemplate;
    
    public User findById(Long id) {
        String sql = "SELECT * FROM user WHERE id = ?";
        return jdbcTemplate.queryForObject(sql, new UserRowMapper(), id);
    }
}
```

**注意**：@Controller、@Service、@Repository 都是 @Component 的特化版本，功能相同，但语义更清晰。

---

### 2. 依赖注入注解

#### @Autowired
**作用**：自动装配，根据类型（byType）进行依赖注入

**使用位置**：字段、构造方法、setter方法

**代码示例**：

**方式1：字段注入（不推荐）**
```java
@Service
public class UserService {
    @Autowired
    private UserDao userDao;  // 字段注入
}
```

**方式2：构造方法注入（推荐）**
```java
@Service
public class UserService {
    private final UserDao userDao;
    
    @Autowired  // Spring 4.3+ 可以省略
    public UserService(UserDao userDao) {
        this.userDao = userDao;
    }
}
```

**方式3：Setter方法注入**
```java
@Service
public class UserService {
    private UserDao userDao;
    
    @Autowired
    public void setUserDao(UserDao userDao) {
        this.userDao = userDao;
    }
}
```

**注入规则**：
- 如果只有一个匹配的Bean，直接注入
- 如果有多个匹配的Bean，按字段名匹配
- 如果找不到匹配的Bean，抛出异常（可通过 `required=false` 避免）

#### @Qualifier
**作用**：配合 @Autowired 使用，根据名称（byName）进行依赖注入

**使用场景**：当有多个相同类型的Bean时，指定注入哪一个

**代码示例**：
```java
// 定义多个相同类型的Bean
@Repository("mysqlUserDao")
public class MysqlUserDao implements UserDao {
    // ...
}

@Repository("oracleUserDao")
public class OracleUserDao implements UserDao {
    // ...
}

// 使用@Qualifier指定注入哪个
@Service
public class UserService {
    @Autowired
    @Qualifier("mysqlUserDao")  // 指定注入mysqlUserDao
    private UserDao userDao;
}
```

#### @Resource
**作用**：JSR-250规范注解，根据名称（byName）进行依赖注入

**与@Autowired的区别**：
- @Autowired：先按类型，再按名称
- @Resource：先按名称，再按类型

**代码示例**：
```java
@Service
public class UserService {
    @Resource(name = "mysqlUserDao")  // 按名称注入
    private UserDao userDao;
}
```

#### @Value
**作用**：注入普通值（基本类型、String、配置文件中的值）

**代码示例**：

**注入普通值**：
```java
@Component
public class AppConfig {
    @Value("张三")
    private String name;
    
    @Value("25")
    private Integer age;
}
```

**注入配置文件中的值**：
```java
// application.yml
app:
  name: MyApp
  version: 1.0.0

// Java代码
@Component
public class AppConfig {
    @Value("${app.name}")
    private String appName;
    
    @Value("${app.version}")
    private String version;
    
    @Value("${server.port:8080}")  // 默认值8080
    private Integer port;
}
```

**注入SpEL表达式**：
```java
@Component
public class AppConfig {
    @Value("#{systemProperties['java.version']}")
    private String javaVersion;
    
    @Value("#{T(java.lang.Math).random() * 100}")
    private Double randomValue;
}
```

---

### 3. 作用域注解

#### @Scope
**作用**：指定Bean的作用域

**作用域类型**：
- **singleton**（默认）：单例，整个容器中只有一个实例
- **prototype**：多例，每次获取都创建新实例
- **request**：每个HTTP请求创建一个实例（Web环境）
- **session**：每个HTTP会话创建一个实例（Web环境）
- **application**：每个ServletContext创建一个实例（Web环境）

**代码示例**：
```java
@Component
@Scope("singleton")  // 单例（默认）
public class SingletonService {
    // ...
}

@Component
@Scope("prototype")  // 多例
public class PrototypeService {
    // ...
}

@Component
@Scope("request")  // 每个请求一个实例
public class RequestService {
    // ...
}
```

**实际应用**：
```java
@Controller
public class UserController {
    @Autowired
    private SingletonService singletonService;  // 同一个实例
    
    @Autowired
    private PrototypeService prototypeService;  // 每次都是新实例
}
```

---

### 4. 配置相关注解

#### @Configuration
**作用**：标识一个类为配置类，替代XML配置文件

**代码示例**：
```java
@Configuration
public class AppConfig {
    @Bean
    public UserService userService() {
        return new UserService();
    }
    
    @Bean
    public DataSource dataSource() {
        HikariDataSource dataSource = new HikariDataSource();
        dataSource.setJdbcUrl("jdbc:mysql://localhost:3306/test");
        dataSource.setUsername("root");
        dataSource.setPassword("password");
        return dataSource;
    }
}
```

#### @Bean
**作用**：在配置类中定义Bean，方法的返回值会被注册为Spring容器中的Bean

**代码示例**：
```java
@Configuration
public class DataSourceConfig {
    @Bean
    public DataSource dataSource() {
        return new HikariDataSource();
    }
    
    @Bean(name = "myDataSource")  // 指定Bean名称
    public DataSource customDataSource() {
        return new HikariDataSource();
    }
    
    @Bean
    @Primary  // 当有多个相同类型的Bean时，优先使用这个
    public DataSource primaryDataSource() {
        return new HikariDataSource();
    }
}
```

#### @ComponentScan
**作用**：指定Spring扫描哪些包，查找被@Component等注解标记的类

**代码示例**：
```java
@Configuration
@ComponentScan(basePackages = "com.example")  // 扫描com.example包及其子包
public class AppConfig {
    // ...
}

// 或者使用basePackageClasses
@Configuration
@ComponentScan(basePackageClasses = {UserService.class, OrderService.class})
public class AppConfig {
    // ...
}

// 排除某些组件
@Configuration
@ComponentScan(
    basePackages = "com.example",
    excludeFilters = @ComponentScan.Filter(type = FilterType.REGEX, pattern = ".*Test.*")
)
public class AppConfig {
    // ...
}
```

#### @Import
**作用**：导入其他配置类

**代码示例**：
```java
@Configuration
public class DatabaseConfig {
    @Bean
    public DataSource dataSource() {
        return new HikariDataSource();
    }
}

@Configuration
public class CacheConfig {
    @Bean
    public RedisTemplate<String, Object> redisTemplate() {
        return new RedisTemplate<>();
    }
}

// 主配置类
@Configuration
@Import({DatabaseConfig.class, CacheConfig.class})  // 导入其他配置类
public class AppConfig {
    // ...
}
```

---

### 5. AOP相关注解

#### @Aspect
**作用**：标识一个类为切面类

**代码示例**：
```java
@Aspect
@Component
public class LoggingAspect {
    // 切面逻辑
}
```

#### @Before
**作用**：前置通知，在目标方法执行之前执行

**代码示例**：
```java
@Aspect
@Component
public class LoggingAspect {
    @Before("execution(* com.example.service.*.*(..))")
    public void before(JoinPoint joinPoint) {
        System.out.println("方法执行前：" + joinPoint.getSignature().getName());
    }
}
```

#### @After
**作用**：后置通知，在目标方法执行之后执行（无论是否抛出异常）

**代码示例**：
```java
@Aspect
@Component
public class LoggingAspect {
    @After("execution(* com.example.service.*.*(..))")
    public void after(JoinPoint joinPoint) {
        System.out.println("方法执行后：" + joinPoint.getSignature().getName());
    }
}
```

#### @AfterReturning
**作用**：返回通知，在目标方法正常返回后执行

**代码示例**：
```java
@Aspect
@Component
public class LoggingAspect {
    @AfterReturning(pointcut = "execution(* com.example.service.*.*(..))", returning = "result")
    public void afterReturning(JoinPoint joinPoint, Object result) {
        System.out.println("方法返回：" + result);
    }
}
```

#### @AfterThrowing
**作用**：异常通知，在目标方法抛出异常后执行

**代码示例**：
```java
@Aspect
@Component
public class LoggingAspect {
    @AfterThrowing(pointcut = "execution(* com.example.service.*.*(..))", throwing = "ex")
    public void afterThrowing(JoinPoint joinPoint, Exception ex) {
        System.out.println("方法抛出异常：" + ex.getMessage());
    }
}
```

#### @Around
**作用**：环绕通知，可以控制目标方法的执行

**代码示例**：
```java
@Aspect
@Component
public class LoggingAspect {
    @Around("execution(* com.example.service.*.*(..))")
    public Object around(ProceedingJoinPoint joinPoint) throws Throwable {
        System.out.println("方法执行前");
        long start = System.currentTimeMillis();
        
        Object result = joinPoint.proceed();  // 执行目标方法
        
        long end = System.currentTimeMillis();
        System.out.println("方法执行后，耗时：" + (end - start) + "ms");
        
        return result;
    }
}
```

#### @Pointcut
**作用**：定义切点表达式，可以在多个通知中复用

**代码示例**：
```java
@Aspect
@Component
public class LoggingAspect {
    // 定义切点
    @Pointcut("execution(* com.example.service.*.*(..))")
    public void servicePointcut() {}
    
    // 使用切点
    @Before("servicePointcut()")
    public void before(JoinPoint joinPoint) {
        System.out.println("方法执行前");
    }
    
    @After("servicePointcut()")
    public void after(JoinPoint joinPoint) {
        System.out.println("方法执行后");
    }
}
```

---

## SpringMVC 注解

### 1. 请求映射注解

#### @RequestMapping
**作用**：映射HTTP请求到处理方法

**属性**：
- `value/path`：请求路径
- `method`：HTTP方法（GET、POST等）
- `params`：请求参数条件
- `headers`：请求头条件
- `consumes`：请求内容类型
- `produces`：响应内容类型

**代码示例**：
```java
@Controller
@RequestMapping("/user")
public class UserController {
    // 映射到 /user/list
    @RequestMapping("/list")
    public String list() {
        return "user/list";
    }
    
    // 只接受GET请求
    @RequestMapping(value = "/detail", method = RequestMethod.GET)
    public String detail() {
        return "user/detail";
    }
    
    // 只接受POST请求
    @RequestMapping(value = "/save", method = RequestMethod.POST)
    public String save() {
        return "success";
    }
    
    // 指定请求参数
    @RequestMapping(value = "/search", params = "keyword")
    public String search() {
        return "user/search";
    }
    
    // 指定请求头
    @RequestMapping(value = "/api", headers = "Content-Type=application/json")
    public String api() {
        return "api";
    }
}
```

#### @GetMapping
**作用**：@RequestMapping(method = RequestMethod.GET) 的简写

**代码示例**：
```java
@Controller
public class UserController {
    @GetMapping("/user/list")
    public String list() {
        return "user/list";
    }
}
```

#### @PostMapping
**作用**：@RequestMapping(method = RequestMethod.POST) 的简写

**代码示例**：
```java
@Controller
public class UserController {
    @PostMapping("/user/save")
    public String save() {
        return "success";
    }
}
```

#### @PutMapping
**作用**：@RequestMapping(method = RequestMethod.PUT) 的简写

**代码示例**：
```java
@RestController
public class UserController {
    @PutMapping("/user/{id}")
    public User update(@PathVariable Long id, @RequestBody User user) {
        // 更新用户
        return user;
    }
}
```

#### @DeleteMapping
**作用**：@RequestMapping(method = RequestMethod.DELETE) 的简写

**代码示例**：
```java
@RestController
public class UserController {
    @DeleteMapping("/user/{id}")
    public void delete(@PathVariable Long id) {
        // 删除用户
    }
}
```

---

### 2. 请求参数注解

#### @RequestParam
**作用**：获取请求参数

**代码示例**：
```java
@Controller
public class UserController {
    // 获取单个参数
    @GetMapping("/user/detail")
    public String detail(@RequestParam Long id) {
        return "user/detail";
    }
    
    // 指定参数名
    @GetMapping("/user/search")
    public String search(@RequestParam("keyword") String key) {
        return "user/search";
    }
    
    // 设置默认值
    @GetMapping("/user/list")
    public String list(@RequestParam(defaultValue = "1") Integer page) {
        return "user/list";
    }
    
    // 参数可选
    @GetMapping("/user/filter")
    public String filter(@RequestParam(required = false) String name) {
        return "user/list";
    }
}
```

#### @PathVariable
**作用**：获取路径变量

**代码示例**：
```java
@RestController
@RequestMapping("/user")
public class UserController {
    // 获取路径变量
    @GetMapping("/{id}")
    public User getById(@PathVariable Long id) {
        return userService.findById(id);
    }
    
    // 指定变量名
    @GetMapping("/{userId}/orders/{orderId}")
    public Order getOrder(
        @PathVariable("userId") Long uid,
        @PathVariable("orderId") Long oid
    ) {
        return orderService.findById(oid);
    }
}
```

#### @RequestBody
**作用**：将请求体内容转换为Java对象（通常用于接收JSON）

**代码示例**：
```java
@RestController
@RequestMapping("/user")
public class UserController {
    @PostMapping
    public User save(@RequestBody User user) {
        // 接收JSON格式的用户数据
        // {"name":"张三","age":25}
        return userService.save(user);
    }
}
```

#### @RequestHeader
**作用**：获取请求头信息

**代码示例**：
```java
@RestController
public class UserController {
    @GetMapping("/user/info")
    public String info(@RequestHeader("User-Agent") String userAgent) {
        return "User-Agent: " + userAgent;
    }
    
    // 获取所有请求头
    @GetMapping("/user/headers")
    public Map<String, String> headers(@RequestHeader Map<String, String> headers) {
        return headers;
    }
}
```

#### @CookieValue
**作用**：获取Cookie值

**代码示例**：
```java
@RestController
public class UserController {
    @GetMapping("/user/profile")
    public String profile(@CookieValue("sessionId") String sessionId) {
        return "Session ID: " + sessionId;
    }
}
```

---

### 3. 响应相关注解

#### @ResponseBody
**作用**：将方法返回值直接写入HTTP响应体（不经过视图解析器）

**代码示例**：
```java
@Controller
public class UserController {
    @GetMapping("/user/json")
    @ResponseBody
    public User getUser() {
        return new User("张三", 25);
    }
}
```

#### @RestController
**作用**：@Controller + @ResponseBody 的组合注解

**代码示例**：
```java
@RestController  // 等价于 @Controller + @ResponseBody
@RequestMapping("/user")
public class UserController {
    @GetMapping("/{id}")
    public User getById(@PathVariable Long id) {
        return userService.findById(id);
    }
}
```

---

### 4. 异常处理注解

#### @ControllerAdvice
**作用**：全局异常处理，可以处理所有Controller抛出的异常

**代码示例**：
```java
@ControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(Exception.class)
    @ResponseBody
    public Result handleException(Exception e) {
        return Result.error(e.getMessage());
    }
    
    @ExceptionHandler(BusinessException.class)
    @ResponseBody
    public Result handleBusinessException(BusinessException e) {
        return Result.error(e.getCode(), e.getMessage());
    }
}
```

#### @ExceptionHandler
**作用**：处理特定类型的异常

**代码示例**：
```java
@Controller
public class UserController {
    @GetMapping("/user/{id}")
    public User getById(@PathVariable Long id) {
        if (id == null) {
            throw new IllegalArgumentException("用户ID不能为空");
        }
        return userService.findById(id);
    }
}

@ControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(IllegalArgumentException.class)
    @ResponseBody
    public Result handleIllegalArgument(IllegalArgumentException e) {
        return Result.error(400, e.getMessage());
    }
}
```

---

## SpringBoot 注解

### 1. 启动相关注解

#### @SpringBootApplication
**作用**：SpringBoot应用的主注解，包含三个注解：
- @SpringBootConfiguration：标识为配置类
- @EnableAutoConfiguration：开启自动配置
- @ComponentScan：组件扫描

**代码示例**：
```java
@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
```

**等价于**：
```java
@SpringBootConfiguration
@EnableAutoConfiguration
@ComponentScan(basePackages = "com.example")
public class Application {
    // ...
}
```

#### @EnableAutoConfiguration
**作用**：开启SpringBoot的自动配置功能

**代码示例**：
```java
@Configuration
@EnableAutoConfiguration
public class AppConfig {
    // SpringBoot会自动配置DataSource、Redis等
}
```

---

### 2. 配置相关注解

#### @ConfigurationProperties
**作用**：将配置文件中的属性绑定到Java对象

**代码示例**：
```yaml
# application.yml
app:
  name: MyApp
  version: 1.0.0
  database:
    url: jdbc:mysql://localhost:3306/test
    username: root
    password: password
```

```java
@Component
@ConfigurationProperties(prefix = "app")
public class AppProperties {
    private String name;
    private String version;
    private Database database;
    
    // getter和setter
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    
    // 内部类
    public static class Database {
        private String url;
        private String username;
        private String password;
        
        // getter和setter
    }
}
```

#### @ConditionalOnProperty
**作用**：根据配置属性决定是否创建Bean

**代码示例**：
```java
@Configuration
public class CacheConfig {
    @Bean
    @ConditionalOnProperty(name = "cache.type", havingValue = "redis")
    public RedisTemplate<String, Object> redisTemplate() {
        return new RedisTemplate<>();
    }
    
    @Bean
    @ConditionalOnProperty(name = "cache.type", havingValue = "local")
    public LocalCache localCache() {
        return new LocalCache();
    }
}
```

---

### 3. 测试相关注解

#### @SpringBootTest
**作用**：SpringBoot测试注解，加载完整的应用上下文

**代码示例**：
```java
@SpringBootTest
class UserServiceTest {
    @Autowired
    private UserService userService;
    
    @Test
    void testFindById() {
        User user = userService.findById(1L);
        assertNotNull(user);
    }
}
```

---

## 注解使用示例

### 完整示例：用户管理模块

```java
// 1. 实体类
public class User {
    private Long id;
    private String name;
    private Integer age;
    // getter和setter
}

// 2. DAO层
@Repository
public class UserDao {
    @Autowired
    private JdbcTemplate jdbcTemplate;
    
    public User findById(Long id) {
        String sql = "SELECT * FROM user WHERE id = ?";
        return jdbcTemplate.queryForObject(sql, new UserRowMapper(), id);
    }
}

// 3. Service层
@Service
public class UserService {
    @Autowired
    private UserDao userDao;
    
    public User findById(Long id) {
        return userDao.findById(id);
    }
    
    @Transactional
    public User save(User user) {
        // 保存用户
        return user;
    }
}

// 4. Controller层
@RestController
@RequestMapping("/api/user")
public class UserController {
    @Autowired
    private UserService userService;
    
    @GetMapping("/{id}")
    public Result<User> getById(@PathVariable Long id) {
        User user = userService.findById(id);
        return Result.success(user);
    }
    
    @PostMapping
    public Result<User> save(@RequestBody User user) {
        User saved = userService.save(user);
        return Result.success(saved);
    }
}

// 5. 全局异常处理
@ControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(Exception.class)
    @ResponseBody
    public Result handleException(Exception e) {
        return Result.error(e.getMessage());
    }
}

// 6. 配置类
@Configuration
@EnableTransactionManagement
public class AppConfig {
    @Bean
    public DataSource dataSource() {
        return new HikariDataSource();
    }
}
```

---

## 注解总结表

### Spring 核心注解

| 注解 | 作用 | 使用场景 |
|------|------|---------|
| @Component | 通用组件注解 | 普通组件类 |
| @Controller | 控制器组件 | MVC控制器 |
| @Service | 服务层组件 | 业务逻辑层 |
| @Repository | 数据访问层组件 | DAO层 |
| @Autowired | 自动装配 | 依赖注入 |
| @Qualifier | 按名称注入 | 多个同类型Bean |
| @Value | 注入值 | 配置值、普通值 |
| @Scope | 作用域 | 单例、多例等 |
| @Configuration | 配置类 | 替代XML配置 |
| @Bean | 定义Bean | 配置类中 |
| @ComponentScan | 组件扫描 | 指定扫描包 |
| @Aspect | 切面 | AOP |
| @Before/@After/@Around | 通知 | AOP通知 |

### SpringMVC 注解

| 注解 | 作用 | 使用场景 |
|------|------|---------|
| @RequestMapping | 请求映射 | 映射HTTP请求 |
| @GetMapping/@PostMapping | 请求映射简写 | RESTful API |
| @RequestParam | 获取请求参数 | 查询参数 |
| @PathVariable | 获取路径变量 | RESTful路径 |
| @RequestBody | 获取请求体 | JSON数据 |
| @ResponseBody | 响应体 | 返回JSON |
| @RestController | 控制器+响应体 | RESTful控制器 |
| @ControllerAdvice | 全局异常处理 | 异常处理 |

### SpringBoot 注解

| 注解 | 作用 | 使用场景 |
|------|------|---------|
| @SpringBootApplication | 启动注解 | 主类 |
| @EnableAutoConfiguration | 自动配置 | 开启自动配置 |
| @ConfigurationProperties | 配置绑定 | 配置文件绑定 |
| @ConditionalOnProperty | 条件配置 | 根据配置创建Bean |
| @SpringBootTest | 测试 | 集成测试 |

---

## 常见问题

### 1. @Autowired 和 @Resource 的区别？

- **@Autowired**：Spring注解，先按类型（byType），再按名称（byName）
- **@Resource**：JSR-250规范，先按名称（byName），再按类型（byType）

### 2. @Component、@Service、@Repository 的区别？

功能相同，都是 @Component 的特化版本，但语义更清晰：
- @Component：通用组件
- @Service：业务逻辑层
- @Repository：数据访问层
- @Controller：控制器层

### 3. @Controller 和 @RestController 的区别？

- **@Controller**：需要配合 @ResponseBody 才能返回JSON
- **@RestController**：@Controller + @ResponseBody，直接返回JSON

### 4. @Autowired 注入失败怎么办？

1. 检查Bean是否被扫描到（@ComponentScan）
2. 检查是否有多个同类型的Bean（使用@Qualifier）
3. 检查required属性（@Autowired(required = false)）

---

## 最佳实践

1. **依赖注入优先使用构造方法注入**（便于测试，不可变）
2. **@Service、@Repository 等语义化注解**（代码更清晰）
3. **@RestController 用于RESTful API**（简化代码）
4. **合理使用 @Transactional**（事务管理）
5. **使用 @ConfigurationProperties 绑定配置**（类型安全）

