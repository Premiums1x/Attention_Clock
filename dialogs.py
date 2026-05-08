"""弹窗组件：StartDialog（开始专注） & HistoryDialog（历史记录）"""

import customtkinter as ctk
from config import C, PRESETS


class StartDialog(ctk.CTkToplevel):
    """开始专注弹窗：任务名(可选) + 时长(必选)"""

    def __init__(self, parent, default_min=25):
        super().__init__(parent)
        self.title("开始专注")
        self.geometry("320x290")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.attributes("-topmost", True)
        self.result = None

        main = ctk.CTkFrame(self, corner_radius=14, fg_color=C("bg_card"))
        main.pack(fill="both", expand=True, padx=6, pady=6)

        ctk.CTkLabel(main, text="新建专注",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=C("text_primary")).pack(pady=(16, 10))

        ctk.CTkLabel(main, text="任务名称（可选）",
                     font=ctk.CTkFont(size=12),
                     text_color=C("text_secondary")).pack(anchor="w", padx=24)
        self.entry = ctk.CTkEntry(main, placeholder_text="例如：写论文第三章",
                                  width=260, height=34,
                                  fg_color=C("bg_surface"),
                                  text_color=C("text_primary"),
                                  placeholder_text_color=C("text_muted"))
        self.entry.pack(padx=24, pady=(2, 10))

        ctk.CTkLabel(main, text="专注时长（分钟）",
                     font=ctk.CTkFont(size=12),
                     text_color=C("text_secondary")).pack(anchor="w", padx=24)

        time_row = ctk.CTkFrame(main, fg_color="transparent")
        time_row.pack(padx=24, pady=(2, 4))

        self.minutes = ctk.IntVar(value=default_min)

        btn_kw = dict(width=36, height=34, corner_radius=8,
                      fg_color=C("btn_face"), hover_color=C("btn_hover"),
                      font=ctk.CTkFont(size=18),
                      text_color=C("text_primary"))
        ctk.CTkButton(time_row, text="−", command=lambda: self._adj(-5),
                      **btn_kw).pack(side="left", padx=(0, 6))
        self.min_label = ctk.CTkLabel(time_row, text=f"{default_min} 分钟", width=80,
                                      font=ctk.CTkFont(size=18, weight="bold"),
                                      text_color=C("text_primary"))
        self.min_label.pack(side="left", padx=4)
        ctk.CTkButton(time_row, text="+", command=lambda: self._adj(5),
                      **btn_kw).pack(side="left", padx=(6, 0))

        preset_row = ctk.CTkFrame(main, fg_color="transparent")
        preset_row.pack(pady=(2, 10))
        for name, mins in PRESETS:
            ctk.CTkButton(preset_row, text=f"{name} {mins}'", width=76, height=26,
                          corner_radius=12, font=ctk.CTkFont(size=11),
                          fg_color=C("btn_face"), hover_color=C("btn_hover"),
                          text_color=C("text_primary"),
                          command=lambda m=mins: self._set(m)).pack(side="left", padx=3)

        btn_row = ctk.CTkFrame(main, fg_color="transparent")
        btn_row.pack(pady=(4, 14))
        ctk.CTkButton(btn_row, text="开始专注", width=130, height=36, corner_radius=10,
                      fg_color=C("success"), hover_color=C("success_hover"),
                      text_color="#FFFFFF",
                      font=ctk.CTkFont(size=14, weight="bold"),
                      command=self._ok).pack(side="left", padx=5)
        ctk.CTkButton(btn_row, text="取消", width=80, height=36, corner_radius=10,
                      fg_color=C("btn_face"), hover_color=C("btn_hover"),
                      text_color=C("text_secondary"),
                      font=ctk.CTkFont(size=13),
                      command=self.destroy).pack(side="left", padx=5)

        self.entry.bind("<Return>", lambda e: self._ok())
        self._center(parent)

    def _adj(self, delta):
        v = max(1, min(120, self.minutes.get() + delta))
        self.minutes.set(v)
        self.min_label.configure(text=f"{v} 分钟")

    def _set(self, m):
        self.minutes.set(m)
        self.min_label.configure(text=f"{m} 分钟")

    def _ok(self):
        self.result = {"task": self.entry.get().strip(), "minutes": self.minutes.get()}
        self.destroy()

    def _center(self, parent):
        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        py = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{max(0, px)}+{max(0, py)}")


class HistoryDialog(ctk.CTkToplevel):

    def __init__(self, parent, history):
        super().__init__(parent)
        self.title("专注历史")
        self.geometry("420x450")
        self.minsize(360, 200)
        self.transient(parent)
        self.attributes("-topmost", True)

        self.update_idletasks()
        self.geometry(f"+{parent.winfo_x()+parent.winfo_width()+8}+{parent.winfo_y()}")

        ctk.CTkLabel(self, text="专注历史记录",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=C("text_primary")).pack(pady=(14, 6))

        if not history:
            ctk.CTkLabel(self, text="暂无记录", text_color=C("text_muted"),
                         font=ctk.CTkFont(size=13)).pack(expand=True)
            return

        scroll = ctk.CTkScrollableFrame(self, corner_radius=8,
                                        fg_color=C("bg_surface"))
        scroll.pack(fill="both", expand=True, padx=12, pady=(4, 12))

        for rec in reversed(history):
            card = ctk.CTkFrame(scroll, corner_radius=10, fg_color=C("bg_card"))
            card.pack(fill="x", pady=4, padx=2)

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=10, pady=(8, 2))

            name = rec["task"] if rec["task"] else "无任务名"
            ctk.CTkLabel(top, text=f"📌 {name}",
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=C("text_primary"),
                         anchor="w").pack(side="left")

            st, sc = ("✅ 完成", C("success")) if rec["status"] == "auto" else ("⏸ 手动", C("warning"))
            ctk.CTkLabel(top, text=st, text_color=sc,
                         font=ctk.CTkFont(size=11, weight="bold")).pack(side="right")

            delta = int((rec["end"] - rec["start"]).total_seconds())
            info = (f"{rec['start'].strftime('%Y-%m-%d')}   "
                    f"{rec['start'].strftime('%H:%M:%S')} → {rec['end'].strftime('%H:%M:%S')}   "
                    f"时长 {delta//60}分{delta%60:02d}秒")
            ctk.CTkLabel(card, text=info, font=ctk.CTkFont(size=11),
                         text_color=C("text_secondary")).pack(anchor="w", padx=10, pady=(0, 8))
