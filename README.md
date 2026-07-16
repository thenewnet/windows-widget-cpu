# Float Monitor 🖥️⚡

Widget giám sát hệ thống **nổi trên màn hình** cho Windows — hiển thị
**CPU · RAM · Disk · Network · Nhiệt độ/GPU** dưới dạng các vòng gauge neon
trong suốt, luôn nổi trên cùng, không còn phải mở Task Manager.

Giao diện tối giản kiểu tương lai: nền kính trong suốt, chỉ hiển thị con số,
vòng sáng chuyển màu đỏ khi tải cao, hiệu ứng chạy mượt.

```
   ╭───────────────────────────────────────────────╮
   │   ◜ 23 ◝   ◜ 61 ◝   ◜ 48 ◝   ◜ 12 ◝            │
   │    CPU      RAM      DISK     GPU              │
   │   ↓ 4.2 MB/s   ↑ 0.3 MB/s          CPU 54°C   │
   ╰───────────────────────────────────────────────╯
```

## Tính năng

- 🔵 Vòng gauge cho **CPU, RAM, Disk** và **GPU** (nếu có card NVIDIA)
- 🌐 Dải **tốc độ mạng** lên/xuống theo thời gian thực
- 🌡️ **Nhiệt độ** CPU (nếu cảm biến hỗ trợ) hoặc GPU
- 🪟 Cửa sổ **trong suốt, không viền, luôn nổi trên cùng**
- 🖱️ **Kéo thả** tự do; nháy đúp để thu gọn; chuột phải mở menu
- 📌 Khóa vị trí, xoay dọc/ngang, chỉnh độ trong suốt, ẩn/hiện nhãn
- 🚀 **Khởi động cùng Windows** (bật trong menu chuột phải)
- 📥 Thu nhỏ xuống **khay hệ thống (system tray)**
- 💾 Tự lưu vị trí & cài đặt

## Cách chạy nhanh nhất

1. Cài **Python 3.9+** (nhớ tick *Add Python to PATH* khi cài).
2. Double-click **`run.bat`** — lần đầu sẽ tự cài thư viện rồi mở widget.

Xong! Widget xuất hiện ở góc trên bên phải màn hình. Kéo tới vị trí bạn thích.

### Hoặc chạy thủ công

```bat
pip install -r requirements.txt
pythonw float_monitor.py
```

## Tạo file .exe chạy độc lập (không cần cài Python)

Double-click **`build_exe.bat`**. Sau khi xong, lấy file
`dist\FloatMonitor.exe` — copy sang máy khác chạy thẳng, không cần Python.

## Sử dụng

| Thao tác | Chức năng |
|---|---|
| Kéo chuột trái | Di chuyển widget |
| Nháy đúp | Bật/tắt chế độ thu gọn |
| Chuột phải | Mở menu tùy chọn |
| Click icon ở khay hệ thống | Ẩn/hiện widget |

Menu chuột phải: khóa vị trí · xoay dọc/ngang · thu gọn · hiện nhãn ·
độ trong suốt · khởi động cùng Windows · thoát.

## Ghi chú

- **Disk** hiển thị phần trăm **dung lượng đã dùng** của ổ hệ thống (ổn định,
  dễ đọc). Nếu bạn muốn đổi sang phần trăm **hoạt động I/O**, mình có thể chỉnh.
- **GPU** dùng `nvidia-smi` (có sẵn khi cài driver NVIDIA). Máy dùng GPU
  AMD/Intel sẽ tự ẩn vòng GPU.
- **Nhiệt độ CPU** trên Windows đôi khi không có sẵn (Windows không expose
  cảm biến cho ứng dụng thường). Khi đó widget sẽ dùng nhiệt độ GPU nếu có,
  hoặc ẩn phần nhiệt độ.
- Cài đặt được lưu tại `%APPDATA%\FloatMonitor\config.json`.

## Yêu cầu

- Windows 10/11
- Python 3.9+ (chỉ cần khi chạy từ mã nguồn, không cần với file `.exe`)
- Thư viện: `PySide6`, `psutil`
