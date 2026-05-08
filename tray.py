"""系统托盘：图标创建、最小化到托盘、从托盘恢复"""

import threading
import pystray
from PIL import Image, ImageDraw


def make_icon():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((6, 10, 58, 60), fill="#FF6B6B")
    d.rectangle((28, 4, 36, 14), fill="#4CAF50")
    return img


class TrayManager:
    """管理托盘图标生命周期，通过回调与主窗口通信"""

    def __init__(self, on_show, on_quit):
        self._icon = None
        self._on_show = on_show
        self._on_quit = on_quit

    @property
    def active(self):
        return self._icon is not None

    def show(self):
        if self._icon:
            return
        menu = pystray.Menu(
            pystray.MenuItem("显示主界面", self._handle_show, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", self._handle_quit))
        self._icon = pystray.Icon("pomodoro", make_icon(), "🍅 番茄钟", menu)
        threading.Thread(target=self._icon.run, daemon=True).start()

    def hide(self):
        if self._icon:
            self._icon.stop()
            self._icon = None

    def _handle_show(self, icon=None, item=None):
        self._on_show()

    def _handle_quit(self, icon=None, item=None):
        self._on_quit()
