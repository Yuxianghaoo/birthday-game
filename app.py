# -*- coding: utf-8 -*-
"""小小学习家 · 中班生日学习小程序（唯一礼物版）

手机浏览器打开即玩：欢迎页 → 关卡地图 → 6 个小关卡 → 奖状。
不登录、不收集信息，所有进度只存在当前浏览器会话里。
"""

from __future__ import annotations

import json
import mimetypes
import random
import re
import time
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import streamlit as st

# ---------------------------------------------------------------------------
# 1. 配置区：改昵称、祝福语、音频目录都在这里
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="生日快乐｜小小学习家",
    page_icon="🎂",
    layout="centered",
    initial_sidebar_state="collapsed",
)

APP_CONFIG = {
    # 改这里就能换成孩子的小名
    "nickname": "小宝贝",
    # 奖状上的生日祝福
    "birthday_wish": "生日快乐！愿你每天都开心，喜欢探索，喜欢学习。",
    # 小寿星生日：欢迎页会按“今天/明天/还有几天”自动显示彩蛋
    "birthday_month": 11,
    "birthday_day": 20,
    # 日期彩蛋按中国时区显示
    "timezone": "Asia/Shanghai",
    # 可选音频目录；没有文件也不会报错
    "audio_dir": "audio",
}

BASE_DIR = Path(__file__).resolve().parent

LEVELS = [
    {"id": 1, "name": "颜色点点乐", "icon": "🎨", "praise": "小眼睛真亮！"},
    {"id": 2, "name": "数蜡烛", "icon": "🕯️", "praise": "数得真清楚！"},
    {"id": 3, "name": "形状配对", "icon": "🔷", "praise": "形状认得很棒！"},
    {"id": 4, "name": "找小动物", "icon": "🐰", "praise": "小动物都认识你啦！"},
    {"id": 5, "name": "英语小耳朵", "icon": "👂", "praise": "小耳朵真灵！"},
    {"id": 6, "name": "记忆翻牌", "icon": "🃏", "praise": "记性真好！"},
]

# 四个难度阶段。默认阶段 2，不会自动升阶，只能在“家长查看”里切换。
STAGES = {
    1: {
        "name": "小芽",
        "badge": "🌱",
        "caption": "第一次玩也不怕",
        "questions": 2,
        "options": 2,
        "shape_options": 2,
        "counting_max": 3,
        "memory_pairs": 2,
        "memory_rounds": 1,
        "animal_grid": 4,
        "animal_columns": 2,
        "english_options": 2,
        "english_actions": False,
        "english_numbers": False,
        "number_max": 3,
        "multi": False,
        "read_aloud_default": True,
        "hint_mode": "specific",
        "show_timer": False,
    },
    2: {
        "name": "小苗",
        "badge": "🌿",
        "caption": "中班日常刚刚好",
        "questions": 3,
        "options": 4,
        "shape_options": 4,
        "counting_max": 5,
        "memory_pairs": 2,
        "memory_rounds": 2,
        "animal_grid": 6,
        "animal_columns": 3,
        "english_options": 4,
        "english_actions": False,
        "english_numbers": True,
        "number_max": 5,
        "multi": False,
        "read_aloud_default": False,
        "hint_mode": "gentle",
        "show_timer": False,
    },
    3: {
        "name": "小树",
        "badge": "🌳",
        "caption": "家长手动开启的挑战档",
        "questions": 4,
        "options": 6,
        "shape_options": 6,
        "counting_max": 10,
        "memory_pairs": 3,
        "memory_rounds": 2,
        "animal_grid": 9,
        "animal_columns": 3,
        "english_options": 6,
        "english_actions": True,
        "english_numbers": True,
        "number_max": 10,
        "multi": True,
        "read_aloud_default": False,
        "hint_mode": "minimal",
        "show_timer": True,
    },
    4: {
        "name": "小果",
        "badge": "🍎",
        "caption": "5–6 岁的小挑战",
        "questions": 5,
        "options": 6,
        "shape_options": 6,
        "counting_max": 10,
        "memory_pairs": 4,
        "memory_rounds": 2,
        "animal_grid": 9,
        "animal_columns": 3,
        "english_options": 6,
        "english_actions": True,
        "english_numbers": True,
        "number_max": 10,
        "multi": True,
        "read_aloud_default": False,
        "hint_mode": "minimal",
        "show_timer": True,
    },
}

COLOR_GROUPS = [
    {
        "key": "red",
        "cn": "红色",
        "en": "red",
        "items": [
            {"id": "red_apple", "emoji": "🍎", "name_cn": "苹果"},
            {"id": "red_strawberry", "emoji": "🍓", "name_cn": "草莓"},
        ],
    },
    {
        "key": "yellow",
        "cn": "黄色",
        "en": "yellow",
        "items": [
            {"id": "yellow_banana", "emoji": "🍌", "name_cn": "香蕉"},
            {"id": "yellow_lemon", "emoji": "🍋", "name_cn": "柠檬"},
        ],
    },
    {
        "key": "green",
        "cn": "绿色",
        "en": "green",
        "items": [
            {"id": "green_kiwi", "emoji": "🥝", "name_cn": "猕猴桃"},
            {"id": "green_broccoli", "emoji": "🥦", "name_cn": "西兰花"},
        ],
    },
    {
        "key": "purple",
        "cn": "紫色",
        "en": "purple",
        "items": [
            {"id": "purple_grapes", "emoji": "🍇", "name_cn": "葡萄"},
            {"id": "purple_eggplant", "emoji": "🍆", "name_cn": "茄子"},
        ],
    },
    {
        "key": "blue",
        "cn": "蓝色",
        "en": "blue",
        "items": [
            {"id": "blue_ball", "emoji": "🔵", "name_cn": "球"},
            {"id": "blue_block", "emoji": "🟦", "name_cn": "积木"},
        ],
    },
    {
        "key": "orange",
        "cn": "橙色",
        "en": "orange",
        "items": [
            {"id": "orange_orange", "emoji": "🍊", "name_cn": "橘子"},
            {"id": "orange_carrot", "emoji": "🥕", "name_cn": "胡萝卜"},
        ],
    },
]

COLOR_ITEMS = []
for _group in COLOR_GROUPS:
    for _item in _group["items"]:
        COLOR_ITEMS.append(
            {
                "id": _item["id"],
                "emoji": _item["emoji"],
                "name_cn": _item["name_cn"],
                "color_key": _group["key"],
                "color_cn": _group["cn"],
                "color_en": _group["en"],
            }
        )

SHAPES = [
    {"id": "circle", "glyph": "●", "cn": "圆形"},
    {"id": "square", "glyph": "■", "cn": "方形"},
    {"id": "triangle", "glyph": "▲", "cn": "三角形"},
    {"id": "star", "glyph": "★", "cn": "星星"},
    {"id": "heart", "glyph": "♥", "cn": "心形"},
    {"id": "diamond", "glyph": "◆", "cn": "菱形"},
    {"id": "rectangle", "glyph": "▬", "cn": "长方形"},
]

ANIMALS = [
    {"id": "cat", "emoji": "🐱", "cn": "小猫咪", "en": "cat"},
    {"id": "dog", "emoji": "🐶", "cn": "小狗", "en": "dog"},
    {"id": "rabbit", "emoji": "🐰", "cn": "小兔子", "en": "rabbit"},
    {"id": "pig", "emoji": "🐷", "cn": "小猪", "en": "pig"},
    {"id": "sheep", "emoji": "🐑", "cn": "小羊", "en": "sheep"},
    {"id": "chicken", "emoji": "🐔", "cn": "小鸡", "en": "chicken"},
    {"id": "duck", "emoji": "🦆", "cn": "小鸭子", "en": "duck"},
    {"id": "cow", "emoji": "🐮", "cn": "小牛", "en": "cow"},
    {"id": "horse", "emoji": "🐴", "cn": "小马", "en": "horse"},
]

COUNT_THEMES = [
    {"emoji": "🕯️", "name": "蜡烛", "unit": "根"},
    {"emoji": "🎈", "name": "气球", "unit": "个"},
    {"emoji": "⭐", "name": "星星", "unit": "颗"},
    {"emoji": "🍎", "name": "苹果", "unit": "个"},
]

EN_NUMBERS = [
    {"id": "one", "word": "one", "cn": "一", "emoji": "1️⃣"},
    {"id": "two", "word": "two", "cn": "二", "emoji": "2️⃣"},
    {"id": "three", "word": "three", "cn": "三", "emoji": "3️⃣"},
    {"id": "four", "word": "four", "cn": "四", "emoji": "4️⃣"},
    {"id": "five", "word": "five", "cn": "五", "emoji": "5️⃣"},
    {"id": "six", "word": "six", "cn": "六", "emoji": "6️⃣"},
    {"id": "seven", "word": "seven", "cn": "七", "emoji": "7️⃣"},
    {"id": "eight", "word": "eight", "cn": "八", "emoji": "8️⃣"},
    {"id": "nine", "word": "nine", "cn": "九", "emoji": "9️⃣"},
    {"id": "ten", "word": "ten", "cn": "十", "emoji": "🔟"},
]

EN_NUMBER_BY_VALUE = {i + 1: w for i, w in enumerate(EN_NUMBERS)}

EN_COLORS = [
    {"id": group["key"], "word": group["en"], "cn": group["cn"], "emoji": group["items"][0]["emoji"]}
    for group in COLOR_GROUPS
]

EN_ANIMALS = [
    {"id": animal["id"], "word": animal["en"], "cn": animal["cn"], "emoji": animal["emoji"]}
    for animal in ANIMALS
]

EN_ACTIONS = [
    {"id": "clap", "word": "clap your hands", "cn": "拍拍手", "emoji": "👏"},
    {"id": "jump", "word": "jump", "cn": "跳一跳", "emoji": "🤸"},
    {"id": "nose", "word": "touch your nose", "cn": "摸摸鼻子", "emoji": "👃"},
    {"id": "stand", "word": "stand up", "cn": "站起来", "emoji": "🧍"},
    {"id": "sit", "word": "sit down", "cn": "坐下", "emoji": "🪑"},
]

MEMORY_THEMES = [
    ["🐱", "🐶", "🐰", "🐷", "🐸", "🦊", "🐼", "🐨"],
    ["🍎", "🍌", "🍇", "🍓", "🍊", "🍉", "🍑", "🥝"],
    ["⭐", "❤️", "🌈", "🎈", "🎁", "🍀", "🌙", "☀️"],
]

CORRECT_PRAISE = ["太棒啦！", "答对啦！", "真厉害！", "好眼力！", "小脑袋转得真快！"]
WRONG_PRAISE = ["再试试看～", "没关系，再想想～", "不着急，再来一次～"]

# ---------------------------------------------------------------------------
# 2. 样式：手机优先，大按钮、宽间距、轻轻柔柔的生日氛围
# ---------------------------------------------------------------------------

APP_CSS = """
<style>
:root {
    --ink: #403541;
    --muted: #8c7a86;
    --pink: #dc6e89;
    --pink-deep: #c95875;
    --pink-soft: #ffe9ee;
    --cream: #fff9f1;
    --gold: #e9bd68;
    --green: #79a98a;
    --line: #f2dfe2;
}
html, body, [class*="css"] {
    font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans SC", sans-serif;
}
.stApp {
    background:
        radial-gradient(circle at 8% 0%, rgba(255, 222, 228, .72), transparent 32%),
        radial-gradient(circle at 95% 8%, rgba(255, 236, 196, .56), transparent 30%),
        linear-gradient(180deg, #fffaf5 0%, #fffdfb 48%, #fff7f8 100%);
    background-attachment: fixed;
}
[data-testid="stAppViewContainer"] { background: transparent; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stDecoration"], [data-testid="stToolbar"], #MainMenu, footer { display: none !important; }
.block-container {
    max-width: 590px;
    padding-top: 1.0rem;
    padding-bottom: 3.2rem;
    padding-left: 1rem;
    padding-right: 1rem;
}
h1, h2, h3, h4, p, label, div { color: var(--ink); }
p { line-height: 1.6; }
[data-testid="stHorizontalBlock"] { gap: .7rem; }
.stButton > button, .stButton button {
    border-radius: 18px;
    border: 1.5px solid #f1d9df;
    background: #fffdfb;
    color: #4d3d4a;
    font-weight: 700;
    min-height: 3.25rem;
    box-shadow: 0 4px 0 rgba(222, 178, 187, .18);
    transition: transform .12s ease, box-shadow .12s ease, border-color .12s ease, background .12s ease;
    white-space: normal;
}
.stButton button:hover {
    border-color: #eda8b7;
    background: #fff8f9;
    color: #4d3d4a;
    transform: translateY(-1px);
}
.stButton button:active {
    transform: translateY(2px);
    box-shadow: 0 1px 0 rgba(222, 178, 187, .16);
}
.stButton button:focus:not(:active) { border-color: #e58da0; }
.stButton button[data-testid="stBaseButton-primary"], .stButton button[kind="primary"] {
    background: linear-gradient(135deg, #e9859d 0%, #d76380 100%);
    border: 0;
    color: #fff;
    box-shadow: 0 6px 0 #c45470, 0 10px 22px rgba(216, 99, 128, .22);
    font-size: 1.08rem;
    letter-spacing: .02em;
}
.stButton button[data-testid="stBaseButton-primary"]:hover, .stButton button[kind="primary"]:hover {
    background: linear-gradient(135deg, #ec91a7 0%, #d96b87 100%);
    color: #fff;
}
.stButton button:disabled {
    opacity: .95;
    color: #8f7f89;
    background: #fbf3ee;
    border-color: #f0e2d8;
    box-shadow: none;
}
.stButton button p, .stButton button span, .stButton button div {
    color: inherit !important;
    font-size: inherit !important;
    line-height: inherit !important;
}
[data-testid="stCaptionContainer"] p { color: #9a8791; font-size: .8rem; line-height: 1.45; }
[data-testid="stMarkdownContainer"] p { line-height: 1.65; }
hr { border-color: #f3e3e3; }

/* 关卡按钮 */
.st-key-level_cards button {
    min-height: 4.05rem;
    border-radius: 20px;
    font-size: 1rem;
    text-align: left;
    padding: .7rem .85rem;
    background: rgba(255, 253, 249, .95);
}
.st-key-level_cards button p { text-align: left; line-height: 1.25; }
.st-key-level_cards [data-testid="stCaptionContainer"] { margin-top: -.25rem; padding-left: .2rem; }

/* 选项按钮：图标要够大，孩子一眼就能看清 */
.st-key-emoji_opts button { min-height: 6.2rem; font-size: 3.75rem; line-height: 1; padding: .2rem; }
.st-key-animal_opts button { min-height: 6.0rem; font-size: 3.55rem; line-height: 1; padding: .15rem; }
.st-key-shape_opts button { min-height: 6.2rem; font-size: 4.2rem; line-height: 1; padding: .1rem; color: #604f60; }
.st-key-number_opts button { min-height: 4.2rem; font-size: 2.1rem; padding: .15rem; }
.st-key-memory_opts button { min-height: 5.9rem; font-size: 3.1rem; line-height: 1; padding: .15rem; }
.st-key-english_opts button { min-height: 6.0rem; font-size: 3.55rem; line-height: 1; padding: .15rem; }
.st-key-action_opts button { min-height: 6.0rem; font-size: 3.4rem; line-height: 1; padding: .15rem; }

/* 小按钮：返回、读题 */
.st-key-top_nav button, .st-key-read_prompt button {
    min-height: 2.2rem;
    padding: .15rem .55rem;
    border: 0;
    background: transparent;
    box-shadow: none;
    color: #9a7d89;
    font-size: .86rem;
    font-weight: 600;
}
.st-key-top_nav button:hover, .st-key-read_prompt button:hover {
    background: #fff4f6;
    color: #b65d75;
}

/* 顶部进度 */
.topbar {
    background: rgba(255, 255, 255, .78);
    border: 1px solid #f4e0e2;
    border-radius: 21px;
    padding: 12px 14px 10px;
    margin: 0 0 14px;
    box-shadow: 0 8px 24px rgba(172, 113, 128, .08);
    backdrop-filter: blur(10px);
}
.topbar-row { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
.chip {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    padding: 4px 9px;
    background: #fff5f6;
    color: #7e5967;
    font-size: .73rem;
    font-weight: 700;
    letter-spacing: .01em;
}
.chip.star { background: #fff8e7; color: #9b762e; }
.chip.total { background: #f1f8f1; color: #5d8067; }
.progress-track {
    height: 9px;
    background: #fbe9ec;
    border-radius: 999px;
    margin: 10px 0 7px;
    overflow: hidden;
}
.progress-fill {
    display: block;
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, #f3a1b3 0%, #f0c671 100%);
    transition: width .35s ease;
}
.topmeta {
    display: flex;
    flex-wrap: wrap;
    gap: 3px 12px;
    color: #917d87;
    font-size: .72rem;
    font-weight: 600;
}
.topmeta .spacer { flex: 1; }

/* 欢迎页 */
.hero {
    position: relative;
    overflow: hidden;
    border: 1px solid #f5dedf;
    border-radius: 30px;
    background:
        radial-gradient(circle at 84% 6%, rgba(255, 218, 160, .6), transparent 26%),
        radial-gradient(circle at 10% 92%, rgba(255, 205, 218, .5), transparent 30%),
        rgba(255, 253, 249, .93);
    padding: 30px 22px 24px;
    text-align: center;
    box-shadow: 0 18px 44px rgba(177, 113, 128, .13);
    margin-bottom: 16px;
}
.hero-balloon { position: absolute; font-size: 1.75rem; opacity: .85; animation: floaty 4.8s ease-in-out infinite; }
.hero-balloon.b1 { left: 16px; top: 22px; animation-delay: -.7s; }
.hero-balloon.b2 { right: 22px; top: 32px; animation-delay: -2.1s; font-size: 1.45rem; }
.hero-balloon.b3 { right: 34px; bottom: 24px; animation-delay: -1.2s; font-size: 1.3rem; }
.hero-balloon.b4 { left: 28px; bottom: 26px; animation-delay: -3.0s; font-size: 1.2rem; }
.hero-kicker {
    font-size: .66rem;
    letter-spacing: .18em;
    color: #b68d58;
    font-weight: 800;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.hero-cake {
    display: inline-block;
    font-size: 3.8rem;
    line-height: 1;
    filter: drop-shadow(0 10px 12px rgba(183, 124, 110, .18));
    animation: bob 3.4s ease-in-out infinite;
}
.hero h1 {
    font-size: clamp(2.05rem, 9.8vw, 2.9rem);
    line-height: 1.18;
    margin: .6rem 0 .35rem;
    color: #b9516e;
    letter-spacing: .02em;
    font-weight: 900;
}
.hero .hero-name {
    font-size: 1.18rem;
    font-weight: 800;
    color: #5b4854;
    margin: .2rem 0 .7rem;
}
.hero .hero-copy {
    color: #7f6c78;
    font-size: .96rem;
    margin: .35rem auto .95rem;
    max-width: 23rem;
}
.date-pill {
    display: inline-flex;
    flex-direction: column;
    align-items: center;
    gap: 1px;
    background: #fff7e6;
    border: 1px solid #f2dfb5;
    border-radius: 17px;
    padding: 7px 14px;
    font-size: .77rem;
    color: #94713b;
    font-weight: 700;
    line-height: 1.45;
}
.date-pill .date-sub { font-size: .72rem; color: #a8844e; font-weight: 600; }
.hero-foot {
    text-align: center;
    color: #ad9198;
    font-size: .78rem;
    margin: -2px 0 14px;
}
.wish-card {
    border: 1px dashed #ecc7a8;
    background: #fff8ef;
    border-radius: 20px;
    padding: 14px 16px;
    text-align: center;
    color: #846950;
    font-size: .9rem;
    line-height: 1.7;
    margin-top: 4px;
}
.wish-card b { color: #b95e72; }

/* 地图 */
.map-head { text-align: center; margin: 8px 0 16px; }
.map-head .map-title { font-size: 1.62rem; font-weight: 900; margin: 0 0 4px; color: #4c3946; }
.map-head p { margin: 0; color: #947e89; font-size: .86rem; }
.stage-badge-card {
    text-align: center;
    border-radius: 24px;
    padding: 18px 16px;
    margin: 12px 0 14px;
    background: linear-gradient(135deg, #fff8e7, #fff4f5);
    border: 1px solid #f0d7a8;
    box-shadow: 0 10px 26px rgba(181, 139, 76, .1);
}
.stage-badge-icon { font-size: 2.8rem; line-height: 1.1; }
.stage-badge-card b { display: block; margin-top: 4px; color: #91682e; font-size: 1.02rem; }
.stage-badge-card p { margin: 3px 0 0; color: #a2866c; font-size: .8rem; }

/* 关卡页 */
.level-head { display: flex; align-items: center; gap: 12px; margin: 2px 0 14px; }
.level-icon {
    width: 3.3rem; height: 3.3rem;
    display: flex; align-items: center; justify-content: center;
    border-radius: 18px; background: #fff0f3; font-size: 1.85rem;
    box-shadow: inset 0 0 0 1px #f6dce1;
    flex: 0 0 auto;
}
.level-head .level-title { font-size: 1.42rem; font-weight: 900; margin: 0; line-height: 1.2; }
.level-head p { margin: 2px 0 0; font-size: .78rem; color: #9b818c; }
.prompt-card {
    border: 1px solid #f3dee2;
    border-radius: 24px;
    background: rgba(255, 253, 250, .94);
    padding: 17px 15px 13px;
    box-shadow: 0 10px 30px rgba(176, 117, 131, .08);
    margin-bottom: 12px;
    text-align: center;
}
.prompt-text {
    font-size: clamp(1.32rem, 5.8vw, 1.58rem);
    font-weight: 900;
    line-height: 1.45;
    color: #43333f;
    margin: 0;
}
.prompt-sub { font-size: .8rem; color: #a18792; margin: .35rem 0 0; }
.word-chip {
    display: inline-block;
    background: #f2f8f4;
    color: #557767;
    border: 1px solid #dcecdf;
    border-radius: 999px;
    padding: 4px 11px;
    font-size: .78rem;
    font-weight: 800;
    letter-spacing: .04em;
    margin: 8px 0 2px;
}
.count-row {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    align-items: center;
    gap: 3px;
    font-size: 2.55rem;
    line-height: 1.2;
    letter-spacing: 1px;
    padding: 4px 0 2px;
}
.listen-area { margin: 2px 0 8px; }
.listen-area [data-testid="stButton"] button {
    min-height: 3.1rem;
    border-radius: 16px;
    background: #fff7e9;
    border-color: #f0d8a9;
    color: #8b642d;
    box-shadow: 0 3px 0 #f1e1c0;
}
.learn-caption {
    display: inline-block;
    margin-top: 4px;
    font-size: .78rem;
    letter-spacing: .03em;
    color: #7d9587;
    background: #f2f8f3;
    border-radius: 999px;
    padding: 3px 9px;
}
.feedback {
    border-radius: 20px;
    padding: 14px 15px;
    margin-top: 13px;
    animation: pop .3s ease-out;
}
.feedback.correct { background: linear-gradient(135deg, #fff9e8, #f1faf2); border: 1px solid #edd8a4; }
.feedback.wrong { background: #fff8f8; border: 1px dashed #efc3cc; }
.feedback.partial { background: #f5fbf7; border: 1px solid #d9ecdf; }
.feedback-title { font-size: 1.13rem; font-weight: 900; color: #76533e; margin-bottom: 2px; }
.feedback.wrong .feedback-title { color: #a06070; }
.feedback.partial .feedback-title { color: #557b65; }
.feedback-detail { color: #806e77; font-size: .88rem; line-height: 1.55; }
.feedback-detail .learn-caption { margin-top: 5px; }

/* 完成 & 奖状 */
.complete-card {
    text-align: center;
    background:
        radial-gradient(circle at 8% 0%, rgba(255, 228, 177, .62), transparent 28%),
        radial-gradient(circle at 96% 10%, rgba(251, 200, 213, .55), transparent 28%),
        rgba(255, 253, 248, .96);
    border: 1px solid #f1dbc1;
    border-radius: 28px;
    padding: 26px 18px 20px;
    box-shadow: 0 18px 40px rgba(177, 117, 129, .12);
    margin: 6px 0 14px;
}
.complete-emoji { font-size: 3.5rem; line-height: 1.1; animation: bob 2.8s ease-in-out infinite; }
.complete-title { font-size: 1.65rem; font-weight: 900; color: #a9576c; margin: 6px 0 2px; }
.complete-sub { color: #8b747e; font-size: .9rem; margin: 3px 0 10px; }
.complete-stars {
    display: inline-block;
    background: #fff8e7;
    border: 1px solid #efdbb5;
    border-radius: 999px;
    padding: 6px 13px;
    font-size: .86rem;
    font-weight: 800;
    color: #98732e;
}
.complete-badge {
    margin: 14px 0 0;
    padding: 11px 12px;
    background: #fff7f9;
    border-radius: 16px;
    color: #9b5f70;
    font-size: .86rem;
    line-height: 1.55;
}
.cert-note { text-align: center; color: #a88c92; font-size: .76rem; margin: 2px 0 10px; }
.certificate {
    position: relative;
    overflow: hidden;
    text-align: center;
    border-radius: 26px;
    padding: 20px 17px 16px;
    border: 2px solid #e8c98e;
    background:
        radial-gradient(circle at 4% 4%, rgba(255, 222, 166, .78), transparent 23%),
        radial-gradient(circle at 98% 7%, rgba(255, 205, 220, .6), transparent 24%),
        radial-gradient(circle at 0% 100%, rgba(255, 226, 232, .52), transparent 26%),
        linear-gradient(160deg, #fffdf8 0%, #fffaf0 56%, #fff8f9 100%);
    box-shadow: 0 0 0 6px #fffdf8, 0 0 0 7px #f0d8ae, 0 18px 44px rgba(164, 115, 70, .15);
    margin: 8px 0 14px;
}
.cert-corner { position: absolute; font-size: 1.05rem; opacity: .64; }
.cert-corner.tl { left: 12px; top: 12px; }
.cert-corner.tr { right: 12px; top: 12px; }
.cert-corner.bl { left: 12px; bottom: 12px; }
.cert-corner.br { right: 12px; bottom: 12px; }
.cert-seal {
    width: 48px; height: 48px;
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto 4px;
    border-radius: 50%;
    font-size: 1.6rem;
    background: linear-gradient(135deg, #fff3cf, #f7df9f);
    border: 1px solid #e6c176;
    box-shadow: 0 4px 12px rgba(189, 146, 67, .16);
}
.cert-title {
    margin: 2px 0 0;
    color: #7d5b32;
    font-size: 1.47rem;
    letter-spacing: .1em;
    font-weight: 900;
}
.cert-name {
    font-size: 1.95rem;
    font-weight: 900;
    color: #c95875;
    line-height: 1.28;
    margin: 3px 0 1px;
}
.cert-desc {
    color: #8f786c;
    font-size: .79rem;
    line-height: 1.55;
    margin: 2px auto 9px;
    max-width: 21rem;
}
.cert-stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 6px;
    background: rgba(255, 255, 255, .64);
    border: 1px solid #f0dfbf;
    border-radius: 15px;
    padding: 7px 5px;
    margin: 5px 0 9px;
}
.cert-stat b { display: block; font-size: 1.2rem; color: #9c6d35; line-height: 1.25; }
.cert-stat small { display: block; font-size: .64rem; color: #a38b74; margin-top: 1px; }
.cert-stage {
    display: inline-block;
    background: #fff7e7;
    border: 1px solid #efdbaf;
    border-radius: 999px;
    padding: 4px 11px;
    color: #8d672e;
    font-size: .76rem;
    font-weight: 800;
    margin: 0 0 7px;
}
.cert-wish {
    color: #725b52;
    font-size: .87rem;
    line-height: 1.6;
    margin: 5px auto 8px;
    max-width: 21rem;
}
.cert-footer {
    border-top: 1px dashed #e9d6b8;
    padding-top: 7px;
    color: #a38a73;
    font-size: .67rem;
    letter-spacing: .02em;
}
.small-note { text-align: center; color: #a88c92; font-size: .74rem; margin: 6px 0 0; }

/* 家长面板 */
[data-testid="stExpander"] {
    border-radius: 18px;
    border: 1px solid #eedfe1;
    background: rgba(255, 253, 250, .8);
    overflow: hidden;
}
[data-testid="stExpander"] summary { font-weight: 700; color: #765c69; }
[data-testid="stExpander"] p { color: #75636e; font-size: .82rem; }
[data-testid="stExpander"] [data-testid="stMetricValue"] { font-size: 1.3rem; color: #a4536a; }
[data-testid="stExpander"] [data-testid="stMetricLabel"] { color: #8e7a83; font-size: .72rem; }
[data-testid="stExpander"] .stButton button { min-height: 2.6rem; font-size: .86rem; }
[data-testid="stExpander"] table { font-size: .76rem; }
[data-testid="stExpander"] h4 { margin: .2rem 0 .35rem; font-size: .9rem; color: #725863; }
[data-testid="stAlert"] { font-size: .82rem; border-radius: 14px; }

/* 音效播放器藏起来，只留声音 */
[class*="st-key-sfx_"] {
    position: absolute !important;
    width: 1px !important;
    height: 1px !important;
    overflow: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
}

@keyframes bob {
    0%, 100% { transform: translateY(0) rotate(-1deg); }
    50% { transform: translateY(-7px) rotate(1deg); }
}
@keyframes floaty {
    0%, 100% { transform: translateY(0) rotate(-2deg); }
    50% { transform: translateY(-10px) rotate(2deg); }
}
@keyframes pop {
    0% { opacity: 0; transform: scale(.97) translateY(4px); }
    100% { opacity: 1; transform: scale(1) translateY(0); }
}

@media (max-width: 420px) {
    .block-container { padding-left: .75rem; padding-right: .75rem; }
    .hero { padding: 25px 16px 20px; border-radius: 26px; }
    .hero h1 { font-size: 2.12rem; }
    .hero-cake { font-size: 3.4rem; }
    .st-key-emoji_opts button, .st-key-english_opts button, .st-key-action_opts button { min-height: 5.9rem; font-size: 3.55rem; }
    .st-key-animal_opts button, .st-key-shape_opts button { min-height: 5.9rem; }
    .st-key-memory_opts button { min-height: 5.4rem; font-size: 2.95rem; }
    .certificate { padding-left: 13px; padding-right: 13px; }
    .cert-name { font-size: 1.8rem; }
    .cert-title { font-size: 1.35rem; }
    .cert-stats { gap: 3px; }
    .cert-stat b { font-size: 1.1rem; }
}
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { animation-duration: .001ms !important; animation-iteration-count: 1 !important; transition-duration: .001ms !important; }
}
</style>
"""


# ---------------------------------------------------------------------------
# 3. 状态与通用小工具
# ---------------------------------------------------------------------------


def _fresh_level_progress() -> dict:
    return {"stars": 0, "completed": False}


def _fresh_stage_progress() -> dict:
    return {
        "levels": {level["id"]: _fresh_level_progress() for level in LEVELS},
        "correct": 0,
        "wrong": 0,
        "level_stats": {
            level["id"]: {"correct": 0, "wrong": 0} for level in LEVELS
        },
    }


def _fresh_progress() -> dict:
    return {stage_id: _fresh_stage_progress() for stage_id in STAGES}


def init_state() -> None:
    ss = st.session_state
    if "progress" not in ss:
        ss.progress = _fresh_progress()
    if "current_stage" not in ss or ss.current_stage not in STAGES:
        ss.current_stage = 2
    if "screen" not in ss:
        ss.screen = "welcome"
    if "current_level" not in ss:
        ss.current_level = None
    if "level_state" not in ss:
        ss.level_state = None
    if "settings" not in ss:
        ss.settings = {
            "sound": True,
            "english_audio": True,
            "english_caption": True,
        }
    if "read_aloud_by_stage" not in ss:
        ss.read_aloud_by_stage = {
            stage_id: bool(cfg["read_aloud_default"]) for stage_id, cfg in STAGES.items()
        }
    if "stage_locked" not in ss:
        ss.stage_locked = False
    if "just_started" not in ss:
        ss.just_started = False
    if "wished" not in ss:
        ss.wished = False
    if "session_started" not in ss:
        ss.session_started = time.time()
    if "cert_celebrated" not in ss:
        ss.cert_celebrated = False
    if "awaiting_reset" not in ss:
        ss.awaiting_reset = False


def stage_conf(stage_id: int | None = None) -> dict:
    return STAGES[stage_id or st.session_state.current_stage]


def stage_progress(stage_id: int | None = None) -> dict:
    return st.session_state.progress[stage_id or st.session_state.current_stage]


def level_config(level_id: int) -> dict:
    return LEVELS[level_id - 1]


def level_progress(level_id: int, stage_id: int | None = None) -> dict:
    stage_id = stage_id or st.session_state.current_stage
    return st.session_state.progress[stage_id]["levels"][level_id]


def level_star_cap(level_id: int, stage_id: int | None = None) -> int:
    stage_id = stage_id or st.session_state.current_stage
    cfg = STAGES[stage_id]
    if level_id == 6:
        return cfg["memory_pairs"] * cfg["memory_rounds"]
    return cfg["questions"]


def stage_stars(stage_id: int | None = None) -> int:
    prog = stage_progress(stage_id)
    return sum(item["stars"] for item in prog["levels"].values())


def total_stars() -> int:
    return sum(stage_stars(sid) for sid in STAGES)


def stage_completed_levels(stage_id: int | None = None) -> int:
    prog = stage_progress(stage_id)
    return sum(1 for item in prog["levels"].values() if item["completed"])


def next_incomplete_level(stage_id: int | None = None) -> int | None:
    prog = stage_progress(stage_id)
    for level in LEVELS:
        if not prog["levels"][level["id"]]["completed"]:
            return level["id"]
    return None


def stage_is_complete(stage_id: int | None = None) -> bool:
    return next_incomplete_level(stage_id) is None


def record_answer(correct: bool) -> None:
    prog = stage_progress()
    level_id = st.session_state.current_level
    if level_id is None:
        return
    if correct:
        prog["correct"] += 1
        prog["level_stats"][level_id]["correct"] += 1
    else:
        prog["wrong"] += 1
        prog["level_stats"][level_id]["wrong"] += 1


def award_star() -> bool:
    level_id = st.session_state.current_level
    if level_id is None:
        return False
    prog = level_progress(level_id)
    cap = level_star_cap(level_id)
    if prog["stars"] >= cap:
        return False
    prog["stars"] += 1
    return True


def mark_level_complete() -> None:
    level_id = st.session_state.current_level
    if level_id is not None:
        level_progress(level_id)["completed"] = True


def reset_current_stage() -> None:
    stage_id = st.session_state.current_stage
    st.session_state.progress[stage_id] = _fresh_stage_progress()
    st.session_state.screen = "welcome"
    st.session_state.current_level = None
    st.session_state.level_state = None
    st.session_state.cert_celebrated = False
    st.session_state.wished = False


def reset_all_progress() -> None:
    st.session_state.progress = _fresh_progress()
    st.session_state.screen = "welcome"
    st.session_state.current_level = None
    st.session_state.level_state = None
    st.session_state.cert_celebrated = False
    st.session_state.wished = False
    st.session_state.just_started = False
    st.session_state.session_started = time.time()
    st.session_state.awaiting_reset = False


def local_now() -> datetime:
    try:
        return datetime.now(ZoneInfo(APP_CONFIG["timezone"]))
    except Exception:
        return datetime.now()


def date_cn(moment: datetime) -> str:
    return f"{moment.year}年{moment.month}月{moment.day}日"


def date_short_cn(moment: datetime) -> str:
    return f"{moment.month}月{moment.day}日"


WEEKDAYS_CN = ["一", "二", "三", "四", "五", "六", "日"]


def birthday_status(moment: datetime) -> tuple[str, int, date | None]:
    """返回 (状态, 距离天数, 今年生日日期)。"""
    try:
        month = int(APP_CONFIG["birthday_month"])
        day = int(APP_CONFIG["birthday_day"])
        birthday = date(moment.year, month, day)
    except (KeyError, TypeError, ValueError):
        return "unknown", 0, None
    today = moment.date()
    if today == birthday:
        return "today", 0, birthday
    if today < birthday:
        days = (birthday - today).days
        return ("tomorrow" if days == 1 else "upcoming"), days, birthday
    try:
        next_birthday = date(moment.year + 1, month, day)
    except ValueError:
        return "passed", 0, birthday
    return "passed", (next_birthday - today).days, next_birthday


def birthday_label() -> str:
    try:
        return f"{int(APP_CONFIG['birthday_month'])}月{int(APP_CONFIG['birthday_day'])}日"
    except (KeyError, TypeError, ValueError):
        return "生日"


def birthday_egg_lines(moment: datetime) -> tuple[str, str]:
    status, days, _ = birthday_status(moment)
    main = f"📅 今天是 {date_short_cn(moment)} · 星期{WEEKDAYS_CN[moment.weekday()]}"
    label = birthday_label()
    if status == "today":
        sub = f"🎂 今天就是 {label} 生日，生日快乐！"
    elif status == "tomorrow":
        sub = f"🎈 明天就是 {label} 生日啦"
    elif status == "upcoming":
        sub = f"🎈 距离 {label} 生日还有 {days} 天"
    elif status == "passed":
        sub = f"🎈 生日是 {label}，快乐不只在一天"
    else:
        sub = "🎈 今天也要开心"
    return main, sub


def birthday_footer_text(moment: datetime) -> str:
    status, days, _ = birthday_status(moment)
    if status == "today":
        return "生日快乐"
    if status == "tomorrow":
        return "明天就是生日 · 提前庆生"
    if status == "upcoming":
        return f"距离生日还有 {days} 天 · 提前庆生"
    if status == "passed":
        return "生日祝福一直有效"
    return "生日快乐"


def seconds_text(seconds: float) -> str:
    seconds = max(0, int(seconds))
    if seconds < 60:
        return "不到 1 分钟"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} 分钟"
    return f"{minutes // 60} 小时 {minutes % 60} 分钟"


def clock_text(seconds: float) -> str:
    seconds = max(0, int(seconds))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def word_slug(word: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", word.lower()).strip("_")


def find_audio(word: str) -> Path | None:
    audio_dir = BASE_DIR / APP_CONFIG["audio_dir"]
    slug = word_slug(word)
    for ext in (".wav", ".mp3", ".m4a", ".ogg", ".opus"):
        candidate = audio_dir / f"{slug}{ext}"
        if candidate.exists():
            return candidate
    return None


def audio_mime(path: Path) -> str:
    return mimetypes.guess_type(path.name)[0] or "audio/wav"


def play_chime(name: str, token: int) -> None:
    if not st.session_state.settings.get("sound", True):
        return
    path = BASE_DIR / APP_CONFIG["audio_dir"] / f"{name}.wav"
    if not path.exists():
        return
    try:
        with st.container(key=f"sfx_{name}_{token}"):
            st.audio(path.read_bytes(), format="audio/wav", autoplay=True)
    except Exception:
        # 没有音效文件、浏览器不支持播放都不该影响游戏
        pass


def speak_web(text: str, lang: str) -> None:
    """可选兜底：用浏览器自带的朗读，只在用户点按钮后调用。"""
    text_js = json.dumps(text, ensure_ascii=False)
    lang_js = json.dumps(lang)
    st.html(
        f"""
        <div style="display:none"></div>
        <script>
        (function() {{
            try {{
                if (!("speechSynthesis" in window)) return;
                window.speechSynthesis.cancel();
                const utter = new SpeechSynthesisUtterance({text_js});
                utter.lang = {lang_js};
                utter.rate = 0.84;
                utter.pitch = 1.04;
                window.speechSynthesis.speak(utter);
            }} catch (err) {{}}
        }})();
        </script>
        """,
        unsafe_allow_javascript=True,
    )


def safe_html(value: str) -> str:
    import html as html_module

    return html_module.escape(value)


# ---------------------------------------------------------------------------
# 4. 出题逻辑（每道题只生成一次，点按钮不会重新洗牌）
# ---------------------------------------------------------------------------


def _new_token(level_state: dict) -> int:
    level_state["token"] = int(level_state.get("token", 0)) + 1
    return level_state["token"]


def make_question(level_id: int, level_state: dict) -> dict:
    cfg = stage_conf()
    if level_id == 1:
        return _make_color_question(level_state, cfg)
    if level_id == 2:
        return _make_counting_question(level_state, cfg)
    if level_id == 3:
        return _make_shape_question(level_state, cfg)
    if level_id == 4:
        return _make_animal_question(level_state, cfg)
    if level_id == 5:
        return _make_english_question(level_state, cfg)
    raise ValueError("记忆翻牌不使用出题器")


def _make_color_question(level_state: dict, cfg: dict) -> dict:
    token = _new_token(level_state)
    multi = bool(cfg["multi"]) and level_state["q_num"] % 2 == 0

    if multi:
        group = random.choice(COLOR_GROUPS)
        targets = [item for item in COLOR_ITEMS if item["color_key"] == group["key"]]
        others = [item for item in COLOR_ITEMS if item["color_key"] != group["key"]]
        extra_count = max(0, int(cfg["options"]) - len(targets))
        options_items = targets + random.sample(others, min(extra_count, len(others)))
        random.shuffle(options_items)
        return {
            "token": token,
            "kind": "color_multi",
            "prompt": f"找出所有{group['cn']}的东西",
            "subtitle": "可以点好几下，全部找齐才算过关哦",
            "hint": f"把{group['cn']}的东西都找出来，可能不止一个",
            "gentle_hint": f"再看看，还有没有{group['cn']}的？",
            "options": [
                {"id": item["id"], "label": item["emoji"]} for item in options_items
            ],
            "target_ids": [item["id"] for item in targets],
            "found": [],
            "caption": f"{group['cn']} {group['en']}",
        }

    target = random.choice(COLOR_ITEMS)
    distractors = [
        item for item in COLOR_ITEMS if item["color_key"] != target["color_key"]
    ]
    option_count = max(1, min(int(cfg["options"]), 1 + len(distractors)))
    options_items = [target] + random.sample(distractors, option_count - 1)
    random.shuffle(options_items)
    return {
        "token": token,
        "kind": "color_single",
        "prompt": f"点一点{target['color_cn']}的{target['name_cn']}",
        "subtitle": "看一看颜色，再点一点",
        "hint": f"找一找{target['color_cn']}的{target['name_cn']}",
        "gentle_hint": "再找一找，不着急～",
        "options": [{"id": item["id"], "label": item["emoji"]} for item in options_items],
        "answer_id": target["id"],
        "caption": f"{target['color_cn']} {target['color_en']}",
    }


def _make_counting_question(level_state: dict, cfg: dict) -> dict:
    token = _new_token(level_state)
    max_number = int(cfg["counting_max"])
    theme = COUNT_THEMES[0] if max_number <= 5 else random.choice(COUNT_THEMES)
    count = random.randint(1, max_number)
    options = [
        {"id": str(number), "label": str(number)} for number in range(1, max_number + 1)
    ]
    number_word = EN_NUMBER_BY_VALUE.get(count)
    return {
        "token": token,
        "kind": "counting",
        "prompt": f"数一数，有几{theme['unit']}{theme['name']}？",
        "subtitle": "用小手指着，一个一个数",
        "hint": "用小手指着，一个一个数，数到几就是几个",
        "gentle_hint": "再数一数，不着急～",
        "options": options,
        "answer_id": str(count),
        "count": count,
        "count_emoji": theme["emoji"],
        "caption": f"{number_word['word']} {count}" if number_word else "",
    }


def _make_shape_question(level_state: dict, cfg: dict) -> dict:
    token = _new_token(level_state)
    shape_pool = SHAPES[:4] if int(cfg["shape_options"]) <= 4 else SHAPES
    target = random.choice(shape_pool)
    option_count = max(2, min(int(cfg["shape_options"]), len(shape_pool)))
    others = [shape for shape in shape_pool if shape["id"] != target["id"]]
    options = [target] + random.sample(others, option_count - 1)
    random.shuffle(options)
    return {
        "token": token,
        "kind": "shape",
        "prompt": f"哪个是{target['cn']}？",
        "subtitle": "看看边和角，找出正确的形状",
        "hint": f"看看哪个是{target['cn']}，注意它的边和角",
        "gentle_hint": "再看看形状，不着急～",
        "options": [{"id": shape["id"], "label": shape["glyph"]} for shape in options],
        "answer_id": target["id"],
        "caption": "",
    }


def _make_animal_question(level_state: dict, cfg: dict) -> dict:
    token = _new_token(level_state)
    target = random.choice(ANIMALS)
    grid_size = min(int(cfg["animal_grid"]), len(ANIMALS))
    others = [animal for animal in ANIMALS if animal["id"] != target["id"]]
    options = [target] + random.sample(others, grid_size - 1)
    random.shuffle(options)
    return {
        "token": token,
        "kind": "animal",
        "prompt": f"哪一只是{target['cn']}？",
        "subtitle": "仔细看看小动物的样子",
        "hint": f"找找{target['cn']}，看看耳朵、尾巴和叫声",
        "gentle_hint": "再找一找，不着急～",
        "options": [{"id": item["id"], "label": item["emoji"]} for item in options],
        "answer_id": target["id"],
        "columns": int(cfg["animal_columns"]),
        "caption": f"{target['en']} {target['cn']}",
    }


def _make_english_question(level_state: dict, cfg: dict) -> dict:
    token = _new_token(level_state)
    use_action = bool(cfg["english_actions"]) and level_state["q_num"] % 2 == 0

    if use_action:
        pool = EN_ACTIONS
        target = random.choice(pool)
        option_count = max(2, min(int(cfg["english_options"]), len(pool)))
        others = [item for item in pool if item["id"] != target["id"]]
        options = [target] + random.sample(others, option_count - 1)
        random.shuffle(options)
        return {
            "token": token,
            "kind": "english_action",
            "prompt": "听一听，选出对应的动作",
            "subtitle": "先点小喇叭，听完再做选择",
            "hint": f"是「{target['cn']}」的动作",
            "gentle_hint": "再听一听，不着急～",
            "options": [{"id": item["id"], "label": item["emoji"]} for item in options],
            "answer_id": target["id"],
            "word": target["word"],
            "word_cn": target["cn"],
            "caption": f"{target['word']} {target['cn']}",
            "columns": 2 if len(options) <= 4 else 3,
        }

    categories = ["colors", "animals"]
    if cfg["english_numbers"]:
        categories.append("numbers")
    category = random.choice(categories)
    if category == "colors":
        pool = EN_COLORS
    elif category == "animals":
        pool = EN_ANIMALS
    else:
        pool = EN_NUMBERS[: int(cfg["number_max"])]
    target = random.choice(pool)
    option_count = max(2, min(int(cfg["english_options"]), len(pool)))
    others = [item for item in pool if item["id"] != target["id"]]
    options = [target] + random.sample(others, option_count - 1)
    random.shuffle(options)
    return {
        "token": token,
        "kind": "english_listen",
        "prompt": "听一听，选出你听到的图片",
        "subtitle": "先点小喇叭，听完再选",
        "hint": f"这个单词是「{target['cn']}」",
        "gentle_hint": "再听一听，不着急～",
        "options": [{"id": item["id"], "label": item["emoji"]} for item in options],
        "answer_id": target["id"],
        "word": target["word"],
        "word_cn": target["cn"],
        "caption": f"{target['word']} {target['cn']}",
        "columns": 2 if len(options) <= 4 else 3,
    }


# ---------------------------------------------------------------------------
# 5. 关卡状态
# ---------------------------------------------------------------------------


def start_level(level_id: int) -> None:
    level_state = {
        "level": level_id,
        "q_num": 1,
        "answered": 0,
        "done": False,
        "feedback": None,
        "token": 0,
        "celebrated": False,
        "sfx": None,
        "question": None,
        "memory": None,
    }
    st.session_state.current_level = level_id
    st.session_state.level_state = level_state
    st.session_state.screen = "level"
    if level_id == 6:
        _init_memory(level_state)
    else:
        level_state["question"] = make_question(level_id, level_state)
    st.rerun()


def _new_memory_deck(pairs: int) -> list[dict]:
    theme = random.choice(MEMORY_THEMES)
    chosen = theme[:pairs]
    cards = []
    for pair_index, emoji in enumerate(chosen):
        cards.append({"pair": pair_index, "emoji": emoji})
        cards.append({"pair": pair_index, "emoji": emoji})
    random.shuffle(cards)
    return cards


def _deal_memory_round(level_state: dict) -> None:
    mem = level_state["memory"]
    mem["deck"] = _new_memory_deck(int(mem["pairs"]))
    mem["revealed"] = []
    mem["matched"] = []
    mem["first"] = None
    mem["mismatch"] = None
    mem["round_done"] = False
    mem["note"] = None
    mem["note_kind"] = None
    mem["deal_id"] = _new_token(level_state)


def _init_memory(level_state: dict) -> None:
    cfg = stage_conf()
    level_state["memory"] = {
        "round": 1,
        "max_rounds": int(cfg["memory_rounds"]),
        "pairs": int(cfg["memory_pairs"]),
        "deck": [],
        "revealed": [],
        "matched": [],
        "first": None,
        "mismatch": None,
        "round_done": False,
        "note": None,
        "note_kind": None,
        "deal_id": 0,
    }
    _deal_memory_round(level_state)


def _caption_for(question: dict) -> str:
    if not st.session_state.settings.get("english_caption", True):
        return ""
    return question.get("caption", "")


def _consume_sfx(level_state: dict) -> None:
    sfx = level_state.get("sfx")
    if not sfx:
        return
    level_state["sfx"] = None
    play_chime(sfx, int(level_state.get("token", 0)))


def _finish_level(level_state: dict) -> None:
    level_state["done"] = True
    level_state["feedback"] = None
    level_state["celebrated"] = False
    level_state["sfx"] = "win"
    mark_level_complete()


def _handle_correct(level_state: dict, detail: str = "") -> None:
    star = award_star()
    record_answer(True)
    level_state["answered"] = int(level_state.get("answered", 0)) + 1
    caption = detail or _caption_for(level_state.get("question") or {})
    bits: list[str] = []
    if star:
        bits.append("又收集到一颗星星 ⭐")
    else:
        bits.append("这一关的星星已经收好啦，复习也很棒！")
    if caption:
        bits.append(f'<span class="learn-caption">{safe_html(caption)}</span>')
    cfg = stage_conf()
    if level_state["answered"] >= int(cfg["questions"]):
        _finish_level(level_state)
    else:
        level_state["feedback"] = {
            "kind": "correct",
            "title": random.choice(CORRECT_PRAISE),
            "detail": " ".join(bits),
        }
        level_state["sfx"] = "correct"
    st.rerun()


def _wrong_hint(level_state: dict) -> str:
    cfg = stage_conf()
    question = level_state.get("question") or {}
    if cfg["hint_mode"] == "specific":
        return question.get("hint", "再试一次～")
    if cfg["hint_mode"] == "gentle":
        return question.get("gentle_hint", "再试试看～")
    return "再试一次～"


def _handle_wrong(level_state: dict, extra: str = "") -> None:
    record_answer(False)
    cfg = stage_conf()
    if cfg["hint_mode"] == "minimal":
        hint = "再试一次～"
    else:
        hint = extra or _wrong_hint(level_state)
    level_state["feedback"] = {
        "kind": "wrong",
        "title": random.choice(WRONG_PRAISE),
        "detail": hint,
    }
    level_state["sfx"] = "wrong"
    st.rerun()


def _handle_multi_click(level_state: dict, option_id: str) -> None:
    question = level_state.get("question") or {}
    target_ids = set(question.get("target_ids", []))
    found = question.setdefault("found", [])
    if option_id in found:
        return
    if option_id in target_ids:
        found.append(option_id)
        remaining = [target for target in target_ids if target not in found]
        if not remaining:
            _handle_correct(level_state)
        else:
            level_state["feedback"] = {
                "kind": "partial",
                "title": "找到一个啦！",
                "detail": f"还有 {len(remaining)} 个，再找找看～",
            }
            st.rerun()
    else:
        color_text = ""
        # 从选项里找颜色提示，让回答更温和
        for group in COLOR_GROUPS:
            if any(item["id"] == option_id for item in group["items"]):
                color_text = group["cn"]
                break
        _handle_wrong(
            level_state,
            f"这个不是{color_text or '目标颜色'}的，再找找～" if color_text else "",
        )


def _advance_question(level_state: dict) -> None:
    level_state["feedback"] = None
    level_state["q_num"] = int(level_state["q_num"]) + 1
    level_state["wrong_this_q"] = 0
    level_state["question"] = make_question(int(level_state["level"]), level_state)
    st.rerun()


# ---------------------------------------------------------------------------
# 6. 页面组件
# ---------------------------------------------------------------------------


def render_topbar() -> None:
    stage_id = st.session_state.current_stage
    cfg = STAGES[stage_id]
    completed = stage_completed_levels()
    partial = 0.0
    level_state = st.session_state.level_state

    if (
        st.session_state.screen == "level"
        and level_state
        and not stage_progress()["levels"][level_state["level"]]["completed"]
    ):
        level_id = int(level_state["level"])
        if level_id == 6 and level_state.get("memory"):
            mem = level_state["memory"]
            pairs = max(1, int(mem["pairs"]))
            rounds = max(1, int(mem["max_rounds"]))
            matched_pairs = len(mem["matched"]) // 2
            partial = ((int(mem["round"]) - 1) + matched_pairs / pairs) / rounds
        elif level_state.get("question"):
            partial = int(level_state.get("answered", 0)) / max(1, int(cfg["questions"]))

    overall = min(1.0, (completed + partial) / 6.0)
    pct = int(round(overall * 100))

    if st.session_state.screen == "level" and st.session_state.current_level:
        level_no = int(st.session_state.current_level)
        level_meta = f"第 {level_no}/6 关"
    else:
        focus = next_incomplete_level() or 6
        level_meta = f"第 {focus}/6 关"

    q_meta = "选一关开始吧"
    if st.session_state.screen == "level" and level_state:
        level_id = int(level_state["level"])
        if level_state.get("done"):
            q_meta = "本关完成"
        elif level_id == 6 and level_state.get("memory"):
            mem = level_state["memory"]
            q_meta = f"本关第 {mem['round']}/{mem['max_rounds']} 轮"
        else:
            q_meta = f"本关第 {level_state.get('q_num', 1)}/{cfg['questions']} 题"

    timer_html = ""
    if cfg["show_timer"]:
        elapsed = clock_text(time.time() - st.session_state.session_started)
        timer_html = f'<span>⏱ {elapsed}</span>'

    st.markdown(
        f"""
        <div class="topbar">
            <div class="topbar-row">
                <span class="chip">{cfg['badge']} 当前阶段：{cfg['name']}</span>
                <span class="chip star">本阶段 ⭐{stage_stars()}</span>
                <span class="chip total">总 ⭐{total_stars()}</span>
            </div>
            <div class="progress-track" role="progressbar" aria-valuenow="{pct}" aria-valuemin="0" aria-valuemax="100">
                <span class="progress-fill" style="width:{pct}%"></span>
            </div>
            <div class="topmeta">
                <span>{level_meta}</span>
                <span>{q_meta}</span>
                <span class="spacer"></span>{timer_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_prompt(question: dict, level_state: dict) -> None:
    st.markdown(
        f"""
        <div class="prompt-card">
            <p class="prompt-text">{safe_html(question['prompt'])}</p>
            <p class="prompt-sub">{safe_html(question.get('subtitle', ''))}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cfg = stage_conf()
    read_on = st.session_state.read_aloud_by_stage.get(st.session_state.current_stage, False)
    if read_on:
        with st.container(key="read_prompt"):
            if st.button("🔊 读题", key=f"read_{level_state['token']}"):
                speak_web(question["prompt"], "zh-CN")


def render_counting_visual(question: dict) -> None:
    count = int(question.get("count", 0))
    emoji = question.get("count_emoji", "🕯️")
    visual = "".join(emoji for _ in range(count))
    st.markdown(f'<div class="count-row">{visual}</div>', unsafe_allow_html=True)


def render_listen_area(question: dict, level_state: dict) -> None:
    word = question.get("word", "")
    word_cn = question.get("word_cn", "")
    st.markdown(
        f'<div style="text-align:center"><span class="word-chip">🔤 {safe_html(word)}</span></div>',
        unsafe_allow_html=True,
    )
    if not word:
        return
    path = find_audio(word)
    with st.container(key="listen_area"):
        if not st.session_state.settings.get("english_audio", True):
            st.info(f"英语发音已关闭 · 单词 **{word}**（{word_cn}）")
            return
        if path:
            if st.button("🔊 听一听", key=f"listen_{level_state['token']}_{word_slug(word)}", use_container_width=True):
                try:
                    st.audio(path.read_bytes(), format=audio_mime(path), autoplay=True)
                    st.caption("没听清的话，再点播放器的 ▶ 听一次。")
                except Exception:
                    st.info(f"播放没成功，单词是 **{word}**（{word_cn}）。")
        else:
            st.info(f"这里还没有录音 · 单词 **{word}**（{word_cn}）")
            if st.button("🔊 听一听（电脑朗读）", key=f"tts_{level_state['token']}_{word_slug(word)}", use_container_width=True):
                speak_web(word, "en-US")


def _render_button_grid(
    options: list[dict],
    columns: int,
    container_key: str,
    on_click,
    disabled_ids: set[str] | None = None,
    checked_ids: set[str] | None = None,
) -> None:
    disabled_ids = disabled_ids or set()
    checked_ids = checked_ids or set()
    with st.container(key=container_key):
        for start in range(0, len(options), columns):
            row = st.columns(columns, wrap=False)
            for index, option in enumerate(options[start : start + columns]):
                with row[index]:
                    label = option["label"]
                    if option["id"] in checked_ids:
                        label = f"{label} ✓"
                    clicked = st.button(
                        label,
                        key=f"opt_{container_key}_{option['id']}",
                        use_container_width=True,
                        disabled=option["id"] in disabled_ids,
                    )
                    if clicked:
                        on_click(option["id"])


def render_options(question: dict, level_state: dict) -> None:
    kind = question.get("kind", "")
    options = question.get("options", [])
    if kind == "color_multi":
        found = set(question.get("found", []))
        _render_button_grid(
            options,
            columns=2,
            container_key="emoji_opts",
            on_click=lambda option_id: _handle_multi_click(level_state, option_id),
            disabled_ids=found,
            checked_ids=found,
        )
        return

    def on_single(option_id: str) -> None:
        if option_id == question.get("answer_id"):
            _handle_correct(level_state)
        else:
            _handle_wrong(level_state)

    if kind == "counting":
        columns = 5 if len(options) > 5 else max(1, len(options))
        _render_button_grid(options, columns, "number_opts", on_single)
    elif kind == "shape":
        _render_button_grid(options, 2, "shape_opts", on_single)
    elif kind == "animal":
        _render_button_grid(options, int(question.get("columns", 3)), "animal_opts", on_single)
    elif kind == "english_action":
        _render_button_grid(
            options, int(question.get("columns", 3)), "action_opts", on_single
        )
    elif kind == "english_listen":
        _render_button_grid(
            options, int(question.get("columns", 2)), "english_opts", on_single
        )
    else:
        _render_button_grid(options, 2, "emoji_opts", on_single)


def _feedback_html(feedback: dict) -> str:
    kind = feedback.get("kind", "wrong")
    title = safe_html(feedback.get("title", ""))
    detail = feedback.get("detail", "")
    # detail 里的英文小字标签是我们自己生成的；普通文字先转义，再还原标签
    if "<span class=\"learn-caption\">" in detail:
        prefix, _, rest = detail.partition('<span class="learn-caption">')
        caption, _, _ = rest.partition("</span>")
        detail_html = f'{safe_html(prefix)}<span class="learn-caption">{safe_html(caption)}</span>'
    else:
        detail_html = safe_html(detail)
    return (
        f'<div class="feedback {kind}">'
        f'<div class="feedback-title">{title}</div>'
        f'<div class="feedback-detail">{detail_html}</div>'
        f"</div>"
    )


def render_feedback(level_state: dict) -> None:
    feedback = level_state.get("feedback")
    if not feedback:
        return
    _consume_sfx(level_state)
    st.markdown(_feedback_html(feedback), unsafe_allow_html=True)
    if feedback["kind"] == "correct":
        if st.button("下一题 →", type="primary", key=f"next_{level_state['token']}", use_container_width=True):
            _advance_question(level_state)


def render_level_page() -> None:
    level_state = st.session_state.level_state
    if not level_state:
        st.session_state.screen = "map"
        st.rerun()
        return

    render_topbar()
    with st.container(key="top_nav"):
        if st.button("← 关卡地图", key="back_to_map"):
            st.session_state.screen = "map"
            st.session_state.current_level = None
            st.session_state.level_state = None
            st.rerun()

    level_id = int(level_state["level"])
    level = level_config(level_id)
    cfg = stage_conf()
    if level_id == 6:
        mem = level_state.get("memory") or {}
        sub = f"第 {level_state['memory']['round']}/{level_state['memory']['max_rounds']} 轮 · {cfg['memory_pairs']} 对卡片"
    else:
        sub = f"{cfg['questions']} 道小题 · 第 {level_state['q_num']} 题"
    st.markdown(
        f"""
        <div class="level-head">
            <div class="level-icon">{level['icon']}</div>
            <div>
                <div class="level-title" role="heading" aria-level="2">{level['name']}</div>
                <p>第 {level_id} 关 · {sub}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if level_state.get("done"):
        render_completion(level_state)
        render_parent_panel()
        return

    if level_id == 6:
        render_memory(level_state)
        render_parent_panel()
        return

    question = level_state.get("question")
    if not question:
        level_state["question"] = make_question(level_id, level_state)
        st.rerun()
        return

    render_prompt(question, level_state)
    if question["kind"] == "counting":
        render_counting_visual(question)
    if question["kind"] in ("english_listen", "english_action"):
        render_listen_area(question, level_state)

    if (level_state.get("feedback") or {}).get("kind") == "correct":
        render_feedback(level_state)
    else:
        render_options(question, level_state)
        if level_state.get("feedback"):
            render_feedback(level_state)

    render_parent_panel()


def render_memory(level_state: dict) -> None:
    mem = level_state.get("memory")
    if not mem:
        _init_memory(level_state)
        st.rerun()
        return

    _consume_sfx(level_state)
    st.markdown(
        f"""
        <div class="prompt-card">
            <p class="prompt-text">翻开两张一样的卡片</p>
            <p class="prompt-sub">第 {mem['round']}/{mem['max_rounds']} 轮 · 已配对 {len(mem['matched']) // 2}/{mem['pairs']} 对</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    n_cols = max(2, min(4, int(mem["pairs"])))
    with st.container(key="memory_opts"):
        for start in range(0, len(mem["deck"]), n_cols):
            row = st.columns(n_cols, wrap=False)
            for index, card in enumerate(mem["deck"][start : start + n_cols]):
                card_index = start + index
                matched = card_index in mem["matched"]
                revealed = card_index in mem["revealed"]
                mismatch_visible = bool(mem["mismatch"]) and card_index in mem["mismatch"]
                blocked = bool(mem["mismatch"]) or bool(mem["round_done"])
                if matched:
                    label = f"{card['emoji']} ✓"
                elif revealed or mismatch_visible:
                    label = card["emoji"]
                else:
                    label = "❓"
                with row[index]:
                    clicked = st.button(
                        label,
                        key=f"mem_{mem['deal_id']}_{card_index}",
                        use_container_width=True,
                        disabled=matched or revealed or mismatch_visible or blocked,
                    )
                    if clicked:
                        _handle_memory_click(level_state, card_index)

    if mem.get("note"):
        kind = mem.get("note_kind") or "correct"
        st.markdown(
            f'<div class="feedback {kind}"><div class="feedback-title">{safe_html(mem["note"])}</div></div>',
            unsafe_allow_html=True,
        )

    if mem.get("mismatch"):
        if st.button(
            "我记住啦，继续 →",
            type="primary",
            key=f"mem_continue_{mem['deal_id']}",
            use_container_width=True,
        ):
            mem["mismatch"] = None
            mem["revealed"] = []
            mem["note"] = None
            st.rerun()

    if mem.get("round_done") and not level_state.get("done"):
        if st.button(
            "下一轮 →",
            type="primary",
            key=f"mem_next_round_{mem['deal_id']}",
            use_container_width=True,
        ):
            mem["round"] = int(mem["round"]) + 1
            _deal_memory_round(level_state)
            st.rerun()

    with st.container(key="memory_reset"):
        if st.button("🔄 重新翻牌", key=f"mem_reset_{mem['deal_id']}", use_container_width=True):
            level_state["done"] = False
            level_state["answered"] = 0
            level_state["celebrated"] = False
            level_state["sfx"] = None
            level_state["feedback"] = None
            mem["round"] = 1
            mem["round_done"] = False
            _deal_memory_round(level_state)
            st.rerun()


def _handle_memory_click(level_state: dict, card_index: int) -> None:
    mem = level_state["memory"]
    if card_index in mem["matched"] or card_index in mem["revealed"] or mem["mismatch"] or mem["round_done"]:
        return

    if mem["first"] is None:
        mem["first"] = card_index
        mem["revealed"] = [card_index]
        mem["note"] = None
        st.rerun()
        return

    first_index = int(mem["first"])
    mem["first"] = None
    mem["revealed"] = [first_index, card_index]
    first_card = mem["deck"][first_index]
    second_card = mem["deck"][card_index]

    if first_card["pair"] == second_card["pair"]:
        mem["matched"].extend([first_index, card_index])
        record_answer(True)
        star = award_star()
        if len(mem["matched"]) >= len(mem["deck"]):
            mem["round_done"] = True
            if int(mem["round"]) >= int(mem["max_rounds"]):
                _finish_level(level_state)
                st.rerun()
            mem["note"] = "这一轮完成啦！"
            mem["note_kind"] = "correct"
            level_state["sfx"] = "correct"
            st.rerun()
        mem["note"] = "配对成功 +1⭐" if star else "配对成功！星星已经收好啦"
        mem["note_kind"] = "correct"
        level_state["sfx"] = "correct"
        st.rerun()

    mem["mismatch"] = (first_index, card_index)
    mem["revealed"] = [first_index, card_index]
    mem["note"] = "不一样，再记一记～"
    mem["note_kind"] = "wrong"
    level_state["sfx"] = "wrong"
    record_answer(False)
    st.rerun()


def render_completion(level_state: dict) -> None:
    _consume_sfx(level_state)
    if not level_state.get("celebrated"):
        level_state["celebrated"] = True
        st.balloons()
    level_id = int(level_state["level"])
    level = level_config(level_id)
    prog = level_progress(level_id)
    cap = level_star_cap(level_id)
    all_done = stage_is_complete()
    cfg = stage_conf()
    badge_html = ""
    if all_done:
        badge_html = (
            f'<div class="complete-badge">🏅 六关全部完成，获得 '
            f'{cfg["badge"]}「{cfg["name"]}」徽章！</div>'
        )
    st.markdown(
        f"""
        <div class="complete-card">
            <div class="complete-emoji">🎉</div>
            <div class="complete-title">第 {level_id} 关完成！</div>
            <div class="complete-sub">{random.choice(CORRECT_PRAISE)} {level['praise']}</div>
            <div class="complete-stars">本关 ⭐ {prog['stars']} / {cap}</div>{badge_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    back_primary = False
    if all_done:
        if st.button("领取我的奖状 🏆", type="primary", key="to_certificate", use_container_width=True):
            st.session_state.screen = "certificate"
            st.session_state.cert_celebrated = False
            st.rerun()
    elif level_id < 6:
        next_level = level_id + 1
        next_level_info = level_config(next_level)
        if st.button(
            f"下一关 · {next_level_info['icon']} {next_level_info['name']} →",
            type="primary",
            key="next_level",
            use_container_width=True,
        ):
            start_level(next_level)
    else:
        back_primary = True
        st.info("还有几关没有完成，回到地图继续吧，不着急。")

    if st.button(
        "回到关卡地图",
        type="primary" if back_primary else "secondary",
        key=f"back_map_complete_{level_id}",
        use_container_width=True,
    ):
        st.session_state.screen = "map"
        st.session_state.current_level = None
        st.session_state.level_state = None
        st.rerun()


def render_welcome() -> None:
    moment = local_now()
    nickname = APP_CONFIG["nickname"]
    date_main, date_sub = birthday_egg_lines(moment)
    st.markdown(
        f"""
        <div class="hero">
            <span class="hero-balloon b1">🎈</span>
            <span class="hero-balloon b2">🎁</span>
            <span class="hero-balloon b3">✨</span>
            <span class="hero-balloon b4">🎈</span>
            <div class="hero-kicker">A LITTLE BIRTHDAY SURPRISE</div>
            <div class="hero-cake">🎂</div>
            <h1>🎂 生日快乐！</h1>
            <p class="hero-name">{safe_html(nickname)}，今天是你的小主角</p>
            <p class="hero-copy">这是给你准备的小小学习游戏，和爸爸妈妈一起玩吧。</p>
            <div class="date-pill"><span>{date_main}</span><span class="date-sub">{date_sub}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="hero-foot">慢慢玩，不赶时间。今天最重要的任务，是开心。</div>', unsafe_allow_html=True)

    if st.button("开始玩 →", type="primary", key="start_game", use_container_width=True):
        st.session_state.screen = "map"
        st.session_state.just_started = True
        st.rerun()

    if st.button("🕯️ 吹蜡烛，许个愿", key="make_wish", use_container_width=True):
        st.session_state.wished = True
        st.balloons()

    if st.session_state.wished:
        st.markdown(
            '<div class="wish-card">🕯️ 呼——蜡烛吹灭啦。<br>愿望已经藏进蛋糕里，'
            f'<b>{safe_html(nickname)}</b> 今天一定会被好多好多爱围着。</div>',
            unsafe_allow_html=True,
        )
    st.caption("家长可以把最下面的「家长查看」展开，调整难度和声音。")
    render_parent_panel()


def render_map() -> None:
    if st.session_state.get("just_started"):
        st.session_state.just_started = False
        st.balloons()

    render_topbar()
    cfg = stage_conf()
    st.markdown(
        f"""
        <div class="map-head">
            <div class="map-title" role="heading" aria-level="2">今天想先玩哪一关？</div>
            <p>{cfg['badge']} {cfg['name']}阶段 · {cfg['caption']} · 6 个小关卡</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if stage_is_complete():
        st.markdown(
            f"""
            <div class="stage-badge-card">
                <div class="stage-badge-icon">{cfg['badge']}</div>
                <b>获得「{cfg['name']}」徽章！</b>
                <p>六关全部完成，可以领取今天的奖状啦。</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    stage_prog = stage_progress()
    with st.container(key="level_cards"):
        for row_start in range(0, len(LEVELS), 2):
            row = st.columns(2, wrap=False)
            for index, level in enumerate(LEVELS[row_start : row_start + 2]):
                with row[index]:
                    label = f"{level['icon']} {level['name']}"
                    if st.button(
                        label,
                        key=f"level_{level['id']}",
                        use_container_width=True,
                    ):
                        start_level(level["id"])
                    lp = stage_prog["levels"][level["id"]]
                    cap = level_star_cap(level["id"])
                    if lp["completed"]:
                        st.caption(f"✅ 已完成 · ⭐{lp['stars']}/{cap}")
                    else:
                        st.caption(f"⭐{lp['stars']}/{cap} · 去挑战")

    next_level = next_incomplete_level()
    if next_level is None:
        if st.button("查看我的奖状 🏆", type="primary", key="map_certificate", use_container_width=True):
            st.session_state.screen = "certificate"
            st.session_state.cert_celebrated = False
            st.rerun()
    else:
        next_info = level_config(next_level)
        if st.button(
            f"继续第 {next_level} 关 · {next_info['icon']} {next_info['name']} →",
            type="primary",
            key="map_continue",
            use_container_width=True,
        ):
            start_level(next_level)

    st.caption("每关第一次完成才会加星星；再玩一次是复习，不重复加星。阶段不会自动升级。")
    render_parent_panel()


def render_certificate() -> None:
    if not stage_is_complete():
        st.warning("奖状还在路上，先把 6 个关卡都完成吧。")
        if st.button("回到关卡地图", type="primary", key="cert_back_incomplete"):
            st.session_state.screen = "map"
            st.rerun()
        render_parent_panel()
        return

    if not st.session_state.get("cert_celebrated"):
        st.session_state.cert_celebrated = True
        st.balloons()

    moment = local_now()
    cfg = stage_conf()
    nickname = APP_CONFIG["nickname"]
    today_stars = total_stars()
    this_stage = stage_stars()
    st.markdown(
        f"""
        <div class="cert-note">📸 这张奖状可以长按或截图保存，留作今天的生日纪念。</div>
        <div class="certificate">
            <span class="cert-corner tl">✨</span>
            <span class="cert-corner tr">🎈</span>
            <span class="cert-corner bl">🎁</span>
            <span class="cert-corner br">✨</span>
            <div class="cert-seal">🎖️</div>
            <div class="cert-title" role="heading" aria-level="2">🏆 小小学习家奖状</div>
            <div class="cert-name">{safe_html(nickname)}</div>
            <div class="cert-desc">在「{cfg['name']}」阶段完成了全部 6 个关卡，<br>今天一共收获了 {today_stars} 颗星星，真棒！</div>
            <div class="cert-stats">
                <div class="cert-stat"><b>{this_stage}</b><small>本阶段星星</small></div>
                <div class="cert-stat"><b>{today_stars}</b><small>总星星</small></div>
                <div class="cert-stat"><b>6/6</b><small>完成关卡</small></div>
            </div>
            <div class="cert-stage">{cfg['badge']} {cfg['name']}徽章 · 生日 {birthday_label()}</div>
            <div class="cert-wish">{safe_html(APP_CONFIG['birthday_wish'])}</div>
            <div class="cert-footer">{date_cn(moment)} · 星期{WEEKDAYS_CN[moment.weekday()]} · {birthday_footer_text(moment)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("再玩一次", type="primary", key="play_again", use_container_width=True):
        reset_current_stage()
        st.rerun()
    if st.button("回到关卡地图", key="cert_back_map", use_container_width=True):
        st.session_state.screen = "map"
        st.session_state.cert_celebrated = False
        st.rerun()
    st.caption("「再玩一次」只会重置当前阶段的进度，其他阶段的记录还在。")
    render_parent_panel()


# ---------------------------------------------------------------------------
# 7. 家长查看
# ---------------------------------------------------------------------------


def _accuracy(correct: int, wrong: int) -> str:
    total = correct + wrong
    if total == 0:
        return "—"
    return f"{correct / total:.0%}"


def _parent_suggestions() -> list[str]:
    prog = stage_progress()
    cfg = stage_conf()
    suggestions: list[str] = []
    played = sum(
        stats["correct"] + stats["wrong"] for stats in prog["level_stats"].values()
    )
    if played == 0:
        return [
            "还没有开始，先陪孩子玩第一关就好，不用急着做完全部。",
            "答错不扣星、也不会结束游戏，可以放心让孩子自己点。",
        ]

    labels = {level["id"]: level["name"] for level in LEVELS}
    weak = []
    for level_id, stats in prog["level_stats"].items():
        attempts = stats["correct"] + stats["wrong"]
        if attempts >= 2 and stats["correct"] / attempts < 0.75:
            weak.append(level_id)
    if 2 in weak:
        suggestions.append("「数蜡烛」可以多玩一轮，先用手指数一数，再点数字。")
    if 1 in weak or 3 in weak or 4 in weak:
        suggestions.append("颜色、形状或动物关可以放慢一点，先让孩子说出名称再选。")
    eng = prog["level_stats"].get(5, {"correct": 0, "wrong": 0})
    eng_attempts = eng["correct"] + eng["wrong"]
    if eng_attempts >= 2 and eng["correct"] / max(1, eng_attempts) >= 0.75:
        suggestions.append("英语听音选图完成得不错，阶段 3 可以试试动作指令。")
    if 6 in weak:
        suggestions.append("记忆翻牌不着急，翻开前先一起说出卡片上的名字，会更容易记住。")
    if stage_is_complete() and st.session_state.current_stage in (1, 2):
        suggestions.append("这个阶段完成得很稳，下次可以试试「小树」挑战档；今天先玩得开心就好。")
    elif st.session_state.current_stage == 3 and stage_is_complete():
        suggestions.append("「小树」阶段也完成了，想挑战可以再开「小果」，但中班不建议默认打开。")
    elif st.session_state.current_stage == 4 and stage_is_complete():
        suggestions.append("「小果」阶段完成啦，今天可以收工了，把开心留给下次。")
    elif cfg["name"] != "小苗":
        suggestions.append("如果孩子今天有点累，可以回到「小苗」阶段，玩得轻松最重要。")
    if not suggestions:
        suggestions.append("今天玩得很稳，保持 5–8 分钟就收，让兴趣留一点到下次。")
    return suggestions[:3]


def render_parent_panel() -> None:
    stage_id = st.session_state.current_stage
    cfg = STAGES[stage_id]
    prog = stage_progress()
    with st.expander(
        "👨‍👩‍👧 家长查看",
        expanded=bool(st.session_state.get("awaiting_reset")),
    ):
        st.markdown("#### 今天的记录")
        metric_cols = st.columns(3, wrap=False)
        with metric_cols[0]:
            st.metric("本阶段星星", stage_stars())
        with metric_cols[1]:
            st.metric("总星星", total_stars())
        with metric_cols[2]:
            st.metric("本次时长", seconds_text(time.time() - st.session_state.session_started))

        attempts = prog["correct"] + prog["wrong"]
        st.markdown(
            f"当前阶段：**{cfg['badge']} {cfg['name']}**　"
            f"答对 **{prog['correct']}** 次 · 答错 **{prog['wrong']}** 次 · "
            f"正确率 **{_accuracy(prog['correct'], prog['wrong'])}**"
        )
        if attempts == 0:
            st.caption("还没有答题记录，陪孩子点第一关就好。")

        st.markdown("#### 各关正确率")
        table_rows = [
            "| 关卡 | 星星 | 答对/答错 | 正确率 |",
            "|---|---|---|---|",
        ]
        for level in LEVELS:
            lp = prog["levels"][level["id"]]
            stats = prog["level_stats"][level["id"]]
            layer_name = f"{level['icon']} {level['name']}"
            table_rows.append(
                f"| {layer_name} | {lp['stars']}/{level_star_cap(level['id'])} | "
                f"{stats['correct']}/{stats['wrong']} | {_accuracy(stats['correct'], stats['wrong'])} |"
            )
        st.markdown("\n".join(table_rows))

        st.markdown("#### 四个阶段的进度")
        stage_rows = ["| 阶段 | 完成关卡 | 星星 |", "|---|---|---|"]
        for sid, scfg in STAGES.items():
            sp = st.session_state.progress[sid]
            completed = sum(1 for item in sp["levels"].values() if item["completed"])
            stars = sum(item["stars"] for item in sp["levels"].values())
            mark = "（当前）" if sid == stage_id else ""
            stage_rows.append(
                f"| {scfg['badge']} {scfg['name']}{mark} | {completed}/6 | ⭐{stars} |"
            )
        st.markdown("\n".join(stage_rows))

        st.markdown("#### 给小寿星的小建议")
        for suggestion in _parent_suggestions():
            st.markdown(f"- {suggestion}")

        st.divider()
        st.markdown("#### 家长设置")
        locked = st.checkbox(
            "🔒 锁定阶段（锁定后不能切换）",
            value=st.session_state.stage_locked,
            key="parent_lock_stage",
        )
        st.session_state.stage_locked = locked

        selected_stage = st.radio(
            "切换难度阶段",
            options=list(STAGES.keys()),
            index=stage_id - 1,
            format_func=lambda sid: f"{STAGES[sid]['badge']} {STAGES[sid]['name']}",
            horizontal=True,
            key="stage_radio",
            disabled=locked,
            help="阶段 2「小苗」是中班日常档；阶段 3「小树」是家长手动开启的挑战档。",
        )
        if selected_stage is not None and int(selected_stage) != stage_id:
            st.session_state.current_stage = int(selected_stage)
            st.session_state.screen = "map"
            st.session_state.current_level = None
            st.session_state.level_state = None
            st.rerun()

        st.caption(
            "不会自动升阶；阶段 2「小苗」是中班默认档，阶段 3 建议家长陪同，"
            "阶段 4 更适合 5–6 岁、中班不建议默认开。切换阶段不会清空其他阶段的星星。"
        )

        toggle_cols = st.columns(2, wrap=False)
        with toggle_cols[0]:
            sound = st.toggle(
                "答对/答错音效",
                value=st.session_state.settings["sound"],
                key="setting_sound",
            )
            read_aloud = st.toggle(
                "题目朗读",
                value=st.session_state.read_aloud_by_stage.get(stage_id, cfg["read_aloud_default"]),
                key=f"setting_read_aloud_{stage_id}",
            )
        with toggle_cols[1]:
            english_audio = st.toggle(
                "英语发音",
                value=st.session_state.settings["english_audio"],
                key="setting_english_audio",
            )
            english_caption = st.toggle(
                "英文小字",
                value=st.session_state.settings["english_caption"],
                key="setting_english_caption",
            )

        st.session_state.settings["sound"] = bool(sound)
        st.session_state.settings["english_audio"] = bool(english_audio)
        st.session_state.settings["english_caption"] = bool(english_caption)
        st.session_state.read_aloud_by_stage[stage_id] = bool(read_aloud)

        st.divider()
        if st.session_state.get("awaiting_reset"):
            st.warning("确定要清空全部星星和进度吗？这一项不能撤销。")
            reset_cols = st.columns(2, wrap=False)
            with reset_cols[0]:
                if st.button("确认清空全部进度", type="primary", key="confirm_reset_all"):
                    reset_all_progress()
                    st.rerun()
            with reset_cols[1]:
                if st.button("先不清空", key="cancel_reset_all"):
                    st.session_state.awaiting_reset = False
                    st.rerun()
        else:
            if st.button("重置全部进度", key="ask_reset_all"):
                st.session_state.awaiting_reset = True
                st.rerun()
        st.caption("进度只保存在本浏览器会话中；刷新页面后会重新开始。不会上传任何孩子信息。")


# ---------------------------------------------------------------------------
# 8. 主入口
# ---------------------------------------------------------------------------


def main() -> None:
    init_state()
    st.markdown(APP_CSS, unsafe_allow_html=True)

    screen = st.session_state.screen
    if screen == "welcome":
        render_welcome()
    elif screen == "map":
        render_map()
    elif screen == "level":
        render_level_page()
    elif screen == "certificate":
        render_certificate()
    else:
        st.session_state.screen = "welcome"
        st.rerun()


if __name__ == "__main__":
    main()
