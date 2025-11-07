# 快速使用指南

## 快速开始

### 1. 准备配置文件

```bash
# 直接编辑现有的配置文件
open config/servers_empty.xlsx  # 用 Excel 打开

# 或者复制一份新的配置
cp config/servers_empty.xlsx config/my_servers.xlsx
```

### 2. 运行测试

```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行测试
python3 main.py -c config/servers_empty.xlsx
```

## 配置文件示例

### 简单示例（单个目标IP）

| ip | user | pass | dip1 | dip2 | dip3 | dip4 |
|----|------|------|------|------|------|------|
| 192.168.1.1 | admin | password | 223.5.5.5 | | | |
| 192.168.1.2 | admin | password | 223.5.5.5 | | | |

### 复杂示例（多个目标IP）

| ip | user | pass | dip1 | dip2 | dip3 | dip4 |
|----|------|------|------|------|------|------|
| 192.168.1.1 | test | 123456 | 223.5.5.5 | | | |
| 192.168.1.5 | admin | pass123 | 223.5.5.5 | | 192.168.2.1 | |
| 192.168.1.7 | root | secret | 223.5.5.5 | 223.6.6.6 | 192.168.2.1 | |

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
python3 main.py --help

# 运行测试
python3 main.py -c config/servers_empty.xlsx

# 指定输出目录
python3 main.py -c config/servers_empty.xlsx -o test_results_20251106

# 后台运行（保存日志）
nohup python3 main.py -c config/servers_empty.xlsx > test.log 2>&1 &

# 查看进程
ps aux | grep main.py

# 停止后台进程
pkill -f main.py
```

## 输出说明

### 实时控制台输出

```
✓ 已连接: 192.168.1.1 (xb01-cpu-0001) -> 开始 ping 223.5.5.5
✓ 已连接: 192.168.1.2 (xb01-cpu-0002) -> 开始 ping 223.5.5.5
⚠ 丢包检测: 192.168.1.1(xb01-cpu-0001) -> 223.5.5.5: no answer yet for icmp_seq=10
```

- ✓ 表示连接成功
- ✗ 表示连接失败
- ⚠ 表示检测到丢包

### 测试报告文件

位置: `results/ping_test_report_YYYYMMDD_HHMMSS.txt`

包含：
1. 测试统计（总连接数、丢包连接数、达标率）
2. 丢包情况摘要（如有）
3. 每个连接的详细 ping 输出

## 使用技巧

### 技巧1: 分批测试

如果服务器很多，可以分批测试：

```bash
# 复制配置文件，分别编辑
cp config/servers_empty.xlsx config/servers_batch1.xlsx
cp config/servers_empty.xlsx config/servers_batch2.xlsx

# 测试第一批
python3 main.py -c config/servers_batch1.xlsx -o results_batch1

# 测试第二批
python3 main.py -c config/servers_batch2.xlsx -o results_batch2
```

### 技巧2: 快速验证配置

测试前先用少量服务器验证配置是否正确：

```bash
# 复制配置文件，只保留1-2台服务器
cp config/servers_empty.xlsx config/test_small.xlsx
# 编辑 test_small.xlsx，只保留几行测试

# 快速测试
python3 main.py -c config/test_small.xlsx
```

### 技巧3: 长时间测试

对于需要长时间运行的测试：

```bash
# 使用 screen 或 tmux
screen -S ping_test
./run.sh config/servers.xlsx

# 分离会话: Ctrl+A D
# 重新连接: screen -r ping_test
```

### 技巧4: 定时报告

需要定时查看报告而不停止测试时，可以手动复制 results 文件：

```bash
# 在另一个终端查看最新结果
ls -lt results/
cat results/ping_test_report_*.txt | head -100
```

## 故障演练场景示例

### 场景: 网络链路切换测试

1. **准备阶段**
   ```bash
   # 启动测试
   source .venv/bin/activate
   python3 main.py -c config/production_servers.xlsx
   ```

2. **观察稳定性**
   - 等待所有连接建立
   - 确认没有异常丢包

3. **执行切换**
   - 在网络设备上执行路由切换
   - 观察控制台实时输出

4. **记录结果**
   - 记录丢包开始时间
   - 记录丢包结束时间
   - 计算切换时长

5. **生成报告**
   ```bash
   # 按 Ctrl+C 停止
   # 查看报告
   cat results/ping_test_report_*.txt
   ```

## 注意事项

1. **首次使用**：建议先用 1-2 台服务器测试，确认配置正确
2. **密码安全**：配置文件包含密码，注意权限控制
3. **网络带宽**：ping 包很小，对带宽影响极小
4. **服务器负载**：ping 对服务器 CPU/内存影响极小
5. **防火墙**：确保本机能 SSH 连接到目标服务器

## 快速排错

| 问题 | 解决方法 |
|------|---------|
| 找不到 python3 | `which python3` 确认路径 |
| 模块导入失败 | `source .venv/bin/activate` |
| 无法连接服务器 | 检查 IP、用户名、密码 |
| Excel 读取失败 | 确认文件格式为 .xlsx |
| 虚拟环境未激活 | `source .venv/bin/activate` |

## 获取帮助

查看完整文档：
```bash
cat README.md | less
```

查看配置文件：
```bash
# 用 Excel 或 LibreOffice 打开
open config/servers_empty.xlsx
```

