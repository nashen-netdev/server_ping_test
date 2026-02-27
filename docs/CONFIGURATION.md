# 配置说明

## 配置文件格式

配置文件使用 Excel 格式（.xlsx），包含以下列：

| 列名 | 说明 | 是否必填 |
|------|------|---------|
| ip | 服务器 IP 地址 | 必填 |
| user | SSH 用户名 | 可选（默认 root） |
| pass | SSH 密码 | 可选 |
| dip1 | 目标 IP 地址 1 | 至少填一个 |
| dip2 | 目标 IP 地址 2 | 可选 |
| dip3 | 目标 IP 地址 3 | 可选 |
| dip4 | 目标 IP 地址 4 | 可选 |

## 配置示例

| ip | user | pass | dip1 | dip2 | dip3 | dip4 |
|----|------|------|------|------|------|------|
| 10.0.0.1 | admin | ******** | 8.8.8.8 | | | |
| 10.0.0.2 | admin | ******** | 8.8.8.8 | 8.8.4.4 | | |
| 10.0.0.3 | root | ******** | 8.8.8.8 | 8.8.4.4 | 10.0.1.1 | |

> **注意**：配置文件包含明文密码，请妥善保管，设置适当的文件权限（如 `chmod 600`）。

## 命令行参数

```
ping-mesh CONFIG_FILE [选项]
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `CONFIG_FILE` | 位置参数 | 必填 | 服务器配置文件 (Excel 格式) |
| `-o, --output` | 选项 | `results` | 测试结果输出目录 |
| `-n, --max-concurrent` | 选项 | 自动计算 | 最大并发 SSH 连接数 |
| `-i, --interval` | 选项 | `0.3` | 连接发起间隔秒数 |
| `-f, --format` | 选项 | `pdf` | 报告格式：`pdf` 或 `txt` |
| `--pdf-password` | 选项 | 内置密码 | PDF 所有者密码（控制编辑权限） |

## 并发数自动计算

默认根据任务数量和系统资源动态计算，取以下三者的最小值：

1. 总任务数（避免浪费）
2. 系统文件描述符限制 / 3（每个 SSH 连接约需 3 个 fd）
3. 硬上限 50（避免服务器端拒绝连接）

## 输出结构

运行后会在输出目录生成：

```
results/
├── sessions/                    # 会话日志目录
│   └── YYYYMMDD_HHMMSS/        # 每次测试的详细日志
│       ├── server1_to_target1.log
│       └── server2_to_target2.log
└── ping_test_report_*.pdf      # 测试报告
```

## PDF 报告安全特性

| 功能 | 状态 | 说明 |
|------|------|------|
| 打开查看 | ✅ 无需密码 | 任何 PDF 阅读器直接打开 |
| 打印 | ✅ 允许 | 可正常打印纸质报告 |
| 修改内容 | ❌ 禁止 | 需要 owner 密码才能编辑 |
| 复制文本 | ❌ 禁止 | 防止内容被复制篡改 |
| 加密强度 | 128 位 | 标准 PDF 加密 |

## 高级用法示例

```bash
# 测试大量服务器时，适当降低并发数和增加间隔
ping-mesh servers.xlsx -n 5 -i 0.5

# 网络条件好时，可以增加并发数
ping-mesh servers.xlsx -n 20 -i 0.2

# 生成 PDF 报告并指定编辑密码
ping-mesh servers.xlsx --pdf-password YourSecretPass

# 生成传统 TXT 报告
ping-mesh servers.xlsx -f txt -o my_results
```

## 相关文档

| 文档 | 说明 |
|------|------|
| [README](../README.md) | 项目概述 |
| [使用指南](./USAGE.md) | 详细使用方法 |
| [故障排查](./TROUBLESHOOTING.md) | 常见问题解决 |
| [项目架构](./PROJECT_STRUCTURE.md) | 代码结构说明 |
| [停止机制](./STOP_MECHANISM.md) | 技术实现细节 |
| [更新日志](../CHANGELOG.md) | 版本历史 |
