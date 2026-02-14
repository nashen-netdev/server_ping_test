# -*- coding: utf-8 -*-
"""
PDF 报告生成模块
生成带加密保护的专业 PDF 测试报告（可查看/打印，禁止修改/复制）
"""

import os
from datetime import datetime
from typing import List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.pdfencrypt import StandardEncryption


# ---------------------------------------------------------------------------
# 中文字体注册（使用 reportlab 内置 CID 宋体，无需额外字体文件）
# ---------------------------------------------------------------------------
_FONT_CN_REGISTERED = False


def _ensure_font():
    """确保中文字体已注册（只注册一次）"""
    global _FONT_CN_REGISTERED
    if not _FONT_CN_REGISTERED:
        pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
        _FONT_CN_REGISTERED = True


# 字体常量
FONT_CN = 'STSong-Light'
FONT_MONO = 'Courier'

# 配色方案
COLOR_PRIMARY = colors.HexColor('#1a1a2e')
COLOR_SECONDARY = colors.HexColor('#16213e')
COLOR_TEXT = colors.HexColor('#333333')
COLOR_TEXT_LIGHT = colors.HexColor('#555555')
COLOR_TEXT_MUTED = colors.HexColor('#999999')
COLOR_SUCCESS = colors.HexColor('#2e7d32')
COLOR_DANGER = colors.HexColor('#c62828')
COLOR_DANGER_BG = colors.HexColor('#ffebee')
COLOR_SUCCESS_BG = colors.HexColor('#e8f5e9')
COLOR_BORDER = colors.HexColor('#cccccc')
COLOR_BORDER_LIGHT = colors.HexColor('#e0e0e0')
COLOR_BG_LIGHT = colors.HexColor('#fafafa')
COLOR_CODE_BG = colors.HexColor('#f5f5f5')


# ---------------------------------------------------------------------------
# 样式定义
# ---------------------------------------------------------------------------
def _create_styles() -> dict:
    """创建 PDF 文档样式集"""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='TitleCN', fontName=FONT_CN, fontSize=22, leading=28,
        alignment=TA_CENTER, spaceAfter=6 * mm, textColor=COLOR_PRIMARY,
    ))
    styles.add(ParagraphStyle(
        name='SubTitleCN', fontName=FONT_CN, fontSize=12, leading=16,
        alignment=TA_CENTER, spaceAfter=4 * mm, textColor=COLOR_TEXT_LIGHT,
    ))
    styles.add(ParagraphStyle(
        name='SectionCN', fontName=FONT_CN, fontSize=14, leading=20,
        spaceBefore=8 * mm, spaceAfter=4 * mm, textColor=COLOR_SECONDARY,
    ))
    styles.add(ParagraphStyle(
        name='BodyCN', fontName=FONT_CN, fontSize=10, leading=15,
        spaceAfter=2 * mm, textColor=COLOR_TEXT,
    ))
    styles.add(ParagraphStyle(
        name='CodeBlock', fontName=FONT_MONO, fontSize=7, leading=9.5,
        spaceAfter=1 * mm, textColor=COLOR_TEXT,
        backColor=COLOR_CODE_BG, borderPadding=(4, 4, 4, 4),
    ))
    styles.add(ParagraphStyle(
        name='Warning', fontName=FONT_CN, fontSize=10, leading=14,
        textColor=COLOR_DANGER, spaceAfter=2 * mm,
    ))
    styles.add(ParagraphStyle(
        name='Success', fontName=FONT_CN, fontSize=10, leading=14,
        textColor=COLOR_SUCCESS, spaceAfter=2 * mm,
    ))
    return styles


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------
def _sanitize(text: str) -> str:
    """
    清理文本，确保能安全嵌入 reportlab 的 XML 段落。
    - 替换 emoji 为纯文本标记
    - 转义 XML 特殊字符
    """
    replacements = {
        '\u26a0\ufe0f': '[!]', '\u26a0': '[!]',       # ⚠️ / ⚠
        '\u2713': '[OK]', '\u2714': '[OK]',             # ✓ / ✔
        '\u2717': '[FAIL]', '\u2718': '[FAIL]',         # ✗ / ✘
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text


# ---------------------------------------------------------------------------
# PDF 报告生成器
# ---------------------------------------------------------------------------
class PDFReportGenerator:
    """
    PDF 报告生成器 — 生成带权限保护的专业 Ping 测试报告

    安全特性:
        - 无需密码即可打开查看和打印
        - 修改、复制、注释等操作需要 owner 密码
        - 128 位 AES 加密
    """

    def __init__(
        self,
        results: list,
        servers: list,
        output_dir: str,
        session_dir: str,
        owner_password: str = "batch_ping_admin",
    ):
        """
        Args:
            results:        PingResult 对象列表
            servers:        服务器配置列表
            output_dir:     输出目录
            session_dir:    会话目录名
            owner_password: PDF 所有者密码（用于控制编辑权限）
        """
        _ensure_font()
        self.results = results
        self.servers = servers
        self.output_dir = output_dir
        self.session_dir = session_dir
        self.owner_password = owner_password
        self.styles = _create_styles()
        self.timestamp = datetime.now()

    # ------------------------------------------------------------------
    # 公共接口
    # ------------------------------------------------------------------
    def generate(self) -> str:
        """
        生成 PDF 报告

        Returns:
            生成的 PDF 文件绝对路径
        """
        ts = self.timestamp.strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(self.output_dir, f"ping_test_report_{ts}.pdf")

        # PDF 加密配置 — 允许查看+打印，禁止修改+复制+注释
        encryption = StandardEncryption(
            userPassword='',                    # 打开无需密码
            ownerPassword=self.owner_password,   # 编辑需要此密码
            canPrint=1,
            canModify=0,
            canCopy=0,
            canAnnotate=0,
            strength=128,
        )

        doc = SimpleDocTemplate(
            report_file,
            pagesize=A4,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=22 * mm,
            title="批量 Ping 测试报告",
            author="Batch Ping Tester",
            subject="网络故障演练测试报告",
            creator="Batch Ping Tester v1.2.0",
            encrypt=encryption,
        )

        story: list = []
        self._build_title(story)
        self._build_statistics(story)
        self._build_loss_summary(story)
        self._build_details(story)

        doc.build(
            story,
            onFirstPage=self._draw_header_footer,
            onLaterPages=self._draw_header_footer,
        )
        return report_file

    # ------------------------------------------------------------------
    # 页面装饰（页眉 / 页脚）
    # ------------------------------------------------------------------
    def _draw_header_footer(self, canvas, doc):
        """在每一页绘制页眉和页脚"""
        canvas.saveState()
        w, h = A4

        # --- 页眉 ---
        canvas.setFont(FONT_CN, 8)
        canvas.setFillColor(COLOR_TEXT_MUTED)
        canvas.drawString(20 * mm, h - 12 * mm, "批量 Ping 测试报告")
        canvas.drawRightString(
            w - 20 * mm, h - 12 * mm,
            f"生成时间: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
        )
        canvas.setStrokeColor(COLOR_BORDER)
        canvas.setLineWidth(0.5)
        canvas.line(20 * mm, h - 14 * mm, w - 20 * mm, h - 14 * mm)

        # --- 页脚 ---
        page_num = canvas.getPageNumber()
        canvas.setFont(FONT_CN, 8)
        canvas.setFillColor(COLOR_TEXT_MUTED)
        canvas.drawCentredString(w / 2, 12 * mm, f"- {page_num} -")
        canvas.setFont(FONT_CN, 7)
        canvas.drawCentredString(
            w / 2, 8 * mm,
            "本报告由 Batch Ping Tester 自动生成 | 文档受密码保护，禁止修改",
        )
        canvas.line(20 * mm, 16 * mm, w - 20 * mm, 16 * mm)
        canvas.restoreState()

    # ------------------------------------------------------------------
    # 内容构建
    # ------------------------------------------------------------------
    def _build_title(self, story: list):
        """标题 + 基本信息"""
        story.append(Spacer(1, 10 * mm))
        story.append(Paragraph("批量 Ping 测试报告", self.styles['TitleCN']))
        story.append(Paragraph(
            f"生成时间: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            self.styles['SubTitleCN'],
        ))
        story.append(Spacer(1, 4 * mm))

        info = [
            ['测试服务器数量', f'{len(self.servers)} 台'],
            ['测试连接总数', f'{len(self.results)} 对'],
            ['会话目录', self.session_dir],
        ]
        t = Table(info, colWidths=[50 * mm, 100 * mm])
        t.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), FONT_CN, 10),
            ('TEXTCOLOR', (0, 0), (0, -1), COLOR_TEXT_LIGHT),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t)
        story.append(Spacer(1, 6 * mm))
        story.append(HRFlowable(
            width="100%", thickness=1, color=COLOR_BORDER_LIGHT,
        ))

    def _build_statistics(self, story: list):
        """测试统计"""
        story.append(Paragraph("测试统计", self.styles['SectionCN']))
        total = len(self.results)
        if total == 0:
            story.append(Paragraph("无测试结果", self.styles['BodyCN']))
            return

        with_loss = sum(1 for r in self.results if r.lost_packets > 0)
        without_loss = total - with_loss

        data = [
            ['指标', '数值', '占比'],
            ['总连接数', str(total), '100%'],
            ['无丢包连接', str(without_loss), f'{without_loss / total * 100:.1f}%'],
            ['有丢包连接', str(with_loss), f'{with_loss / total * 100:.1f}%'],
        ]
        t = Table(data, colWidths=[60 * mm, 40 * mm, 40 * mm])
        style_cmds = [
            ('FONT', (0, 0), (-1, -1), FONT_CN, 10),
            ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 2), (-1, 2), COLOR_SUCCESS_BG),
        ]
        if with_loss > 0:
            style_cmds.append(('BACKGROUND', (0, 3), (-1, 3), COLOR_DANGER_BG))
            style_cmds.append(('TEXTCOLOR', (0, 3), (-1, 3), COLOR_DANGER))
        t.setStyle(TableStyle(style_cmds))
        story.append(t)

    def _build_loss_summary(self, story: list):
        """丢包情况摘要"""
        lossy = [r for r in self.results if r.lost_packets > 0]
        if not lossy:
            story.append(Spacer(1, 4 * mm))
            story.append(Paragraph(
                "[OK] 所有连接测试正常，未检测到丢包", self.styles['Success'],
            ))
            return

        story.append(Paragraph("[!] 丢包情况摘要", self.styles['SectionCN']))

        # 汇总表
        header = ['服务器', '目标 IP', '总包数', '丢包数', '丢包率', '测试时长']
        rows = [header]
        for r in lossy:
            dur = '未完成'
            if r.end_time:
                dur = f'{(r.end_time - r.start_time).total_seconds():.1f}s'
            rows.append([
                f'{r.server_ip}\n({r.server_hostname})',
                r.target_ip,
                str(r.total_packets),
                str(r.lost_packets),
                f'{r.get_loss_rate():.2f}%',
                dur,
            ])

        cw = [45 * mm, 30 * mm, 20 * mm, 20 * mm, 20 * mm, 22 * mm]
        t = Table(rows, colWidths=cw)
        t.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), FONT_CN, 8),
            ('BACKGROUND', (0, 0), (-1, 0), COLOR_DANGER),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.HexColor('#fff8f8'), colors.white]),
        ]))
        story.append(t)

        # 每条连接的丢包明细
        story.append(Spacer(1, 4 * mm))
        for r in lossy:
            story.append(Paragraph(
                _sanitize(f"{r.server_ip} ({r.server_hostname}) -> {r.target_ip} 丢包详情:"),
                self.styles['Warning'],
            ))
            lines = r.packet_loss_lines[:20]
            for line in lines:
                story.append(Paragraph(_sanitize(line), self.styles['CodeBlock']))
            if len(r.packet_loss_lines) > 20:
                story.append(Paragraph(
                    f"... 共 {len(r.packet_loss_lines)} 条丢包记录，此处仅展示前 20 条 ...",
                    self.styles['BodyCN'],
                ))
            story.append(Spacer(1, 3 * mm))

    def _build_details(self, story: list):
        """详细测试结果（每个连接）"""
        story.append(PageBreak())
        story.append(Paragraph("详细测试结果", self.styles['SectionCN']))

        for idx, r in enumerate(self.results, 1):
            icon = "[!]" if r.lost_packets > 0 else "[OK]"
            sty = self.styles['Warning'] if r.lost_packets > 0 else self.styles['Success']

            story.append(Paragraph(
                _sanitize(
                    f"{icon} 测试 {idx}/{len(self.results)}: "
                    f"{r.server_ip} ({r.server_hostname}) -> {r.target_ip}"
                ),
                sty,
            ))

            end_str = r.end_time.strftime('%Y-%m-%d %H:%M:%S') if r.end_time else '未完成'
            dur_str = '未完成'
            if r.end_time:
                dur_str = f'{(r.end_time - r.start_time).total_seconds():.1f} 秒'

            detail = [
                ['开始时间', r.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                 '结束时间', end_str],
                ['测试时长', dur_str, '丢包率', f'{r.get_loss_rate():.2f}%'],
                ['总包数', str(r.total_packets), '丢包数', str(r.lost_packets)],
            ]
            if r.log_file:
                detail.append(['会话日志', r.log_file, '', ''])

            dt = Table(detail, colWidths=[25 * mm, 55 * mm, 25 * mm, 55 * mm])
            dt_style = [
                ('FONT', (0, 0), (-1, -1), FONT_CN, 8),
                ('TEXTCOLOR', (0, 0), (0, -1), COLOR_TEXT_LIGHT),
                ('TEXTCOLOR', (2, 0), (2, -1), COLOR_TEXT_LIGHT),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.3, COLOR_BORDER_LIGHT),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('BACKGROUND', (0, 0), (-1, -1), COLOR_BG_LIGHT),
            ]
            if r.log_file:
                dt_style.append(('SPAN', (1, len(detail) - 1), (3, len(detail) - 1)))
            dt.setStyle(TableStyle(dt_style))
            story.append(dt)

            # Ping 输出摘要
            story.append(Spacer(1, 2 * mm))
            story.append(Paragraph("Ping 输出摘要（最近 50 行）:", self.styles['BodyCN']))

            if r.output_lines:
                show = r.output_lines[-50:] if len(r.output_lines) > 50 else r.output_lines
                if len(r.output_lines) > 50:
                    story.append(Paragraph(
                        f"... 省略前 {len(r.output_lines) - 50} 行，"
                        f"查看完整输出请参考会话日志文件 ...",
                        self.styles['BodyCN'],
                    ))
                # 每 5 行合并为一个段落，平衡可读性和性能
                batch = 5
                for i in range(0, len(show), batch):
                    chunk = show[i:i + batch]
                    text = '<br/>'.join(_sanitize(ln) for ln in chunk)
                    story.append(Paragraph(text, self.styles['CodeBlock']))
            else:
                story.append(Paragraph("(无输出记录)", self.styles['BodyCN']))

            story.append(Spacer(1, 4 * mm))
            story.append(HRFlowable(
                width="100%", thickness=0.5, color=COLOR_BORDER_LIGHT,
            ))
