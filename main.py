"""桌面悬浮番茄钟 v5 — 主窗口"""

import threading
import winsound
import customtkinter as ctk
from plyer import notification
from datetime import datetime

from config import C, PRESETS, MINI_W, MINI_H, FULL_W, FULL_H, MIN_W, MIN_H
from dialogs import StartDialog, HistoryDialog
from tray import TrayManager


class PomodoroApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Pomodoro")
        self.geometry(f"{FULL_W}x{FULL_H}")
        self.minsize(MIN_W, MIN_H)
        self.overrideredirect(True)
        self.attributes("-topmost", True)

        # 状态
        self.current_minutes = 25
        self.time_left = 25 * 60
        self.timer_state = "idle"
        self._after_id = None
        self.current_task = ""
        self._session_start = None
        self.history = []
        self.is_mini = False
        self._editing = False
        self._history_dlg = None

        self._drag_x = self._drag_y = 0
        self._grip = {}

        self._tray = TrayManager(
            on_show=lambda: self.after(0, self._restore),
            on_quit=lambda: self.after(0, self.destroy),
        )

        self._build_full_ui()
        self._build_mini_ui()
        self._refresh()
        self._update_btns()
        self._show_full()

    # ── 完整界面 ────────────────────────────────────────────────
    def _build_full_ui(self):
        self.full_frame = ctk.CTkFrame(self, corner_radius=16,
                                       fg_color=C("bg_main"))
        # 顶部栏
        top = ctk.CTkFrame(self.full_frame, fg_color="transparent", height=30)
        top.pack(fill="x", padx=12, pady=(8, 0))
        top.pack_propagate(False)

        self.mode_lbl = ctk.CTkLabel(top, text="🍅 专注", anchor="w",
                                     font=ctk.CTkFont(size=13, weight="bold"),
                                     text_color=C("accent"))
        self.mode_lbl.pack(side="left")

        for txt, cmd in [("—", self._minimize_to_tray),
                         ("▽", self._show_mini),
                         ("☀", self._toggle_theme),
                         ("📋", self._open_history)]:
            b = ctk.CTkButton(top, text=txt, width=26, height=22, corner_radius=6,
                              fg_color="transparent", hover_color=C("bg_hover"),
                              text_color=C("icon_btn_text"), command=cmd)
            b.pack(side="right", padx=1)
            if txt == "☀":
                self.theme_btn = b

        # 任务标签
        self.task_lbl = ctk.CTkLabel(self.full_frame, text="",
                                     font=ctk.CTkFont(size=11),
                                     text_color=C("text_secondary"))
        self.task_lbl.pack(pady=(4, 0))

        # 时间显示区
        time_area = ctk.CTkFrame(self.full_frame, fg_color="transparent")
        time_area.pack(expand=True, fill="both", padx=20)

        self.time_lbl = ctk.CTkLabel(time_area, text="25:00",
                                     font=ctk.CTkFont(family="Consolas", size=56, weight="bold"),
                                     text_color=C("text_primary"))
        self.time_lbl.pack(expand=True)

        self.time_entry = ctk.CTkEntry(time_area, font=ctk.CTkFont(family="Consolas", size=56, weight="bold"),
                                       text_color=C("text_primary"), fg_color=C("bg_main"),
                                       border_width=0,
                                       justify="center", width=200, height=80, corner_radius=0)
        self.time_entry.bind("<Return>", lambda e: self._commit_edit())
        self.time_entry.bind("<Escape>", lambda e: self._cancel_edit())

        self.bind("<Button-1>", self._on_root_click)

        # 时间调节 (idle 时可用)
        adj_row = ctk.CTkFrame(self.full_frame, fg_color="transparent")
        adj_row.pack(pady=(0, 4))

        adj_kw = dict(height=26, corner_radius=8, font=ctk.CTkFont(size=11),
                      fg_color=C("btn_face"), hover_color=C("btn_hover"),
                      text_color=C("text_primary"))

        self.adj_down = ctk.CTkButton(adj_row, text="− 5 min", width=70,
                                      command=lambda: self._adj_time(-5), **adj_kw)
        self.adj_down.pack(side="left", padx=4)

        for name, mins in PRESETS:
            ctk.CTkButton(adj_row, text=f"{mins}'", width=40,
                          command=lambda m=mins: self._set_time(m), **adj_kw).pack(side="left", padx=2)

        self.adj_up = ctk.CTkButton(adj_row, text="+ 5 min", width=70,
                                    command=lambda: self._adj_time(5), **adj_kw)
        self.adj_up.pack(side="left", padx=4)

        self.adj_row = adj_row

        # 控制按钮
        ctrl = ctk.CTkFrame(self.full_frame, fg_color="transparent")
        ctrl.pack(pady=(8, 12))
        bkw = dict(width=80, height=36, corner_radius=10,
                   font=ctk.CTkFont(size=13, weight="bold"),
                   text_color="#FFFFFF")

        self.start_btn = ctk.CTkButton(ctrl, text="开始",
                                       fg_color=C("success"), hover_color=C("success_hover"),
                                       command=self._on_start, **bkw)
        self.start_btn.pack(side="left", padx=4)

        self.stop_btn = ctk.CTkButton(ctrl, text="停止",
                                      fg_color=C("warning"), hover_color=C("warning_hover"),
                                      command=self._on_stop, **bkw)
        self.stop_btn.pack(side="left", padx=4)

        self.end_btn = ctk.CTkButton(ctrl, text="结束",
                                     fg_color=C("btn_face"), hover_color=C("btn_hover"),
                                     command=self._on_end_manual, **bkw)
        self.end_btn.pack(side="left", padx=4)

        # 缩放抓手
        grip = ctk.CTkLabel(self.full_frame, text="⋱", width=14, height=14,
                            text_color=C("text_muted"),
                            font=ctk.CTkFont(size=12), cursor="size_nw_se")
        grip.place(relx=1.0, rely=1.0, anchor="se", x=-4, y=-4)
        grip.bind("<ButtonPress-1>", self._grip_start)
        grip.bind("<B1-Motion>", self._grip_drag)

        # 拖拽
        for w in [self.full_frame, top, self.mode_lbl, self.task_lbl, time_area]:
            w.bind("<ButtonPress-1>", self._drag_start)
            w.bind("<B1-Motion>", self._drag_move)

        self.time_lbl.bind("<ButtonPress-1>", self._time_press)
        self.time_lbl.bind("<B1-Motion>", self._time_drag)
        self.time_lbl.bind("<ButtonRelease-1>", self._time_release)

    # ── 迷你浮窗 ──────────────────────────────────────────────
    def _build_mini_ui(self):
        self.mini_frame = ctk.CTkFrame(self, corner_radius=12,
                                       fg_color=C("bg_main"))
        self.mini_time = ctk.CTkLabel(self.mini_frame, text="25:00",
                                      font=ctk.CTkFont(family="Consolas",
                                                       size=18, weight="bold"),
                                      text_color=C("text_primary"))
        self.mini_time.pack(expand=True, padx=10, pady=(4, 0))

        self.mini_hint = ctk.CTkLabel(self.mini_frame, text="双击放大",
                                      font=ctk.CTkFont(size=9),
                                      text_color=C("text_muted"))
        self.mini_hint.pack(pady=(0, 4))

        for w in [self.mini_frame, self.mini_time, self.mini_hint]:
            w.bind("<ButtonPress-1>", self._drag_start)
            w.bind("<B1-Motion>", self._drag_move)
            w.bind("<Double-Button-1>", lambda e: self._show_full())

    def _show_full(self):
        self.is_mini = False
        self.mini_frame.pack_forget()
        self.full_frame.pack(fill="both", expand=True, padx=2, pady=2)
        w = max(FULL_W, self.winfo_width()) if self.winfo_width() > MINI_W + 20 else FULL_W
        h = max(FULL_H, self.winfo_height()) if self.winfo_height() > MINI_H + 20 else FULL_H
        self.geometry(f"{w}x{h}")
        self.minsize(MIN_W, MIN_H)

    def _show_mini(self):
        self.is_mini = True
        self._apply_mini()

    def _apply_mini(self):
        self.full_frame.pack_forget()
        self.mini_frame.pack(fill="both", expand=True, padx=1, pady=1)
        self.minsize(MINI_W, MINI_H)
        self.geometry(f"{MINI_W}x{MINI_H}")

    # ── 主题 ────────────────────────────────────────────────────
    def _toggle_theme(self):
        new = "Light" if ctk.get_appearance_mode() == "Dark" else "Dark"
        ctk.set_appearance_mode(new)
        self.theme_btn.configure(text="🌙" if new == "Dark" else "☀")
        self._update_colors()

    def _update_colors(self):
        self.full_frame.configure(fg_color=C("bg_main"))
        self.mini_frame.configure(fg_color=C("bg_main"))
        self.mode_lbl.configure(text_color=C("accent"))
        self.task_lbl.configure(text_color=C("text_secondary"))
        self.time_lbl.configure(text_color=C("text_primary"))
        self.mini_time.configure(text_color=C("text_primary"))

        for child in self.full_frame.winfo_children():
            if isinstance(child, ctk.CTkFrame) and child.winfo_y() < 5:
                for btn in child.winfo_children():
                    if isinstance(btn, ctk.CTkButton):
                        btn.configure(fg_color="transparent",
                                      hover_color=C("bg_hover"),
                                      text_color=C("icon_btn_text"))

        adj_kw = dict(fg_color=C("btn_face"), hover_color=C("btn_hover"),
                      text_color=C("text_primary"))
        self.adj_down.configure(**adj_kw)
        self.adj_up.configure(**adj_kw)
        for child in self.adj_row.winfo_children():
            if isinstance(child, ctk.CTkButton):
                child.configure(**adj_kw)

        self.start_btn.configure(fg_color=C("success"), hover_color=C("success_hover"))
        self.stop_btn.configure(fg_color=C("warning"), hover_color=C("warning_hover"))
        self.end_btn.configure(fg_color=C("btn_face"), hover_color=C("btn_hover"),
                               text_color=C("text_secondary"))

    # ── 拖拽 ────────────────────────────────────────────────────
    def _drag_start(self, e):
        self._drag_x = e.x_root - self.winfo_x()
        self._drag_y = e.y_root - self.winfo_y()

    def _drag_move(self, e):
        self.geometry(f"+{e.x_root - self._drag_x}+{e.y_root - self._drag_y}")

    # ── 缩放 ────────────────────────────────────────────────────
    def _grip_start(self, e):
        self._grip = {"x": e.x_root, "y": e.y_root,
                      "w": self.winfo_width(), "h": self.winfo_height()}

    def _grip_drag(self, e):
        nw = max(MIN_W, self._grip["w"] + e.x_root - self._grip["x"])
        nh = max(MIN_H, self._grip["h"] + e.y_root - self._grip["y"])
        self.geometry(f"{nw}x{nh}")

    # ── 时间调节 ────────────────────────────────────────────────
    def _adj_time(self, delta):
        if self.timer_state != "idle":
            return
        self._cancel_edit()
        self.current_minutes = max(1, min(120, self.current_minutes + delta))
        self.time_left = self.current_minutes * 60
        self._refresh()

    def _set_time(self, m):
        if self.timer_state != "idle":
            return
        self._cancel_edit()
        self.current_minutes = m
        self.time_left = m * 60
        self._refresh()

    # ── 时间标签：拖拽 + 点击编辑 ──────────────────────────────
    def _time_press(self, e):
        self._time_dragged = False
        self._drag_start(e)

    def _time_drag(self, e):
        self._time_dragged = True
        self._drag_move(e)

    def _time_release(self, e):
        if not self._time_dragged:
            self._start_edit()

    # ── 点击编辑时间 ────────────────────────────────────────────
    def _on_root_click(self, e):
        if not self._editing:
            return
        ex = self.time_entry.winfo_rootx()
        ey = self.time_entry.winfo_rooty()
        ew = self.time_entry.winfo_width()
        eh = self.time_entry.winfo_height()
        if not (ex <= e.x_root <= ex + ew and ey <= e.y_root <= ey + eh):
            self._cancel_edit()

    def _start_edit(self):
        if self.timer_state != "idle" or self._editing:
            return
        self._editing = True
        self.time_lbl.pack_forget()
        mins, secs = divmod(self.time_left, 60)
        self.time_entry.delete(0, "end")
        self.time_entry.insert(0, f"{mins:02d}:{secs:02d}")
        self.time_entry.pack(expand=True)
        self.time_entry.focus()
        self.time_entry.select_range(0, "end")

    def _commit_edit(self):
        if not self._editing:
            return
        text = self.time_entry.get().strip()
        try:
            if ":" in text:
                m, s = text.split(":", 1)
                total = int(m) * 60 + int(s)
            else:
                total = int(text) * 60
            total = max(60, min(7200, total))
            self.current_minutes = (total + 59) // 60
            self.time_left = total
        except ValueError:
            pass
        self._end_edit()

    def _cancel_edit(self):
        if not self._editing:
            return
        self._end_edit()

    def _end_edit(self):
        self._editing = False
        self.time_entry.pack_forget()
        self.time_lbl.pack(expand=True)
        self._refresh()

    # ── 历史 ────────────────────────────────────────────────────
    def _open_history(self):
        if self._history_dlg and self._history_dlg.winfo_exists():
            return
        self._history_dlg = HistoryDialog(self, self.history)
        self._history_dlg.bind("<Destroy>", lambda e: setattr(self, "_history_dlg", None))

    # ── 按钮状态 ────────────────────────────────────────────────
    def _update_btns(self):
        s = self.timer_state
        self.start_btn.configure(state="disabled" if s == "running" else "normal")
        self.stop_btn.configure(state="normal" if s == "running" else "disabled")
        self.end_btn.configure(state="disabled" if s == "idle" else "normal")
        adj_state = "normal" if s == "idle" else "disabled"
        self.adj_down.configure(state=adj_state)
        self.adj_up.configure(state=adj_state)

    # ── 开始 ────────────────────────────────────────────────────
    def _on_start(self):
        if self.timer_state == "paused":
            self.timer_state = "running"
            self._update_btns()
            self._tick()
            return

        dlg = StartDialog(self, self.current_minutes)
        self.wait_window(dlg)
        if dlg.result is None:
            return
        self.current_task = dlg.result["task"]
        self.current_minutes = dlg.result["minutes"]
        self.time_left = self.current_minutes * 60
        self._start_timer()

    def _start_timer(self):
        self.timer_state = "running"
        self._session_start = datetime.now()
        self._update_btns()
        self.task_lbl.configure(
            text=f"📌 {self.current_task}" if self.current_task else "")
        self._notify_async("🍅 专注开始！",
                           f"任务：{self.current_task}" if self.current_task else "全力专注，加油！")
        self._refresh()
        self._tick()

    # ── 停止 ────────────────────────────────────────────────────
    def _on_stop(self):
        if self.timer_state != "running":
            return
        self._cancel_after()
        self.timer_state = "paused"
        self._update_btns()

    # ── 手动结束 ────────────────────────────────────────────────
    def _on_end_manual(self):
        self._cancel_after()
        task = self.current_task
        if self._session_start:
            self._save_record("manual")
        self._reset_idle()
        title = "⏸ 提前结束专注"
        msg = f"「{task}」已提前结束，记得放松一下 😌" if task else "专注已提前结束，记得放松一下 😌"
        threading.Thread(target=lambda: (winsound.MessageBeep(winsound.MB_OK),
                                         self._send_notif(title, msg)),
                         daemon=True).start()

    # ── tick ────────────────────────────────────────────────────
    def _tick(self):
        if self.timer_state != "running":
            return
        if self.time_left > 0:
            self.time_left -= 1
            self._refresh()
            self._after_id = self.after(1000, self._tick)
        else:
            self._after_id = None
            self._on_end_natural()

    def _cancel_after(self):
        if self._after_id:
            self.after_cancel(self._after_id)
            self._after_id = None

    # ── 自然结束 ────────────────────────────────────────────────
    def _on_end_natural(self):
        task = self.current_task
        if self._session_start:
            self._save_record("auto")
        self._reset_idle()
        if self.is_mini:
            self._show_full()
        title = "✅ 专注时间到！"
        msg = f"「{task}」完成！好好放松一下吧 🎉" if task else "专注完成，好好放松一下吧 🎉"
        threading.Thread(target=lambda: (winsound.MessageBeep(winsound.MB_ICONASTERISK),
                                         self._send_notif(title, msg)),
                         daemon=True).start()

    # ── 重置 ────────────────────────────────────────────────────
    def _reset_idle(self):
        self.timer_state = "idle"
        self.time_left = self.current_minutes * 60
        self.current_task = ""
        self._session_start = None
        self.task_lbl.configure(text="")
        self._update_btns()
        self._refresh()

    # ── 记录 ────────────────────────────────────────────────────
    def _save_record(self, status):
        self.history.append({"task": self.current_task or "（无任务名）",
                             "start": self._session_start,
                             "end": datetime.now(), "status": status})
        self._session_start = None

    # ── 刷新 ────────────────────────────────────────────────────
    def _refresh(self):
        mins, secs = divmod(self.time_left, 60)
        t = f"{mins:02d}:{secs:02d}"
        if not self._editing:
            self.time_lbl.configure(text=t)
        self.mini_time.configure(text=t)

    # ── 通知 ────────────────────────────────────────────────────
    def _notify_async(self, title, msg):
        threading.Thread(target=self._send_notif, args=(title, msg), daemon=True).start()

    @staticmethod
    def _send_notif(title, msg):
        try:
            notification.notify(title=title, message=msg, app_name="🍅 番茄钟", timeout=6)
        except Exception as e:
            print(f"[通知] {e}")

    # ── 托盘 ────────────────────────────────────────────────────
    def _minimize_to_tray(self):
        self.withdraw()
        self._tray.show()

    def _restore(self):
        self._tray.hide()
        self.deiconify()
        self.attributes("-topmost", True)
        self.lift()


if __name__ == "__main__":
    PomodoroApp().mainloop()
