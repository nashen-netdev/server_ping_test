# 批量 Ping 测试工具

用于网络故障演练的批量 ping 测试工具，支持同时在多台服务器上 ping 多个目标 IP，并实时记录所有结果和丢包情况。

## 功能亮点

- 从 Excel 配置文件批量读取服务器和目标 IP
- 并发执行多个服务器的 ping 测试
- 可配置的并发连接数控制和 SSH 自动重试机制
- 实时检测和记录丢包情况
- 自动生成测试报告（PDF 加密保护 / TXT 格式）
- 支持手动停止测试（Ctrl+C）

## 系统要求

- Python 3.8+
- 支持 SSH 连接的 Linux 服务器
- Excel 配置文件（.xlsx 格式）

## 快速安装

```bash
# 克隆项目并进入目录
git clone <repository-url> && cd server_ping_test

# 创建虚拟环境并安装依赖
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## 基本用法

```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行测试（默认生成 PDF 报告）
batch-ping servers.xlsx

# 指定输出目录和并发数
batch-ping servers.xlsx -o results -n 10

# 生成 TXT 格式报告
batch-ping servers.xlsx -f txt

# 查看帮助
batch-ping --help
```

## 文档导航

| 文档 | 说明 |
|------|------|
| [快速使用指南](docs/USAGE.md) | 详细的使用方法和技巧 |
| [配置说明](docs/CONFIGURATION.md) | 配置文件格式和参数说明 |
| [故障排查](docs/TROUBLESHOOTING.md) | 常见问题和解决方案 |
| [项目架构](docs/PROJECT_STRUCTURE.md) | 代码结构和技术细节 |
| [停止机制](docs/STOP_MECHANISM.md) | Ping 停止原理和实现 |
| [更新日志](CHANGELOG.md) | 版本历史和变更记录 |

## 项目结构

```
server_ping_test/
├── src/server_ping_test/    # 源代码（src-layout）
├── examples/                 # 配置文件模板
├── tests/                    # 测试目录
├── docs/                     # 详细文档
├── requirements.txt          # 依赖列表
└── pyproject.toml           # 项目配置
```

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件
