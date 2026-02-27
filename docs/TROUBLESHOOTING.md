# 故障排查

## 问题 1: 无法连接服务器

**现象：** `✗ 无法连接到服务器 x.x.x.x`

**排查思路：**

1. 检查服务器 IP 是否可达（本地 ping 测试）
2. 确认 SSH 端口（默认 22）是否开放
3. 验证用户名和密码是否正确
4. 检查防火墙设置
5. 查看服务器 SSH 服务状态

## 问题 2: 大量连接错误

**现象：** 同时测试多台服务器时，出现 "No existing session" 或 "Error reading SSH protocol banner" 错误

**原因分析：**

- 同时发起的 SSH 连接数超过了网络或服务器的限制
- SSH 服务器的 `MaxStartups` 参数限制了并发连接数
- 网络设备（防火墙/负载均衡器）有连接速率限制

**解决方案：**

```bash
# 降低并发连接数
ping-mesh servers.xlsx -n 5

# 增加连接间隔
ping-mesh servers.xlsx -i 0.5

# 同时调整两个参数
ping-mesh servers.xlsx -n 5 -i 0.5
```

**服务器端优化（如有权限）：**

```bash
# 修改 /etc/ssh/sshd_config
MaxStartups 30:50:100  # 提高并发连接限制
```

## 问题 3: 依赖安装失败

**现象：** `pip install` 报错

**排查思路：**

1. 确认 Python 版本（需要 3.8+）
   ```bash
   python3 --version
   ```

2. 更新 pip
   ```bash
   pip install --upgrade pip
   ```

3. 使用国内镜像源
   ```bash
   pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
   ```

4. 检查网络连接

## 问题 4: Excel 文件读取失败

**现象：** 配置文件加载错误

**排查思路：**

1. 确认文件路径正确
2. 检查 Excel 文件格式（必须是 .xlsx）
3. 验证必需列是否存在（ip, dip1）
4. 确保至少有一行有效数据
5. 检查数据格式（IP 地址格式是否正确）

## 问题 5: 虚拟环境问题

**现象：** 找不到模块 / ModuleNotFoundError

**解决方案：**

```bash
# 确保虚拟环境已激活
source .venv/bin/activate

# 确认 Python 路径
which python3

# 重新安装依赖
pip install -r requirements.txt

# 或使用开发模式安装
pip install -e .
```

## 问题 6: 报告生成失败

**现象：** PDF 报告生成报错

**排查思路：**

1. 确认 reportlab 已正确安装
   ```bash
   pip show reportlab
   ```

2. 尝试使用 TXT 格式
   ```bash
   ping-mesh servers.xlsx -f txt
   ```

3. 检查输出目录是否有写入权限

## 问题 7: 测试过程中内存占用过高

**现象：** 长时间测试或大规模测试时内存持续增长

**解决方案：**

1. 分批测试，每批测试完成后查看报告
2. 适当降低并发数
3. 定期停止并重新开始测试

## 快速排错表

| 问题 | 解决方法 |
|------|---------|
| 找不到 python3 | `which python3` 确认路径 |
| 模块导入失败 | `source .venv/bin/activate` |
| 无法连接服务器 | 检查 IP、用户名、密码、防火墙 |
| Excel 读取失败 | 确认文件格式为 .xlsx |
| 连接超时过多 | 降低并发数 `-n 5` |
| 报告生成失败 | 尝试 `-f txt` 格式 |

## 日志分析

会话日志位于 `results/sessions/YYYYMMDD_HHMMSS/` 目录下，每个连接一个独立文件。

查看日志可以帮助分析：
- 具体的丢包时间点
- ping 统计信息
- 连接异常原因

## 相关文档

| 文档 | 说明 |
|------|------|
| [README](../README.md) | 项目概述 |
| [使用指南](./USAGE.md) | 详细使用方法 |
| [配置说明](./CONFIGURATION.md) | 配置文件和参数 |
| [项目架构](./PROJECT_STRUCTURE.md) | 代码结构说明 |
| [停止机制](./STOP_MECHANISM.md) | 技术实现细节 |
| [更新日志](../CHANGELOG.md) | 版本历史 |
