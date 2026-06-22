#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""런처 아이콘 생성: 브랜드 블루 배경 + 흰 방패 + 체크(보안인증/학습).
출력: app/assets/icon/ic_launcher.png(1024, 배경포함), ic_foreground.png(1024, 투명, 적응형 전경).
"""
import os
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'app', 'assets', 'icon')
os.makedirs(OUT, exist_ok=True)

BLUE = (30, 91, 203, 255)      # #1E5BCB
BLUE_DK = (22, 67, 150, 255)
WHITE = (255, 255, 255, 255)
S = 1024


def shield_points(cx, top, w, h):
    """둥근 어깨 + 뾰족한 아래의 방패 외곽 다각형 점들."""
    hw = w / 2
    pts = [
        (cx - hw, top + h * 0.06),
        (cx, top),
        (cx + hw, top + h * 0.06),
        (cx + hw, top + h * 0.52),
        (cx + hw * 0.62, top + h * 0.80),
        (cx, top + h),
        (cx - hw * 0.62, top + h * 0.80),
        (cx - hw, top + h * 0.52),
    ]
    return pts


def draw_shield(draw, cx, top, w, h, fill, check=BLUE):
    draw.polygon(shield_points(cx, top, w, h), fill=fill)
    # 체크마크
    lw = int(w * 0.13)
    x0, y0 = cx - w * 0.22, top + h * 0.46
    x1, y1 = cx - w * 0.04, top + h * 0.64
    x2, y2 = cx + w * 0.26, top + h * 0.28
    draw.line([(x0, y0), (x1, y1)], fill=check, width=lw, joint='curve')
    draw.line([(x1, y1), (x2, y2)], fill=check, width=lw, joint='curve')
    for p in [(x0, y0), (x1, y1), (x2, y2)]:
        draw.ellipse([p[0] - lw / 2, p[1] - lw / 2, p[0] + lw / 2, p[1] + lw / 2], fill=check)


def vgradient(size, top, bottom):
    img = Image.new('RGBA', (size, size))
    px = img.load()
    for y in range(size):
        t = y / (size - 1)
        px_row = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(4))
        for x in range(size):
            px[x, y] = px_row
    return img


# 1) 배경 포함 아이콘
bg = vgradient(S, BLUE, BLUE_DK)
d = ImageDraw.Draw(bg)
draw_shield(d, S / 2, S * 0.20, S * 0.52, S * 0.60, fill=WHITE, check=BLUE)
bg.save(os.path.join(OUT, 'ic_launcher.png'))

# 2) 적응형 전경(투명 배경, 안전영역 안에 더 작게)
fg = Image.new('RGBA', (S, S), (0, 0, 0, 0))
d2 = ImageDraw.Draw(fg)
draw_shield(d2, S / 2, S * 0.30, S * 0.40, S * 0.44, fill=WHITE, check=BLUE)
fg.save(os.path.join(OUT, 'ic_foreground.png'))

print('icons written to', OUT)
