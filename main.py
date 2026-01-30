#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量 Ping 测试工具 - 主程序入口
用于网络故障演练的批量 ping 测试

支持两种运行方式:
1. 直接运行: python3 main.py -c config/servers.xlsx
2. 安装后运行: batch-ping -c config/servers.xlsx
"""

import sys
import os

# 添加 src 目录到 Python 路径（支持直接运行 main.py）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from server_ping_test.cli import main

if __name__ == "__main__":
    sys.exit(main())
