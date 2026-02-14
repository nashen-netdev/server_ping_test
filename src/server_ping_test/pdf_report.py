# -*- coding: utf-8 -*-
"""
PDF 报告生成模块
将纯文本报告内容渲染为加密保护的 PDF（可查看/打印，禁止修改/复制）

内容与 TXT 报告完全一致，PDF 仅作为不可修改的"容器"。
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.pdfencrypt import StandardEncryption


# ---------------------------------------------------------------------------
# 中文字体注册
# ---------------------------------------------------------------------------
_FONT_REGISTERED = False

# 中文字体 + 等宽字体
FONT_CN = 'STSong-Light'
FONT_MONO = 'Courier'

# 页面配置
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_LEFT = 20 * mm
MARGIN_RIGHT = 20 * mm
MARGIN_TOP = 18 * mm
MARGIN_BOTTOM = 18 * mm

# 正文区域
TEXT_WIDTH = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
TEXT_TOP = PAGE_HEIGHT - MARGIN_TOP
TEXT_BOTTOM = MARGIN_BOTTOM

# 字体大小和行高
FONT_SIZE = 9
LINE_HEIGHT = 13  # 点


def _ensure_font():
    """确保中文字体已注册（只注册一次）"""
    global _FONT_REGISTERED
    if not _FONT_REGISTERED:
        pdfmetrics.registerFont(UnicodeCIDFont(FONT_CN))
        _FONT_REGISTERED = True


def _has_chinese(text: str) -> bool:
    """检测文本是否包含中文字符"""
    for ch in text:
        if '\u4e00' <= ch <= '\u9fff' or '\u3000' <= ch <= '\u303f':
            return True
    return False


def generate_pdf_from_text(
    text: str,
    output_path: str,
    owner_password: str = None,
) -> str:
    """
    将纯文本内容渲染为加密保护的 PDF 文件

    安全特性:
        - 无需密码即可打开查看和打印
        - 修改、复制、注释需要 owner 密码
        - 128 位加密

    Args:
        text:           报告的纯文本内容（与 TXT 报告完全一致）
        output_path:    输出 PDF 文件路径
        owner_password: PDF 所有者密码（控制编辑权限，默认 "batch_ping_admin"）

    Returns:
        生成的 PDF 文件路径
    """
    _ensure_font()

    if owner_password is None:
        owner_password = "batch_ping_admin"

    # PDF 加密配置 — 允许查看+打印，禁止修改+复制+注释
    encryption = StandardEncryption(
        userPassword='',
        ownerPassword=owner_password,
        canPrint=1,
        canModify=0,
        canCopy=0,
        canAnnotate=0,
        strength=128,
    )

    c = Canvas(
        output_path,
        pagesize=A4,
        encrypt=encryption,
    )
    c.setTitle("批量 Ping 测试报告")
    c.setAuthor("Batch Ping Tester")
    c.setSubject("网络故障演练测试报告")
    c.setCreator("Batch Ping Tester v1.2.0")

    # 按行渲染文本
    lines = text.splitlines()
    y = TEXT_TOP  # 当前绘制 y 坐标
    page_num = 1

    _draw_footer(c, page_num)

    for line in lines:
        # 如果当前行放不下，换页
        if y - LINE_HEIGHT < TEXT_BOTTOM:
            c.showPage()
            page_num += 1
            y = TEXT_TOP
            _draw_footer(c, page_num)

        # 根据内容选择字体（含中文用宋体，纯 ASCII 用等宽）
        if _has_chinese(line):
            c.setFont(FONT_CN, FONT_SIZE)
        else:
            c.setFont(FONT_MONO, FONT_SIZE)

        # 绘制文本行（截断超长行以防溢出）
        c.drawString(MARGIN_LEFT, y, line)
        y -= LINE_HEIGHT

    c.save()
    return output_path


def _draw_footer(c: Canvas, page_num: int):
    """在当前页绘制页脚（页码 + 保护声明）"""
    c.setFont(FONT_CN, 7)
    c.setFillGray(0.6)
    c.drawCentredString(
        PAGE_WIDTH / 2, 10 * mm,
        f"- {page_num} -    本报告由 Batch Ping Tester 自动生成 | 文档受密码保护，禁止修改",
    )
    c.setFillGray(0)  # 恢复黑色
