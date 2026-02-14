# -*- coding: utf-8 -*-
"""
批量 Ping 测试工具 (server_ping_test)
用于网络故障演练的批量 ping 测试和结果记录

使用方式:
    from server_ping_test import ConfigLoader, PingTester
    
    # 加载配置
    loader = ConfigLoader("config/servers.xlsx")
    servers = loader.load_config()
    
    # 运行测试
    tester = PingTester(servers, "results")
    tester.start_test()
"""

__version__ = "1.2.0"
__author__ = "sen"

from .config_loader import ConfigLoader
from .ping_tester import PingTester, PingResult
from .ssh_client import SSHClient
from .session_logger import SessionLogger
from .pdf_report import generate_pdf_from_text

__all__ = [
    "ConfigLoader",
    "PingTester",
    "PingResult",
    "SSHClient",
    "SessionLogger",
    "generate_pdf_from_text",
]

