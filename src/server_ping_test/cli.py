# -*- coding: utf-8 -*-
"""
命令行接口模块
提供 batch-ping 命令入口
"""

import sys
import os
import argparse

from .config_loader import ConfigLoader
from .ping_tester import PingTester


def main():
    """主函数 - 命令行入口"""
    parser = argparse.ArgumentParser(
        description='批量 Ping 测试工具 - 用于网络故障演练',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  batch-ping servers.xlsx                       # 默认生成 PDF 报告（加密保护）
  batch-ping servers.xlsx -f txt                # 生成传统 TXT 报告
  batch-ping servers.xlsx -o /tmp/output        # 指定输出目录
  batch-ping servers.xlsx -n 20 -i 0.5          # 自定义并发和间隔
  batch-ping servers.xlsx --pdf-password MyPass  # 自定义 PDF 编辑密码
  python -m server_ping_test servers.xlsx
  
配置文件格式 (Excel):
  - ip: 服务器IP地址 (必需)
  - user: SSH用户名 (可选，默认为root)
  - pass: SSH密码 (可选)
  - dip1, dip2, dip3, dip4: 目标IP地址 (至少一个)
        """
    )
    
    parser.add_argument(
        'config',
        metavar='CONFIG_FILE',
        help='服务器配置文件 (Excel格式)'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='results',
        help='测试结果输出目录 (默认: results)'
    )
    
    parser.add_argument(
        '-n', '--max-concurrent',
        type=int,
        default=None,
        help='最大并发 SSH 连接数 (默认: 根据任务数和系统资源自动计算)'
    )
    
    parser.add_argument(
        '-i', '--interval',
        type=float,
        default=0.3,
        help='连接发起间隔秒数 (默认: 0.3)'
    )
    
    parser.add_argument(
        '-f', '--format',
        choices=['pdf', 'txt'],
        default='pdf',
        help='报告输出格式 (默认: pdf，受密码保护不可修改)'
    )
    
    parser.add_argument(
        '--pdf-password',
        default=None,
        help='PDF 所有者密码（用于控制编辑权限，默认使用内置密码）'
    )
    
    args = parser.parse_args()
    
    # 打印欢迎信息
    print("\n" + "="*80)
    print("批量 Ping 测试工具".center(80))
    print("="*80)
    print(f"配置文件: {args.config}")
    print(f"输出目录: {args.output}")
    print(f"连接间隔: {args.interval} 秒")
    fmt_desc = "PDF（加密保护，禁止修改）" if args.format == 'pdf' else "TXT（纯文本）"
    print(f"报告格式: {fmt_desc}")
    print("="*80 + "\n")
    
    try:
        # 加载配置
        print("正在加载配置文件...")
        config_loader = ConfigLoader(args.config)
        servers = config_loader.load_config()
        
        if not config_loader.validate_config(servers):
            print("配置验证失败，程序退出")
            return 1
        
        print(f"成功加载 {len(servers)} 台服务器配置")
        
        # 统计总的测试连接数
        total_tests = sum(len(s['target_ips']) for s in servers)
        print(f"将执行 {total_tests} 个 ping 测试\n")
        
        # 显示服务器列表
        print("测试服务器列表:")
        for idx, server in enumerate(servers, 1):
            print(f"  {idx}. {server['ip']} -> {', '.join(server['target_ips'])}")
        print()
        
        # 创建测试管理器
        tester = PingTester(
            servers, 
            args.output,
            max_concurrent=args.max_concurrent,
            connection_interval=args.interval
        )
        
        # 显示实际并发配置
        if args.max_concurrent is None:
            print(f"并发连接: {tester.max_concurrent} (自动计算: 任务数 {total_tests}, 系统支持)")
        else:
            print(f"并发连接: {tester.max_concurrent} (用户指定)")
        print()
        
        # 启动测试
        tester.start_test()
        
        # 等待用户停止或测试完成
        try:
            tester.wait_for_completion()
        except KeyboardInterrupt:
            print("\n\n收到用户中断信号，正在停止...")
            tester.stop_test()
        
        # 生成报告（无论是正常结束还是中断都要生成）
        fmt_hint = "PDF" if args.format == 'pdf' else "TXT"
        print(f"\n正在生成 {fmt_hint} 测试报告...")
        report_file = tester.generate_report(
            report_format=args.format,
            pdf_password=args.pdf_password,
        )
        
        print("\n" + "="*80)
        print("测试完成")
        print("="*80)
        print(f"测试报告已保存: {report_file}")
        print(f"会话日志目录: {os.path.join(args.output, 'sessions', tester.session_dir)}/")
        print(f"输出目录: {args.output}")
        print("="*80 + "\n")
        
        return 0
        
    except FileNotFoundError as e:
        print(f"\n错误: {str(e)}")
        return 1
    except Exception as e:
        print(f"\n发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
