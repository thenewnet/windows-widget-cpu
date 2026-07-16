"""
Float Monitor - Widget giám sát hệ thống nổi trên màn hình cho Windows.

Hiển thị CPU, RAM, Disk, Network và Nhiệt độ/GPU dưới dạng các vòng gauge
neon trong suốt, luôn nổi trên cùng, có thể kéo thả tự do.

Yêu cầu: Python 3.9+, PySide6, psutil
    pip install -r requirements.txt

Chạy:  pythonw float_monitor.py   (hoặc double-click run.bat)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time

try:
    import psutil
except ImportError:  # pragma: no cover
    sys.exit(
        "Thiếu thư viện 'psutil'. Chạy:  pip install -r requirements.txt"
    )

from PySide6.QtCore import Qt, QTimer, QPointF, QRectF
from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QColor,
    QFont,
    QGuiApplication,
    QIcon,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QColorDialog,
    QMenu,
    QSystemTrayIcon,
    QWidget,
)


# --------------------------------------------------------------------------- #
#  Cấu hình & lưu trạng thái
# --------------------------------------------------------------------------- #
APP_NAME = "FloatMonitor"
IS_WINDOWS = sys.platform.startswith("win")


def config_dir() -> str:
    if IS_WINDOWS:
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.path.join(os.path.expanduser("~"), ".config")
    path = os.path.join(base, APP_NAME)
    os.makedirs(path, exist_ok=True)
    return path


CONFIG_PATH = os.path.join(config_dir(), "config.json")

# Các chỉ số vẽ dưới dạng vòng gauge (thứ tự hiển thị)
GAUGE_SPECS = [
    ("cpu", "CPU"),
    ("ram", "RAM"),
    ("disk", "DISK"),
    ("gpu", "GPU"),
]

# Bảng màu chủ đề dựng sẵn: mỗi theme gán màu cho từng chỉ số + "net" (accent)
THEMES = {
    "cyber":  {"cpu": "#00E5FF", "ram": "#A78BFA", "disk": "#00E676",
               "gpu": "#FFB300", "net": "#00E5FF"},
    "aurora": {"cpu": "#00F5D4", "ram": "#7B61FF", "disk": "#4CC9F0",
               "gpu": "#F72585", "net": "#00F5D4"},
    "sunset": {"cpu": "#FF6B6B", "ram": "#FFD166", "disk": "#FF9F1C",
               "gpu": "#EF476F", "net": "#FFD166"},
    "matrix": {"cpu": "#39FF14", "ram": "#00E676", "disk": "#7CFC00",
               "gpu": "#B6FF00", "net": "#39FF14"},
    "ice":    {"cpu": "#E6EDF3", "ram": "#9FB3C8", "disk": "#6FA8DC",
               "gpu": "#B0BEC5", "net": "#8BD3FF"},
    "magma":  {"cpu": "#FF3D57", "ram": "#FF7A00", "disk": "#FFB300",
               "gpu": "#FF006E", "net": "#FF7A00"},
}

# Tên hiển thị tiếng Việt cho các theme
THEME_LABELS = {
    "cyber": "Cyber (xanh neon)",
    "aurora": "Aurora (cực quang)",
    "sunset": "Sunset (hoàng hôn)",
    "matrix": "Matrix (xanh lá)",
    "ice": "Ice (trắng bạc)",
    "magma": "Magma (đỏ cam)",
}

DEFAULT_CONFIG = {
    "pos_x": None,
    "pos_y": None,
    "layout": "horizontal",   # horizontal | vertical
    "locked": False,
    "panel_opacity": 0.72,     # độ mờ nền panel (0..1)
    "compact": False,
    "show_labels": True,
    "disk_mode": "usage",      # usage = dung lượng đã dùng | activity = hoạt động I/O
    "theme": "cyber",          # tên theme dựng sẵn, hoặc "custom"
    "colors": dict(THEMES["cyber"]),  # màu thực tế đang dùng cho từng chỉ số
}


def load_config() -> dict:
    cfg = dict(DEFAULT_CONFIG)
    cfg["colors"] = dict(DEFAULT_CONFIG["colors"])
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        colors = data.pop("colors", None)
        cfg.update(data)
        if isinstance(colors, dict):
            cfg["colors"].update(colors)  # giữ đủ khóa dù file cũ thiếu
    except (OSError, ValueError):
        pass
    return cfg


def save_config(cfg: dict) -> None:
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except OSError:
        pass


# --------------------------------------------------------------------------- #
#  Thu thập chỉ số hệ thống
# --------------------------------------------------------------------------- #
class SystemMetrics:
    """Đọc các chỉ số hệ thống. An toàn khi một số chỉ số không khả dụng."""

    def __init__(self) -> None:
        self._last_net = psutil.net_io_counters()
        self._last_disk_io = self._safe_disk_io()
        self._last_time = time.monotonic()
        self._gpu_available = self._detect_nvidia()
        # "mồi" cpu_percent để lần đọc đầu không trả về 0.0
        psutil.cpu_percent(interval=None)

    @staticmethod
    def _safe_disk_io():
        try:
            return psutil.disk_io_counters()
        except Exception:
            return None

    # -- GPU (NVIDIA) ------------------------------------------------------- #
    @staticmethod
    def _detect_nvidia() -> bool:
        try:
            SystemMetrics._nvidia_smi(["--help"])
            return True
        except Exception:
            return False

    @staticmethod
    def _nvidia_smi(args: list[str]) -> str:
        flags = 0x08000000 if IS_WINDOWS else 0  # CREATE_NO_WINDOW
        out = subprocess.run(
            ["nvidia-smi", *args],
            capture_output=True,
            text=True,
            timeout=2,
            creationflags=flags,
        )
        if out.returncode != 0:
            raise RuntimeError(out.stderr)
        return out.stdout

    def _read_gpu(self) -> tuple[float | None, float | None]:
        """Trả về (gpu_util_%, gpu_temp_°C) hoặc (None, None)."""
        if not self._gpu_available:
            return None, None
        try:
            raw = self._nvidia_smi([
                "--query-gpu=utilization.gpu,temperature.gpu",
                "--format=csv,noheader,nounits",
            ])
            first = raw.strip().splitlines()[0]
            util_s, temp_s = (p.strip() for p in first.split(","))
            return float(util_s), float(temp_s)
        except Exception:
            self._gpu_available = False
            return None, None

    # -- Nhiệt độ CPU ------------------------------------------------------- #
    @staticmethod
    def _read_cpu_temp() -> float | None:
        fn = getattr(psutil, "sensors_temperatures", None)
        if fn is None:
            return None
        try:
            temps = fn()
        except Exception:
            return None
        if not temps:
            return None
        # Ưu tiên các cảm biến hay gặp
        for key in ("coretemp", "k10temp", "cpu_thermal", "acpitz"):
            if key in temps and temps[key]:
                return float(temps[key][0].current)
        # Không có key ưu tiên -> lấy cảm biến đầu tiên có giá trị
        for entries in temps.values():
            if entries:
                return float(entries[0].current)
        return None

    # -- API chính ---------------------------------------------------------- #
    def poll(self) -> dict:
        now = time.monotonic()
        elapsed = max(now - self._last_time, 1e-6)

        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage(os.path.abspath(os.sep)).percent

        net = psutil.net_io_counters()
        down = (net.bytes_recv - self._last_net.bytes_recv) / elapsed
        up = (net.bytes_sent - self._last_net.bytes_sent) / elapsed
        self._last_net = net

        # Mức hoạt động ổ đĩa (% thời gian bận I/O) - dựa trên busy_time (ms).
        # Không phải nền tảng nào cũng có busy_time -> trả None nếu thiếu.
        disk_activity = None
        io = self._safe_disk_io()
        if io is not None and self._last_disk_io is not None:
            last_busy = getattr(self._last_disk_io, "busy_time", None)
            busy = getattr(io, "busy_time", None)
            if last_busy is not None and busy is not None:
                delta = busy - last_busy               # mili-giây bận
                disk_activity = max(0.0, min(100.0, delta / (elapsed * 1000) * 100))
        self._last_disk_io = io

        self._last_time = now

        gpu_util, gpu_temp = self._read_gpu()
        cpu_temp = self._read_cpu_temp()

        return {
            "cpu": cpu,
            "ram": ram,
            "disk_usage": disk_usage,        # % dung lượng đã dùng
            "disk_activity": disk_activity,  # % hoạt động I/O hoặc None
            "net_down": down,        # bytes/s
            "net_up": up,            # bytes/s
            "gpu": gpu_util,         # % hoặc None
            "gpu_temp": gpu_temp,    # °C hoặc None
            "cpu_temp": cpu_temp,    # °C hoặc None
        }

    @staticmethod
    def disk_activity_supported() -> bool:
        io = SystemMetrics._safe_disk_io()
        return io is not None and getattr(io, "busy_time", None) is not None

    @property
    def gpu_available(self) -> bool:
        return self._gpu_available


def human_speed(bytes_per_sec: float) -> str:
    b = bytes_per_sec
    if b < 1024:
        return f"{b:4.0f} B/s"
    kb = b / 1024
    if kb < 1024:
        return f"{kb:5.1f} KB/s"
    mb = kb / 1024
    if mb < 1024:
        return f"{mb:5.1f} MB/s"
    return f"{mb / 1024:5.2f} GB/s"


# --------------------------------------------------------------------------- #
#  Mô hình một gauge
# --------------------------------------------------------------------------- #
class Gauge:
    def __init__(self, key: str, label: str, color: str):
        self.key = key
        self.label = label
        self.base_color = QColor(color)
        self.target = 0.0       # giá trị mục tiêu (0..100)
        self.display = 0.0      # giá trị đang hiển thị (animation)

    def set_target(self, value: float) -> None:
        self.target = max(0.0, min(100.0, float(value)))

    def step(self, factor: float = 0.18) -> None:
        self.display += (self.target - self.display) * factor
        if abs(self.target - self.display) < 0.05:
            self.display = self.target

    def current_color(self) -> QColor:
        """Chuyển dần sang đỏ khi tải cao (>70%)."""
        v = self.display
        if v <= 70:
            return QColor(self.base_color)
        t = min((v - 70) / 30.0, 1.0)
        hot = QColor("#FF3D57")
        c = self.base_color
        return QColor(
            int(c.red() + (hot.red() - c.red()) * t),
            int(c.green() + (hot.green() - c.green()) * t),
            int(c.blue() + (hot.blue() - c.blue()) * t),
        )


# --------------------------------------------------------------------------- #
#  Widget chính
# --------------------------------------------------------------------------- #
class MonitorWidget(QWidget):
    # kích thước
    RING = 96          # đường kính vòng
    RING_COMPACT = 68
    GAP = 16           # khoảng cách giữa các vòng
    MARGIN = 18        # lề panel
    FOOTER = 30        # chiều cao dải network/nhiệt độ

    def __init__(self, cfg: dict):
        super().__init__()
        self.cfg = cfg
        self.metrics = SystemMetrics()
        self._drag_offset = None
        self._data = {}

        # Các gauge sẽ hiển thị dưới dạng vòng, màu lấy từ config
        self.gauges = []
        for key, label in GAUGE_SPECS:
            if key == "gpu" and not self.metrics.gpu_available:
                continue
            self.gauges.append(Gauge(key, label, self._color_for(key)))

        self._init_window()
        self._build_menu()
        self._layout_window()

        # Timer đọc dữ liệu (1s) và timer animation (~60fps)
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self._poll)
        self.poll_timer.start(1000)

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._animate)
        self.anim_timer.start(16)

        self._poll()

    # -- Thiết lập cửa sổ --------------------------------------------------- #
    def _init_window(self) -> None:
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowTitle(APP_NAME)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_menu)

    def _ring_size(self) -> int:
        return self.RING_COMPACT if self.cfg["compact"] else self.RING

    def _layout_window(self) -> None:
        ring = self._ring_size()
        n = len(self.gauges)
        show_footer = True  # luôn có network (+ nhiệt độ nếu có)

        if self.cfg["layout"] == "vertical":
            width = self.MARGIN * 2 + ring
            height = self.MARGIN * 2 + n * ring + (n - 1) * self.GAP
        else:
            width = self.MARGIN * 2 + n * ring + (n - 1) * self.GAP
            height = self.MARGIN * 2 + ring

        if show_footer:
            height += self.FOOTER

        self.resize(width, height)

        # Vị trí: dùng lại vị trí đã lưu, nếu chưa có thì góc trên phải
        x, y = self.cfg.get("pos_x"), self.cfg.get("pos_y")
        if x is None or y is None:
            screen = QGuiApplication.primaryScreen().availableGeometry()
            x = screen.right() - width - 40
            y = screen.top() + 60
        self.move(int(x), int(y))

    # -- Menu chuột phải ---------------------------------------------------- #
    def _build_menu(self) -> None:
        self.menu = QMenu(self)
        self.menu.setStyleSheet(
            "QMenu{background:#141922;color:#E6EDF3;border:1px solid #2A3444;"
            "border-radius:8px;padding:6px;}"
            "QMenu::item{padding:6px 22px;border-radius:6px;}"
            "QMenu::item:selected{background:#1F6FEB;}"
            "QMenu::separator{height:1px;background:#2A3444;margin:6px 4px;}"
        )

        self.act_lock = QAction("Khóa vị trí", self, checkable=True)
        self.act_lock.setChecked(self.cfg["locked"])
        self.act_lock.triggered.connect(self._toggle_lock)

        self.act_layout = QAction("Xoay dọc / ngang", self)
        self.act_layout.triggered.connect(self._toggle_layout)

        self.act_compact = QAction("Thu gọn", self, checkable=True)
        self.act_compact.setChecked(self.cfg["compact"])
        self.act_compact.triggered.connect(self._toggle_compact)

        self.act_labels = QAction("Hiện nhãn", self, checkable=True)
        self.act_labels.setChecked(self.cfg["show_labels"])
        self.act_labels.triggered.connect(self._toggle_labels)

        op_menu = QMenu("Độ trong suốt", self.menu)
        op_menu.setStyleSheet(self.menu.styleSheet())
        for pct in (40, 55, 70, 85, 100):
            a = QAction(f"{pct}%", op_menu)
            a.triggered.connect(lambda _=False, p=pct: self._set_opacity(p / 100))
            op_menu.addAction(a)

        # Submenu chọn màu: theme dựng sẵn + tùy chỉnh từng chỉ số
        color_menu = QMenu("Màu sắc", self.menu)
        color_menu.setStyleSheet(self.menu.styleSheet())
        self.theme_group = QActionGroup(self)
        self.theme_group.setExclusive(True)
        for name, label in THEME_LABELS.items():
            a = QAction(label, color_menu, checkable=True)
            a.setChecked(self.cfg.get("theme") == name)
            a.triggered.connect(lambda _=False, n=name: self._set_theme(n))
            self.theme_group.addAction(a)
            color_menu.addAction(a)
        color_menu.addSeparator()
        for key, label in GAUGE_SPECS:
            if key == "gpu" and not self.metrics.gpu_available:
                continue
            a = QAction(f"Tùy chỉnh màu {label}…", color_menu)
            a.triggered.connect(lambda _=False, k=key: self._pick_color(k))
            color_menu.addAction(a)
        a_net = QAction("Tùy chỉnh màu Mạng/nhấn…", color_menu)
        a_net.triggered.connect(lambda _=False: self._pick_color("net"))
        color_menu.addAction(a_net)
        self.color_menu = color_menu

        # Submenu hiển thị ổ cứng: dung lượng đã dùng | mức hoạt động I/O
        disk_menu = QMenu("Ổ cứng", self.menu)
        disk_menu.setStyleSheet(self.menu.styleSheet())
        self.disk_group = QActionGroup(self)
        self.disk_group.setExclusive(True)
        act_disk_usage = QAction("Dung lượng đã dùng (%)", disk_menu, checkable=True)
        act_disk_usage.setChecked(self.cfg.get("disk_mode", "usage") == "usage")
        act_disk_usage.triggered.connect(lambda: self._set_disk_mode("usage"))
        act_disk_act = QAction("Mức hoạt động I/O (%)", disk_menu, checkable=True)
        act_disk_act.setChecked(self.cfg.get("disk_mode") == "activity")
        act_disk_act.triggered.connect(lambda: self._set_disk_mode("activity"))
        if not SystemMetrics.disk_activity_supported():
            act_disk_act.setText("Mức hoạt động I/O (không hỗ trợ)")
            act_disk_act.setEnabled(False)
        self.disk_group.addAction(act_disk_usage)
        self.disk_group.addAction(act_disk_act)
        disk_menu.addAction(act_disk_usage)
        disk_menu.addAction(act_disk_act)

        self.act_autostart = QAction("Khởi động cùng Windows", self, checkable=True)
        self.act_autostart.setChecked(self._is_autostart())
        self.act_autostart.triggered.connect(self._toggle_autostart)
        self.act_autostart.setEnabled(IS_WINDOWS)

        act_quit = QAction("Thoát", self)
        act_quit.triggered.connect(self._quit)

        self.menu.addAction(self.act_lock)
        self.menu.addAction(self.act_layout)
        self.menu.addAction(self.act_compact)
        self.menu.addAction(self.act_labels)
        self.menu.addMenu(disk_menu)
        self.menu.addMenu(op_menu)
        self.menu.addMenu(color_menu)
        self.menu.addSeparator()
        self.menu.addAction(self.act_autostart)
        self.menu.addSeparator()
        self.menu.addAction(act_quit)

    def _show_menu(self, pos) -> None:
        self.menu.exec(self.mapToGlobal(pos))

    # -- Các hành động trong menu ------------------------------------------ #
    def _toggle_lock(self) -> None:
        self.cfg["locked"] = self.act_lock.isChecked()
        save_config(self.cfg)

    def _toggle_layout(self) -> None:
        self.cfg["layout"] = (
            "vertical" if self.cfg["layout"] == "horizontal" else "horizontal"
        )
        self._layout_window()
        self.update()
        save_config(self.cfg)

    def _toggle_compact(self) -> None:
        self.cfg["compact"] = self.act_compact.isChecked()
        self._layout_window()
        self.update()
        save_config(self.cfg)

    def _toggle_labels(self) -> None:
        self.cfg["show_labels"] = self.act_labels.isChecked()
        self.update()
        save_config(self.cfg)

    def _set_opacity(self, value: float) -> None:
        self.cfg["panel_opacity"] = value
        self.update()
        save_config(self.cfg)

    def _set_disk_mode(self, mode: str) -> None:
        self.cfg["disk_mode"] = mode
        if self._data:                 # cập nhật ngay nhãn & giá trị gauge ổ đĩa
            for g in self.gauges:
                if g.key == "disk":
                    val, label = self._disk_value_label()
                    g.label = label
                    g.set_target(val)
        self.update()
        save_config(self.cfg)

    # -- Màu sắc ------------------------------------------------------------ #
    def _color_for(self, key: str) -> str:
        colors = self.cfg.get("colors") or {}
        return colors.get(key) or THEMES["cyber"].get(key, "#00E5FF")

    def _accent_color(self, alpha: int = 255) -> QColor:
        c = QColor(self._color_for("net"))
        c.setAlpha(alpha)
        return c

    def _apply_colors(self) -> None:
        for g in self.gauges:
            g.base_color = QColor(self._color_for(g.key))
        self.update()

    def _set_theme(self, name: str) -> None:
        if name not in THEMES:
            return
        self.cfg["theme"] = name
        self.cfg["colors"] = dict(THEMES[name])
        self._apply_colors()
        save_config(self.cfg)

    def _pick_color(self, key: str) -> None:
        current = QColor(self._color_for(key))
        col = QColorDialog.getColor(current, self, "Chọn màu hiển thị")
        if not col.isValid():
            return
        self.cfg.setdefault("colors", {})[key] = col.name()
        self.cfg["theme"] = "custom"
        for a in self.theme_group.actions():   # bỏ chọn các theme dựng sẵn
            a.setChecked(False)
        self._apply_colors()
        save_config(self.cfg)

    # -- Tự khởi động cùng Windows ----------------------------------------- #
    def _autostart_command(self) -> str:
        pyw = sys.executable
        if pyw.lower().endswith("python.exe"):
            cand = pyw[:-len("python.exe")] + "pythonw.exe"
            if os.path.exists(cand):
                pyw = cand
        script = os.path.abspath(__file__)
        return f'"{pyw}" "{script}"'

    def _is_autostart(self) -> bool:
        if not IS_WINDOWS:
            return False
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
            )
            winreg.QueryValueEx(key, APP_NAME)
            winreg.CloseKey(key)
            return True
        except OSError:
            return False

    def _toggle_autostart(self) -> None:
        if not IS_WINDOWS:
            return
        import winreg
        run_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, run_key, 0, winreg.KEY_SET_VALUE
            )
            if self.act_autostart.isChecked():
                winreg.SetValueEx(
                    key, APP_NAME, 0, winreg.REG_SZ, self._autostart_command()
                )
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except OSError:
                    pass
            winreg.CloseKey(key)
        except OSError:
            self.act_autostart.setChecked(self._is_autostart())

    def _quit(self) -> None:
        self._save_position()
        QApplication.quit()

    # -- Kéo thả ------------------------------------------------------------ #
    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton and not self.cfg["locked"]:
            self._drag_offset = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event) -> None:
        if self._drag_offset is not None:
            self._drag_offset = None
            self._save_position()

    def mouseDoubleClickEvent(self, event) -> None:
        # Nháy đúp để bật/tắt thu gọn nhanh
        self.act_compact.toggle()
        self._toggle_compact()

    def _save_position(self) -> None:
        self.cfg["pos_x"] = self.x()
        self.cfg["pos_y"] = self.y()
        save_config(self.cfg)

    # -- Cập nhật dữ liệu --------------------------------------------------- #
    def _disk_value_label(self) -> tuple[float, str]:
        """Trả về (giá trị %, nhãn) cho gauge ổ đĩa theo chế độ đang chọn."""
        if self.cfg.get("disk_mode") == "activity":
            act = self._data.get("disk_activity")
            if act is not None:
                return act, "I/O"
        return self._data.get("disk_usage", 0.0), "DISK"

    def _poll(self) -> None:
        self._data = self.metrics.poll()
        for g in self.gauges:
            if g.key == "disk":
                val, label = self._disk_value_label()
                g.label = label
                g.set_target(val)
                continue
            val = self._data.get(g.key)
            if val is not None:
                g.set_target(val)

    def _animate(self) -> None:
        moved = False
        for g in self.gauges:
            before = g.display
            g.step()
            if abs(before - g.display) > 0.01:
                moved = True
        if moved:
            self.update()

    # -- Vẽ ----------------------------------------------------------------- #
    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setRenderHint(QPainter.TextAntialiasing, True)

        rect = QRectF(0, 0, self.width(), self.height())
        self._draw_panel(p, rect)

        ring = self._ring_size()
        for i, g in enumerate(self.gauges):
            if self.cfg["layout"] == "vertical":
                x = self.MARGIN
                y = self.MARGIN + i * (ring + self.GAP)
            else:
                x = self.MARGIN + i * (ring + self.GAP)
                y = self.MARGIN
            self._draw_ring(p, g, QRectF(x, y, ring, ring))

        self._draw_footer(p)
        p.end()

    def _draw_panel(self, p: QPainter, rect: QRectF) -> None:
        alpha = int(self.cfg["panel_opacity"] * 255)
        radius = 22.0
        path = QPainterPath()
        path.addRoundedRect(rect.adjusted(1, 1, -1, -1), radius, radius)

        # Nền tối chuyển sắc nhẹ
        p.fillPath(path, QColor(11, 15, 22, alpha))
        # Viền phát sáng mờ
        p.setPen(QPen(QColor(90, 130, 180, 60), 1.4))
        p.drawPath(path)
        # Đường accent mảnh phía trên
        p.setPen(QPen(self._accent_color(70), 1.2))
        p.drawLine(
            QPointF(rect.left() + 20, rect.top() + 8),
            QPointF(rect.right() - 20, rect.top() + 8),
        )

    def _draw_ring(self, p: QPainter, g: Gauge, box: QRectF) -> None:
        pad = box.width() * 0.14
        arc_box = box.adjusted(pad, pad, -pad, -pad)
        thickness = box.width() * 0.085
        color = g.current_color()

        # Track nền
        track = QPen(QColor(255, 255, 255, 28), thickness)
        track.setCapStyle(Qt.RoundCap)
        p.setPen(track)
        p.drawArc(arc_box, 0, 360 * 16)

        frac = g.display / 100.0
        span = int(-frac * 360 * 16)
        start = 90 * 16  # bắt đầu từ đỉnh

        if frac > 0.001:
            # Lớp glow rộng, mờ
            glow = QPen(QColor(color.red(), color.green(), color.blue(), 70),
                        thickness * 2.1)
            glow.setCapStyle(Qt.RoundCap)
            p.setPen(glow)
            p.drawArc(arc_box, start, span)
            # Lớp chính sáng
            main = QPen(color, thickness)
            main.setCapStyle(Qt.RoundCap)
            p.setPen(main)
            p.drawArc(arc_box, start, span)

        # Con số ở giữa
        cx, cy = box.center().x(), box.center().y()
        big = box.width() * (0.30 if not self.cfg["compact"] else 0.34)
        num_font = QFont("Segoe UI", int(big), QFont.DemiBold)
        num_font.setStyleStrategy(QFont.PreferAntialias)

        value_text = f"{int(round(g.display))}"
        p.setFont(num_font)
        p.setPen(QColor(240, 248, 255))
        # canh giữa (chừa chỗ cho nhãn bên dưới nếu có)
        offset = -box.height() * 0.06 if self.cfg["show_labels"] else 0
        num_rect = QRectF(box.left(), box.top() + offset,
                          box.width(), box.height())
        p.drawText(num_rect, Qt.AlignCenter, value_text)

        # dấu %
        small = QFont("Segoe UI", int(box.width() * 0.11))
        p.setFont(small)
        p.setPen(QColor(150, 170, 190))
        fm_w = p.fontMetrics().horizontalAdvance("%")
        p.setFont(num_font)
        num_w = p.fontMetrics().horizontalAdvance(value_text)
        p.setFont(small)
        p.drawText(
            QRectF(cx + num_w / 2 + 2, cy + offset - box.height() * 0.10,
                   fm_w + 6, box.height() * 0.3),
            Qt.AlignLeft | Qt.AlignVCenter, "%",
        )

        # Nhãn
        if self.cfg["show_labels"]:
            lbl_font = QFont("Segoe UI", int(box.width() * 0.095), QFont.Bold)
            lbl_font.setLetterSpacing(QFont.AbsoluteSpacing, 2.0)
            p.setFont(lbl_font)
            p.setPen(QColor(color.red(), color.green(), color.blue(), 220))
            lbl_rect = QRectF(box.left(), cy + box.height() * 0.16,
                              box.width(), box.height() * 0.3)
            p.drawText(lbl_rect, Qt.AlignHCenter | Qt.AlignTop, g.label)

    def _draw_footer(self, p: QPainter) -> None:
        d = self._data
        y = self.height() - self.FOOTER
        rect = QRectF(self.MARGIN, y, self.width() - self.MARGIN * 2, self.FOOTER)

        # đường phân cách mảnh
        p.setPen(QPen(QColor(255, 255, 255, 22), 1))
        p.drawLine(QPointF(rect.left(), y + 2), QPointF(rect.right(), y + 2))

        font = QFont("Consolas", 9)
        if not font.exactMatch():
            font = QFont("Segoe UI", 9)
        p.setFont(font)

        down = human_speed(d.get("net_down", 0.0))
        up = human_speed(d.get("net_up", 0.0))

        # Network bên trái
        p.setPen(self._accent_color(235))
        p.drawText(
            QRectF(rect.left(), y + 4, rect.width() * 0.62, self.FOOTER - 6),
            Qt.AlignLeft | Qt.AlignVCenter,
            f"↓ {down.strip()}   ↑ {up.strip()}",
        )

        # Nhiệt độ bên phải (CPU ưu tiên, không có thì GPU)
        temp = d.get("cpu_temp")
        temp_lbl = "CPU"
        if temp is None:
            temp = d.get("gpu_temp")
            temp_lbl = "GPU"
        if temp is not None:
            tcol = QColor("#00E676") if temp < 70 else QColor("#FF3D57")
            p.setPen(tcol)
            p.drawText(
                QRectF(rect.left() + rect.width() * 0.62, y + 4,
                       rect.width() * 0.38, self.FOOTER - 6),
                Qt.AlignRight | Qt.AlignVCenter,
                f"{temp_lbl} {int(round(temp))}°C",
            )


# --------------------------------------------------------------------------- #
#  Khay hệ thống
# --------------------------------------------------------------------------- #
def make_tray_icon() -> QIcon:
    pix = QPixmap(64, 64)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing, True)
    pen = QPen(QColor("#00E5FF"), 7)
    pen.setCapStyle(Qt.RoundCap)
    p.setPen(pen)
    p.drawArc(QRectF(10, 10, 44, 44), 90 * 16, -250 * 16)
    p.end()
    return QIcon(pix)


def setup_tray(app: QApplication, widget: MonitorWidget) -> QSystemTrayIcon | None:
    if not QSystemTrayIcon.isSystemTrayAvailable():
        return None
    tray = QSystemTrayIcon(make_tray_icon(), app)
    tray.setToolTip("Float Monitor")

    menu = QMenu()
    menu.setStyleSheet(widget.menu.styleSheet())

    act_show = QAction("Ẩn / Hiện", menu)
    act_show.triggered.connect(
        lambda: widget.setVisible(not widget.isVisible())
    )
    act_quit = QAction("Thoát", menu)
    act_quit.triggered.connect(widget._quit)

    menu.addAction(act_show)
    menu.addSeparator()
    menu.addAction(act_quit)
    tray.setContextMenu(menu)
    tray.activated.connect(
        lambda reason: widget.setVisible(not widget.isVisible())
        if reason == QSystemTrayIcon.Trigger else None
    )
    tray.show()
    return tray


# --------------------------------------------------------------------------- #
#  main
# --------------------------------------------------------------------------- #
def main() -> None:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    cfg = load_config()
    widget = MonitorWidget(cfg)
    widget.show()

    # giữ tham chiếu để tray không bị thu gom
    widget._tray = setup_tray(app, widget)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
