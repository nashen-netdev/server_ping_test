# -*- coding: utf-8 -*-
"""
配置文件加载模块
从 Excel 文件读取服务器配置信息
"""

import pandas as pd
from typing import List, Dict
import os


class ConfigLoader:
    """配置加载器"""
    
    def __init__(self, excel_path: str):
        """
        初始化配置加载器
        
        Args:
            excel_path: Excel 配置文件路径
        """
        self.excel_path = excel_path
        
    def load_config(self) -> List[Dict]:
        """
        从 Excel 加载配置
        
        Returns:
            服务器配置列表，每个元素包含:
            - ip: 服务器IP
            - user: 用户名
            - password: 密码
            - target_ips: 目标IP列表 (dip1, dip2, dip3, dip4)
        """
        if not os.path.exists(self.excel_path):
            raise FileNotFoundError(f"配置文件不存在: {self.excel_path}")
        
        # 读取 Excel
        df = pd.read_excel(self.excel_path)
        
        # 验证必需列
        required_columns = ['ip']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"配置文件缺少必需列: {col}")
        
        servers = []
        
        for _, row in df.iterrows():
            # 跳过空行
            if pd.isna(row['ip']):
                continue
                
            # 收集目标IP (dip1, dip2, dip3, dip4)
            target_ips = []
            for col in ['dip1', 'dip2', 'dip3', 'dip4']:
                if col in df.columns and not pd.isna(row[col]):
                    target_ips.append(str(row[col]))
            
            # 如果没有目标IP，跳过该服务器
            if not target_ips:
                continue
            
            server_config = {
                'ip': str(row['ip']),
                'user': str(row['user']) if 'user' in df.columns and not pd.isna(row['user']) else 'root',
                'password': str(row['pass']) if 'pass' in df.columns and not pd.isna(row['pass']) else '',
                'target_ips': target_ips
            }
            
            servers.append(server_config)
        
        return servers
    
    def validate_config(self, servers: List[Dict]) -> bool:
        """
        验证配置有效性
        
        Args:
            servers: 服务器配置列表
            
        Returns:
            配置是否有效
        """
        if not servers:
            print("错误: 没有找到有效的服务器配置")
            return False
        
        for idx, server in enumerate(servers):
            if not server.get('ip'):
                print(f"错误: 第 {idx+1} 个服务器缺少IP地址")
                return False
            
            if not server.get('target_ips'):
                print(f"警告: 服务器 {server['ip']} 没有配置目标IP")
        
        return True

