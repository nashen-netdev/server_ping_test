# -*- coding: utf-8 -*-
"""
Ping 测试模块
管理多个服务器的并发 ping 测试
"""

import threading
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
import time
import resource
import re
from .ssh_client import SSHClient
from .session_logger import SessionLogger


def get_system_max_connections() -> int:
    """
    获取系统支持的最大连接数（基于文件描述符限制）
    
    Returns:
        系统建议的最大并发连接数
    """
    try:
        # 获取当前进程的文件描述符软限制
        soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
        
        # 每个 SSH 连接大约需要 3 个文件描述符
        # 预留 100 个给系统和其他用途
        available_fds = soft_limit - 100
        max_from_fds = max(10, available_fds // 3)
        
        # 获取 CPU 核心数作为参考
        cpu_count = os.cpu_count() or 4
        max_from_cpu = cpu_count * 10  # 每核心支持 10 个连接
        
        # 取较小值，但设置上限 50（避免服务器端拒绝）
        return min(max_from_fds, max_from_cpu, 50)
    except Exception:
        # 如果获取失败，返回保守值
        return 20


class PingResult:
    """Ping 结果记录"""
    
    def __init__(self, server_ip: str, server_hostname: str, target_ip: str, log_file: str = None):
        self.server_ip = server_ip
        self.server_hostname = server_hostname
        self.target_ip = target_ip
        self.start_time = datetime.now()
        self.end_time = None
        self.output_lines = []
        self.packet_loss_lines = []  # 记录丢包的行
        self.total_packets = 0
        self.lost_packets = 0
        self.consecutive_losses = 0  # 连续丢包计数
        self.log_file = log_file  # 独立的会话日志文件路径
        
    def _extract_icmp_seq(self, line: str) -> Optional[int]:
        """
        从 ping 输出中提取 icmp_seq 序号
        
        支持格式:
        - "64 bytes from 223.5.5.5: icmp_seq=123 ttl=117 time=20.1 ms"
        - "no answer yet for icmp_seq=123"
        """
        match = re.search(r'icmp_seq[=:](\d+)', line)
        if match:
            return int(match.group(1))
        return None
    
    def _calculate_timestamp(self, icmp_seq: Optional[int]) -> str:
        """
        根据 icmp_seq 计算实际的 ping 时间
        
        ping 每秒发送一个包，icmp_seq=1 对应测试开始时间
        """
        if icmp_seq is not None and icmp_seq > 0:
            # icmp_seq=1 对应 start_time，每增加 1 就加 1 秒
            actual_time = self.start_time + timedelta(seconds=icmp_seq - 1)
            return actual_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            # 无法提取序号时使用当前时间
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def add_output(self, line: str):
        """添加输出行"""
        # 尝试从 ping 输出中提取 icmp_seq，计算实际时间
        icmp_seq = self._extract_icmp_seq(line)
        timestamp = self._calculate_timestamp(icmp_seq)
        formatted_line = f"[{timestamp}] {line}"
        self.output_lines.append(formatted_line)
        
        # 检测是否是 ping 响应或丢包
        if 'bytes from' in line:
            self.total_packets += 1
            self.consecutive_losses = 0  # 重置连续丢包计数
        elif 'no answer yet' in line or 'timeout' in line.lower():
            self.lost_packets += 1
            self.total_packets += 1
            self.consecutive_losses += 1
            self.packet_loss_lines.append(formatted_line)
    
    def finish(self):
        """结束测试"""
        self.end_time = datetime.now()
    
    def get_loss_rate(self) -> float:
        """获取丢包率"""
        if self.total_packets == 0:
            return 0.0
        return (self.lost_packets / self.total_packets) * 100


class PingTester:
    """Ping 测试管理器"""
    
    # 默认并发配置
    DEFAULT_CONNECTION_INTERVAL = 0.3  # 连接间隔（秒）
    MAX_CONCURRENT_LIMIT = 50  # 并发连接数硬上限（避免服务器拒绝）
    
    def __init__(self, servers: List[Dict], output_dir: str, 
                 max_concurrent: int = None, connection_interval: float = None):
        """
        初始化测试管理器
        
        Args:
            servers: 服务器配置列表
            output_dir: 输出目录
            max_concurrent: 最大并发连接数（默认根据任务数和系统资源动态计算）
            connection_interval: 连接间隔秒数（默认 0.3）
        """
        self.servers = servers
        self.output_dir = output_dir
        self.results = []
        self.threads = []
        self.ssh_clients = []  # 跟踪所有 SSH 客户端以便停止时主动关闭
        self.lock = threading.Lock()
        self.running = False
        
        # 计算总任务数
        self.total_tasks = sum(len(server['target_ips']) for server in servers)
        
        # 动态计算默认并发数
        if max_concurrent is None:
            system_max = get_system_max_connections()
            # 取任务数和系统支持数的较小值
            self.max_concurrent = min(self.total_tasks, system_max, self.MAX_CONCURRENT_LIMIT)
            # 确保至少为 1
            self.max_concurrent = max(1, self.max_concurrent)
        else:
            self.max_concurrent = min(max_concurrent, self.MAX_CONCURRENT_LIMIT)
        
        self.connection_interval = connection_interval or self.DEFAULT_CONNECTION_INTERVAL
        
        # 使用信号量限制并发 SSH 连接数
        self.connection_semaphore = threading.Semaphore(self.max_concurrent)
        
        # 为本次测试创建带时间戳的会话目录
        self.session_dir = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, "sessions", self.session_dir), exist_ok=True)
        
    def start_test(self):
        """启动所有测试"""
        self.running = True
        print(f"\n{'='*80}")
        print(f"开始批量 Ping 测试")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"测试服务器数量: {len(self.servers)} 台")
        print(f"{'='*80}\n")
        
        # 计算总任务数
        total_tasks = sum(len(server['target_ips']) for server in self.servers)
        print(f"正在启动 {total_tasks} 个测试任务...")
        print(f"并发限制: 最多 {self.max_concurrent} 个同时连接")
        print(f"连接间隔: {self.connection_interval} 秒")
        print("按 Ctrl+C 可随时停止\n")
        
        # 为每个服务器的每个目标IP创建一个线程
        for server in self.servers:
            for target_ip in server['target_ips']:
                thread = threading.Thread(
                    target=self._run_ping_test,
                    args=(server, target_ip),
                    daemon=True
                )
                thread.start()
                self.threads.append(thread)
                
                # 连接间隔，避免同时建立太多 SSH 连接
                time.sleep(self.connection_interval)
    
    def _run_ping_test(self, server: Dict, target_ip: str):
        """
        运行单个 ping 测试
        
        Args:
            server: 服务器配置
            target_ip: 目标IP
        """
        ssh_client = None
        result = None
        session_logger = None
        
        # 使用信号量限制并发 SSH 连接数
        with self.connection_semaphore:
            try:
                # 连接服务器（带重试机制）
                ssh_client = SSHClient(
                    host=server['ip'],
                    username=server['user'],
                    password=server['password']
                )
                
                if not ssh_client.connect():
                    print(f"✗ 无法连接到服务器 {server['ip']}")
                    return
                
                # 将 SSH 客户端添加到列表（用于停止时统一管理）
                with self.lock:
                    self.ssh_clients.append(ssh_client)
                
                hostname = ssh_client.get_hostname()
                print(f"✓ 已连接: {server['ip']} ({hostname}) -> 开始 ping {target_ip}")
                
                # 创建会话日志记录器（独立的终端日志文件）
                session_logger = SessionLogger(self.output_dir, self.session_dir, server['ip'], hostname, target_ip)
                
                # 创建结果记录
                result = PingResult(server['ip'], hostname, target_ip, session_logger.get_log_file())
                
                with self.lock:
                    self.results.append(result)
                
                # 定义输出回调
                def output_callback(line: str):
                    # 记录到内存
                    result.add_output(line)
                    
                    # 记录到独立的会话日志文件
                    if 'no answer yet' in line or 'timeout' in line.lower():
                        session_logger.log_loss(line)  # 丢包用特殊标记
                    else:
                        session_logger.log(line)  # 正常记录
                    
                    # 控制台智能显示（首次、每10次、恢复时）
                    if 'no answer yet' in line or 'timeout' in line.lower():
                        # 首次丢包或每10次丢包显示一次
                        if result.consecutive_losses == 1:
                            print(f"⚠ 丢包检测: {server['ip']}({hostname}) -> {target_ip}: 开始丢包")
                        elif result.consecutive_losses % 10 == 0:
                            print(f"⚠ 丢包检测: {server['ip']}({hostname}) -> {target_ip}: 已连续丢包 {result.consecutive_losses} 个")
                    elif result.consecutive_losses > 0 and 'bytes from' in line:
                        # 只有真正的 ping 响应才算恢复（避免统计信息误判）
                        print(f"✓ 恢复正常: {server['ip']}({hostname}) -> {target_ip}: 共丢失 {result.consecutive_losses} 个包后恢复")
                
                # 执行 ping
                ssh_client.execute_ping(target_ip, callback=output_callback)
                
            except Exception as e:
                error_msg = f"测试出错: {server['ip']} -> {target_ip}: {str(e)}"
                print(f"✗ {error_msg}")
                if result:
                    result.add_output(error_msg)
                if session_logger:
                    session_logger.log(error_msg)
            finally:
                # 确保结果被标记为完成
                if result and result.end_time is None:
                    result.finish()
                # 关闭会话日志
                if session_logger:
                    session_logger.close()
                # 关闭 SSH 连接（stop_ping 已在 stop_test 中统一调用）
                if ssh_client:
                    ssh_client.close()
    
    def stop_test(self):
        """停止所有测试 - 主动停止所有 SSH ping 并等待线程"""
        self.running = False
        print("\n正在停止所有测试...")
        
        # 1. 主动停止所有 SSH 客户端的 ping（发送 Ctrl+C）
        with self.lock:
            for ssh_client in self.ssh_clients:
                try:
                    ssh_client.stop_ping()
                except:
                    pass  # 忽略已关闭的连接
            
            # 标记所有结果为结束状态（避免 end_time 为 None）
            for result in self.results:
                if result.end_time is None:
                    result.finish()
        
        # 2. 并行等待所有线程结束（总超时5秒，已主动停止 ping）
        start_time = time.time()
        timeout = 5  # 从8秒减少到5秒（因为已主动停止）
        total_threads = len(self.threads)
        last_alive_count = total_threads
        
        while time.time() - start_time < timeout:
            # 检查还有多少线程在运行
            alive_threads = [t for t in self.threads if t.is_alive()]
            alive_count = len(alive_threads)
            
            if alive_count == 0:
                # 所有线程都已停止
                break
            
            # 显示进度（当数量变化时更新）
            if alive_count != last_alive_count:
                stopped_count = total_threads - alive_count
                print(f"  已停止: {stopped_count}/{total_threads} 个连接...", end='\r')
                last_alive_count = alive_count
            
            time.sleep(0.2)  # 每0.2秒检查一次
        
        # 清除进度显示
        print(" " * 60, end='\r')
        
        # 最后再检查一次（可能刚好在循环结束时完成）
        time.sleep(0.5)
        alive_threads = [t for t in self.threads if t.is_alive()]
        
        if alive_threads:
            print(f"警告: 还有 {len(alive_threads)} 个连接未能完全停止（但 ping 进程已终止）")
        
        print("所有测试已停止\n")
    
    def wait_for_completion(self):
        """等待所有测试完成"""
        for thread in self.threads:
            thread.join()
    
    def generate_report(self, report_format: str = 'pdf', pdf_password: str = None) -> str:
        """
        生成测试报告
        
        Args:
            report_format: 报告格式 ('pdf' 或 'txt')
            pdf_password: PDF 所有者密码（仅 PDF 格式有效，默认使用内置密码）
        
        Returns:
            报告文件路径
        """
        if report_format == 'pdf':
            return self._generate_pdf_report(pdf_password)
        else:
            return self._generate_txt_report()
    
    def _generate_pdf_report(self, pdf_password: str = None) -> str:
        """
        生成 PDF 格式报告（加密保护，禁止修改）
        
        Args:
            pdf_password: PDF 所有者密码
        
        Returns:
            PDF 报告文件路径
        """
        from .pdf_report import PDFReportGenerator
        
        kwargs = {
            'results': self.results,
            'servers': self.servers,
            'output_dir': self.output_dir,
            'session_dir': self.session_dir,
        }
        if pdf_password:
            kwargs['owner_password'] = pdf_password
        
        generator = PDFReportGenerator(**kwargs)
        return generator.generate()
    
    def _generate_txt_report(self) -> str:
        """
        生成 TXT 格式报告（传统纯文本格式）
        
        Returns:
            TXT 报告文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(self.output_dir, f"ping_test_report_{timestamp}.txt")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            # 写入报告头
            f.write("="*80 + "\n")
            f.write("批量 Ping 测试报告\n")
            f.write("="*80 + "\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"测试服务器数量: {len(self.servers)} 台\n")
            f.write(f"测试连接总数: {len(self.results)} 对\n")
            f.write("\n")
            
            # 统计信息
            total_connections = len(self.results)
            connections_with_loss = sum(1 for r in self.results if r.lost_packets > 0)
            connections_without_loss = total_connections - connections_with_loss
            
            f.write("="*80 + "\n")
            f.write("测试统计\n")
            f.write("="*80 + "\n")
            f.write(f"总连接数: {total_connections}\n")
            f.write(f"无丢包连接: {connections_without_loss} ({connections_without_loss/total_connections*100:.2f}%)\n")
            f.write(f"有丢包连接: {connections_with_loss} ({connections_with_loss/total_connections*100:.2f}%)\n")
            f.write("\n")
            
            # 如果有丢包，先显示丢包摘要
            if connections_with_loss > 0:
                f.write("="*80 + "\n")
                f.write("丢包情况摘要 ⚠\n")
                f.write("="*80 + "\n")
                for result in self.results:
                    if result.lost_packets > 0:
                        f.write(f"\n服务器: {result.server_ip} ({result.server_hostname})\n")
                        f.write(f"目标IP: {result.target_ip}\n")
                        f.write(f"总包数: {result.total_packets}, 丢包数: {result.lost_packets}, 丢包率: {result.get_loss_rate():.2f}%\n")
                        if result.end_time:
                            f.write(f"测试时长: {(result.end_time - result.start_time).total_seconds():.1f} 秒\n")
                        else:
                            f.write(f"测试时长: 未完成\n")
                        f.write("\n丢包详情:\n")
                        for line in result.packet_loss_lines:
                            f.write(f"  {line}\n")
                        f.write("\n" + "-"*80 + "\n")
                f.write("\n")
            
            # 详细测试结果
            f.write("="*80 + "\n")
            f.write("详细测试结果\n")
            f.write("="*80 + "\n")
            
            for idx, result in enumerate(self.results, 1):
                f.write(f"\n[测试 {idx}/{len(self.results)}]\n")
                f.write(f"服务器: {result.server_ip} ({result.server_hostname})\n")
                f.write(f"目标IP: {result.target_ip}\n")
                f.write(f"开始时间: {result.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                end_time_str = result.end_time.strftime('%Y-%m-%d %H:%M:%S') if result.end_time else '未完成'
                f.write(f"结束时间: {end_time_str}\n")
                if result.end_time:
                    f.write(f"测试时长: {(result.end_time - result.start_time).total_seconds():.1f} 秒\n")
                else:
                    f.write(f"测试时长: 未完成\n")
                f.write(f"总包数: {result.total_packets}, 丢包数: {result.lost_packets}, 丢包率: {result.get_loss_rate():.2f}%\n")
                
                # 如果有丢包，标记提示
                if result.lost_packets > 0:
                    f.write(f"\n⚠️ 警告: 检测到丢包 {result.lost_packets}/{result.total_packets} 个 ({result.get_loss_rate():.2f}%)\n")
                
                # 会话日志文件路径
                if result.log_file:
                    f.write(f"\n完整会话日志: {result.log_file}\n")
                
                f.write("\nPing 输出摘要（最近 50 行）:\n")
                f.write("-"*80 + "\n")
                
                # 只输出最近的 50 行（避免报告过大）
                if result.output_lines:
                    output_to_show = result.output_lines[-50:] if len(result.output_lines) > 50 else result.output_lines
                    if len(result.output_lines) > 50:
                        f.write(f"... (省略前 {len(result.output_lines) - 50} 行，查看完整输出请查看会话日志文件) ...\n\n")
                    for line in output_to_show:
                        f.write(f"{line}\n")
                else:
                    f.write("(无输出记录)\n")
                
                f.write("-"*80 + "\n")
        
        return report_file

