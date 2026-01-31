# -*- coding: utf-8 -*-
"""
支持 python -m server_ping_test 方式运行

使用方式:
    python -m server_ping_test -c config/servers.xlsx
"""

from .cli import main

if __name__ == "__main__":
    main()
