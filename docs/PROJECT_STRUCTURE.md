# 项目架构说明

## 目录结构

采用标准的 **src-layout** 结构：

```
ping-mesh/
├── src/                          # 源代码目录（src-layout）
│   └── ping_mesh/               # 包目录
│       ├── __init__.py          # 包初始化，导出主要类
│       ├── __main__.py          # 支持 python -m 运行
│       ├── cli.py               # 命令行接口
│       ├── config_loader.py     # 配置加载模块
│       ├── ssh_client.py        # SSH 客户端模块
│       ├── session_logger.py    # 会话日志记录模块
│       ├── ping_tester.py       # Ping 测试核心模块
│       └── pdf_report.py        # PDF 报告生成模块
│
├── examples/                     # 示例目录
│   └── servers_template.xlsx    # 配置文件模板
│
├── tests/                        # 测试目录
│   └── __init__.py
│
├── docs/                         # 文档目录
│   ├── USAGE.md                 # 使用指南
│   ├── CONFIGURATION.md         # 配置说明
│   ├── TROUBLESHOOTING.md       # 故障排查
│   ├── PROJECT_STRUCTURE.md     # 本文件
│   └── STOP_MECHANISM.md        # 停止机制说明
│
├── results/                      # 测试结果（运行时生成）
│   ├── sessions/                # 会话日志
│   └── ping_test_report_*.pdf   # 测试报告
│
├── requirements.txt              # 依赖包列表
├── pyproject.toml                # 项目配置（Python 标准）
├── README.md                     # 项目概述
├── CHANGELOG.md                  # 版本历史
├── LICENSE                       # 许可证
└── .gitignore                    # Git 忽略配置
```

## 模块说明

### 1. cli.py - 命令行接口

**职责：** 解析命令行参数，协调各模块工作

**入口点：** `ping-mesh` 命令（通过 pyproject.toml 配置）

### 2. config_loader.py - 配置加载模块

**职责：** 从 Excel 文件读取和验证服务器配置

**核心类：**
- `ConfigLoader`: 配置加载器

**主要方法：**
- `load_config()`: 从 Excel 加载配置，返回服务器列表
- `validate_config()`: 验证配置有效性

### 3. ssh_client.py - SSH 客户端模块

**职责：** 管理 SSH 连接和远程命令执行

**核心类：**
- `SSHClient`: SSH 客户端封装

**主要方法：**
- `connect()`: 连接到远程服务器
- `get_hostname()`: 获取服务器主机名
- `execute_ping()`: 执行持续 ping 命令
- `stop_ping()`: 停止 ping 命令
- `close()`: 关闭连接

**特点：**
- 自动处理 SSH 密钥策略
- 支持实时输出回调
- 连接失败自动重试（指数退避）
- 优雅的连接关闭

### 4. ping_tester.py - Ping 测试核心模块

**职责：** 管理多个服务器的并发测试和结果记录

**核心类：**
- `PingResult`: Ping 结果记录类
- `PingTester`: Ping 测试管理器

**PingResult 功能：**
- 记录每行输出（带时间戳）
- 自动检测丢包
- 计算丢包率

**PingTester 功能：**
- 多线程并发测试
- 实时丢包告警
- 生成详细测试报告

### 5. session_logger.py - 会话日志模块

**职责：** 管理每个连接的独立日志文件

**功能：**
- 为每个 SSH 连接创建独立日志
- 记录完整的 ping 输出
- 包含开始/结束时间戳

### 6. pdf_report.py - PDF 报告生成模块

**职责：** 生成加密的 PDF 测试报告

**功能：**
- 专业的页面布局（页眉、页脚、页码）
- 表格和颜色高亮
- 128 位 PDF 加密（禁止修改/复制）
- 中文字体支持

## 数据流

```
┌─────────────────┐
│  Excel 配置文件  │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  ConfigLoader   │  读取配置
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   PingTester    │  创建测试任务
└────────┬────────┘
         │
         ↓
   ┌────┴────┬────┬────┐
   ↓         ↓    ↓    ↓
┌──────┐ ┌──────┐ ... ┌──────┐
│Thread│ │Thread│     │Thread│  多线程并发
└──┬───┘ └──┬───┘     └──┬───┘
   │        │            │
   ↓        ↓            ↓
┌──────┐ ┌──────┐     ┌──────┐
│ SSH  │ │ SSH  │ ... │ SSH  │  SSH 连接
└──┬───┘ └──┬───┘     └──┬───┘
   │        │            │
   ↓        ↓            ↓
┌──────┐ ┌──────┐     ┌──────┐
│ Ping │ │ Ping │ ... │ Ping │  执行 ping
└──┬───┘ └──┬───┘     └──┬───┘
   │        │            │
   └────────┴────────────┘
            │
            ↓
   ┌────────────────┐
   │  PingResult    │  结果记录
   └────────┬───────┘
            │
            ↓
   ┌────────────────┐
   │  PDF/TXT 报告   │
   └────────────────┘
```

## 并发模型

### 线程分配
- 主线程：用户交互和协调
- 工作线程：每个 (服务器 × 目标IP) 组合一个线程

### 线程安全
- 使用 `threading.Lock` 保护共享数据
- 每个 `PingResult` 对象独立管理自己的数据

### 资源管理
- SSH 连接在线程内创建和销毁
- 异常自动捕获和处理
- 优雅关闭所有连接

## 关键技术点

### 1. SSH 交互式 Shell
使用 `paramiko.invoke_shell()` 创建交互式 shell，支持：
- 实时读取输出
- 发送 Ctrl+C 中断信号
- 持续监控命令状态

### 2. 实时输出处理
- 逐字符读取避免阻塞
- 按行缓冲处理输出
- 回调函数实现解耦

### 3. 丢包检测
关键字匹配：
- `no answer yet` - ping -O 选项输出
- `timeout` - 超时提示

### 4. 报告生成
两种格式：
- **PDF**（默认）：专业排版，加密保护
- **TXT**：纯文本，兼容旧流程

## 扩展点

### 1. 支持更多配置源
可以扩展 `ConfigLoader` 支持：
- JSON/YAML 配置文件
- 数据库读取
- API 接口获取

### 2. 自定义测试命令
修改 `SSHClient.execute_ping()` 支持：
- 自定义 ping 参数
- 其他网络测试命令（traceroute, mtr 等）
- 自定义脚本执行

### 3. 多种报告格式
扩展报告生成支持：
- JSON 格式
- CSV 格式
- HTML 可视化报告

### 4. 告警功能
添加告警模块：
- 邮件通知
- 企业微信/钉钉通知
- 自定义 Webhook

## 安全考虑

### 1. 密码保护
- ⚠️ 当前版本使用明文密码
- 建议使用 SSH 密钥认证
- 或使用加密配置文件

### 2. 权限控制
- 配置文件应设置适当权限（600）
- 结果文件包含敏感信息
- 日志文件注意权限设置

### 3. 输入验证
- IP 地址格式验证
- 防止命令注入
- 配置文件完整性检查

## 相关文档

| 文档 | 说明 |
|------|------|
| [README](../README.md) | 项目概述 |
| [使用指南](./USAGE.md) | 详细使用方法 |
| [配置说明](./CONFIGURATION.md) | 配置文件和参数 |
| [故障排查](./TROUBLESHOOTING.md) | 常见问题解决 |
| [停止机制](./STOP_MECHANISM.md) | 技术实现细节 |
| [更新日志](../CHANGELOG.md) | 版本历史 |
