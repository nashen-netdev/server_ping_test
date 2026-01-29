# -*- coding: utf-8 -*-
"""
SSH 客户端模块
用于连接远程服务器并执行 ping 命令
"""

import paramiko
import time
from typing import Optional, Callable
import threading


class SSHClient:
    """SSH 客户端封装"""
    
    def __init__(self, host: str, username: str, password: str, port: int = 22):
        """
        初始化 SSH 客户端
        
        Args:
            host: 服务器地址
            username: 用户名
            password: 密码
            port: SSH 端口
        """
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.client = None
        self.channel = None
        self.hostname = None
        self.should_stop = False  # 停止标志
        
    def connect(self, timeout: int = 15, banner_timeout: int = 30, retries: int = 3) -> bool:
        """
        连接到服务器（带重试机制）
        
        Args:
            timeout: 连接超时时间（秒）
            banner_timeout: SSH banner 读取超时时间（秒）
            retries: 重试次数
            
        Returns:
            连接是否成功
        """
        last_error = None
        
        for attempt in range(retries):
            try:
                self.client = paramiko.SSHClient()
                self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    timeout=timeout,
                    banner_timeout=banner_timeout,
                    look_for_keys=False,
                    allow_agent=False
                )
                
                # 获取主机名
                stdin, stdout, stderr = self.client.exec_command('hostname')
                self.hostname = stdout.read().decode('utf-8').strip()
                
                return True
            except Exception as e:
                last_error = e
                if self.client:
                    try:
                        self.client.close()
                    except:
                        pass
                    self.client = None
                
                # 如果还有重试机会，等待后重试
                if attempt < retries - 1:
                    wait_time = (attempt + 1) * 2  # 指数退避: 2s, 4s
                    time.sleep(wait_time)
        
        # 所有重试都失败
        print(f"连接服务器 {self.host} 失败 (已重试 {retries} 次): {str(last_error)}")
        return False
    
    def get_hostname(self) -> str:
        """获取主机名"""
        return self.hostname or self.host
    
    def execute_ping(self, target_ip: str, callback: Optional[Callable] = None) -> None:
        """
        执行 ping 命令（持续 ping）
        
        Args:
            target_ip: 目标IP地址
            callback: 回调函数，用于处理每行输出
        """
        try:
            # 使用 -O 选项来显示无应答的包
            command = f"ping {target_ip} -O"
            
            # 创建交互式 shell
            self.channel = self.client.invoke_shell()
            self.channel.send(command + '\n')
            
            # 持续读取输出
            buffer = ""
            while not self.should_stop:
                if self.channel.recv_ready():
                    chunk = self.channel.recv(4096).decode('utf-8', errors='ignore')
                    buffer += chunk
                    
                    # 按行处理
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        
                        # 过滤掉命令行提示符和空行
                        if line and not line.endswith('$') and not line.endswith('#'):
                            if callback:
                                callback(line)
                
                # 检查连接是否关闭
                if self.channel.exit_status_ready():
                    break
                
                time.sleep(0.1)
            
            # 循环退出后，快速读取剩余的缓冲区（包括 ping 的统计信息）
            time.sleep(0.3)  # 稍微等待 ping 统计输出（从0.5秒减少到0.3秒）
            
            # 快速读取所有剩余数据（最多尝试10次，避免无限等待）
            for _ in range(10):
                if not self.channel.recv_ready():
                    break
                
                try:
                    chunk = self.channel.recv(4096).decode('utf-8', errors='ignore')
                    buffer += chunk
                    time.sleep(0.05)  # 短暂延迟（从0.1秒减少到0.05秒）
                except:
                    break
            
            # 处理所有缓冲的内容
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                line = line.strip()
                if line and not line.endswith('$') and not line.endswith('#'):
                    if callback:
                        callback(line)
            
            # 处理最后可能没有换行符的内容
            if buffer.strip():
                if callback:
                    callback(buffer.strip())
                
        except Exception as e:
            if callback:
                callback(f"执行 ping 命令出错: {str(e)}")
    
    def stop_ping(self):
        """
        停止 ping 命令 - 模拟手动 Ctrl+C 的方式
        
        流程：
        1. 设置停止标志，让 execute_ping 的循环退出
        2. 发送 Ctrl+C 到远程服务器停止 ping
        3. execute_ping 会读取 ping 的统计信息后退出
        """
        try:
            # 1. 设置停止标志
            self.should_stop = True
            
            # 2. 发送 Ctrl+C 停止 ping（模拟手动操作）
            if self.channel and not self.channel.closed:
                self.channel.send('\x03')
                
                # ping 收到 Ctrl+C 后会输出统计信息：
                # ^C
                # --- 223.5.5.5 ping statistics ---
                # 100 packets transmitted, 95 received, 5% packet loss, time 99050ms
                # rtt min/avg/max/mdev = 20.123/20.456/20.789/0.123 ms
                
                # execute_ping 会继续读取这些统计信息并通过回调记录
                
        except Exception as e:
            pass  # 停止时的错误可以忽略
    
    def close(self):
        """关闭连接"""
        try:
            if self.channel:
                self.channel.close()
            if self.client:
                self.client.close()
        except Exception as e:
            print(f"关闭连接失败: {str(e)}")

