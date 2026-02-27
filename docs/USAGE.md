# 快速使用指南

## 快速开始

### 1. 准备配置文件

```bash
# 复制模板到你的工作目录
cp examples/servers_template.xlsx ~/work/servers.xlsx

# 用 Excel 或 LibreOffice 编辑配置文件
open ~/work/servers.xlsx  # macOS
# 或 libreoffice ~/work/servers.xlsx  # Linux
```

### 2. 运行测试

```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行测试
batch-ping ~/work/servers.xlsx
```

## 配置文件示例

### 简单示例（单个目标 IP）

| ip | user | pass | dip1 | dip2 | dip3 | dip4 |
|----|------|------|------|------|------|------|
| 10.0.0.1 | admin | ******** | 8.8.8.8 | | | |
| 10.0.0.2 | admin | ******** | 8.8.8.8 | | | |

### 复杂示例（多个目标 IP）

| ip | user | pass | dip1 | dip2 | dip3 | dip4 |
|----|------|------|------|------|------|------|
| 10.0.0.1 | admin | ******** | 8.8.8.8 | | | |
| 10.0.0.2 | admin | ******** | 8.8.8.8 | 8.8.4.4 | | |
| 10.0.0.3 | root | ******** | 8.8.8.8 | 8.8.4.4 | 10.0.1.1 | |

## 测试流程

```
1. 准备配置文件
   ↓
2. 运行测试程序
   ↓
3. 观察实时输出（连接状态、丢包告警）
   ↓
4. 执行你的网络操作（如切换路由）
   ↓
5. 继续观察实时丢包情况
   ↓
6. 按 Ctrl+C 停止测试
   ↓
7. 查看生成的测试报告
```

## 常用命令

```bash
# 查看帮助
batch-ping --help

# 运行测试（默认 PDF 报告）
batch-ping servers.xlsx

# 指定输出目录
batch-ping servers.xlsx -o test_results

# 降低并发数（大量服务器时推荐）
batch-ping servers.xlsx -n 5 -i 0.5

# 生成 TXT 格式报告
batch-ping servers.xlsx -f txt

# 使用 python -m 方式运行
python -m server_ping_test servers.xlsx
```

## 输出说明

### 实时控制台输出

```
✓ 已连接: 10.0.0.1 (server-01) -> 开始 ping 8.8.8.8
✓ 已连接: 10.0.0.2 (server-02) -> 开始 ping 8.8.8.8
⚠ 丢包检测: 10.0.0.1 (server-01) -> 8.8.8.8: 开始丢包
✓ 恢复正常: 10.0.0.1 (server-01) -> 8.8.8.8: 共丢失 5 个包后恢复
```

- ✓ 表示连接成功或恢复正常
- ✗ 表示连接失败
- ⚠ 表示检测到丢包

### 测试报告

位置: `results/ping_test_report_YYYYMMDD_HHMMSS.pdf`

包含：
1. 测试统计（总连接数、丢包连接数、达标率）
2. 丢包情况摘要（如有）
3. 每个连接的详细 ping 输出

## 使用技巧

### 技巧 1: 分批测试

如果服务器很多，可以分批测试：

```bash
# 复制配置文件，分别编辑
cp servers.xlsx servers_batch1.xlsx
cp servers.xlsx servers_batch2.xlsx

# 测试第一批
batch-ping servers_batch1.xlsx -o results_batch1

# 测试第二批
batch-ping servers_batch2.xlsx -o results_batch2
```

### 技巧 2: 快速验证配置

测试前先用少量服务器验证配置是否正确：

```bash
# 复制配置文件，只保留 1-2 台服务器
cp servers.xlsx test_small.xlsx
# 编辑 test_small.xlsx，只保留几行测试

# 快速测试
batch-ping test_small.xlsx
```

### 技巧 3: 长时间测试

对于需要长时间运行的测试：

```bash
# 使用 screen 或 tmux
screen -S ping_test
batch-ping servers.xlsx

# 分离会话: Ctrl+A D
# 重新连接: screen -r ping_test
```

## 故障演练场景示例

### 场景: 网络链路切换测试

1. **准备阶段**
   ```bash
   source .venv/bin/activate
   batch-ping servers.xlsx
   ```

2. **观察稳定性** - 等待所有连接建立，确认没有异常丢包

3. **执行切换** - 在网络设备上执行路由切换，观察控制台实时输出

4. **记录结果** - 记录丢包开始/结束时间，计算切换时长

5. **生成报告**
   ```bash
   # 按 Ctrl+C 停止
   # 查看报告
   ls results/ping_test_report_*.pdf
   ```

## 注意事项

1. **首次使用**：建议先用 1-2 台服务器测试，确认配置正确
2. **密码安全**：配置文件包含密码，注意权限控制
3. **网络带宽**：ping 包很小，对带宽影响极小
4. **服务器负载**：ping 对服务器 CPU/内存影响极小
5. **防火墙**：确保本机能 SSH 连接到目标服务器

## 相关文档

| 文档 | 说明 |
|------|------|
| [README](../README.md) | 项目概述 |
| [配置说明](./CONFIGURATION.md) | 配置文件和参数详解 |
| [故障排查](./TROUBLESHOOTING.md) | 常见问题解决 |
| [项目架构](./PROJECT_STRUCTURE.md) | 代码结构说明 |
| [停止机制](./STOP_MECHANISM.md) | 技术实现细节 |
| [更新日志](../CHANGELOG.md) | 版本历史 |
