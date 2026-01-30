# -*- coding: utf-8 -*-
"""
会话日志记录模块
为每个 ping 会话保存独立的日志文件
"""

import os
from datetime import datetime
from typing import TextIO


class SessionLogger:
    """会话日志记录器 - 每个连接一个独立的日志文件"""
    
    def __init__(self, output_dir: str, session_dir: str, server_ip: str, server_hostname: str, target_ip: str):
        """
        初始化会话日志记录器
        
        Args:
            output_dir: 输出目录
            session_dir: 本次测试的会话目录名
            server_ip: 服务器IP
            server_hostname: 服务器主机名
            target_ip: 目标IP
        """
        self.server_ip = server_ip
        self.server_hostname = server_hostname
        self.target_ip = target_ip
        
        # 文件名格式: server_ip_to_target_ip.log
        safe_filename = f"{server_ip.replace('.', '_')}_to_{target_ip.replace('.', '_')}.log"
        # 路径: output_dir/sessions/session_dir/filename
        self.log_file = os.path.join(output_dir, "sessions", session_dir, safe_filename)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        # 打开文件
        self.file_handle: TextIO = open(self.log_file, 'w', encoding='utf-8', buffering=1)  # 行缓冲
        
        # 写入文件头
        self._write_header()
        
    def _write_header(self):
        """写入日志文件头"""
        self.file_handle.write("="*80 + "\n")
        self.file_handle.write(f"Ping 测试会话日志\n")
        self.file_handle.write("="*80 + "\n")
        self.file_handle.write(f"服务器IP: {self.server_ip}\n")
        self.file_handle.write(f"服务器主机名: {self.server_hostname}\n")
        self.file_handle.write(f"目标IP: {self.target_ip}\n")
        self.file_handle.write(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        self.file_handle.write("="*80 + "\n\n")
        
    def log(self, line: str):
        """
        记录一行日志
        
        Args:
            line: 日志内容
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # 保留毫秒
        self.file_handle.write(f"[{timestamp}] {line}\n")
        
    def log_loss(self, line: str):
        """
        记录丢包信息（带特殊标记）
        
        Args:
            line: 丢包信息
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        self.file_handle.write(f"[{timestamp}] ⚠ {line}\n")
        
    def close(self):
        """关闭日志文件"""
        if self.file_handle and not self.file_handle.closed:
            self.file_handle.write("\n" + "="*80 + "\n")
            self.file_handle.write(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            self.file_handle.write("="*80 + "\n")
            self.file_handle.close()
    
    def get_log_file(self) -> str:
        """获取日志文件路径"""
        return self.log_file

