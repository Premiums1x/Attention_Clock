"""配色方案、预设、窗口尺寸等全局常量"""

import customtkinter as ctk

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# 格式: (light, dark)
COLOR = {
    "bg_main":       ("#F0F2F5", "#1a1a2e"),
    "bg_card":       ("#FFFFFF", "#252545"),
    "bg_surface":    ("#E8EBF0", "#2a2a4a"),
    "bg_hover":      ("#D8DCE3", "#353560"),

    "text_primary":  ("#1A1D23", "#E8E8F0"),
    "text_secondary":("#4A4E59", "#9CA0AD"),
    "text_muted":    ("#6B7080", "#6B7080"),

    "accent":        ("#5B6AE0", "#7B88FF"),
    "accent_hover":  ("#4A58C8", "#9BA5FF"),

    "success":       ("#2E9E47", "#4CAF50"),
    "success_hover": ("#248038", "#66BB6A"),
    "warning":       ("#D97B00", "#FF9800"),
    "warning_hover": ("#B86800", "#FFB74D"),

    "btn_face":      ("#D5D8E0", "#363660"),
    "btn_hover":     ("#C5C8D2", "#454578"),

    "icon_btn_text": ("#6B7080", "#8890A0"),
}

PRESETS = [("经典", 25), ("轻松", 15), ("深度", 50)]

MINI_W, MINI_H = 100, 52
FULL_W, FULL_H = 320, 310
MIN_W, MIN_H = 280, 270


def C(key):
    return COLOR[key]
