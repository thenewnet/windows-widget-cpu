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
- 💽 **Ổ cứng 2 chế độ**: hiển thị **dung lượng đã dùng (%)** hoặc **mức hoạt
  động I/O (%)** — đổi trong menu chuột phải
- 🌐 Dải **tốc độ mạng** lên/xuống theo thời gian thực
- 🌡️ **Nhiệt độ** CPU (nếu cảm biến hỗ trợ) hoặc GPU
- 🪟 Cửa sổ **trong suốt, không viền, luôn nổi trên cùng**
- 🎨 **Tùy chọn màu sắc**: 6 bảng màu dựng sẵn (Cyber, Aurora, Sunset, Matrix,
  Ice, Magma) hoặc **tự chọn màu riêng cho từng chỉ số**
- 🖱️ **Kéo thả** tự do; nháy đúp để thu gọn; chuột phải mở menu
- 📌 Khóa vị trí, xoay dọc/ngang, chỉnh độ trong suốt, ẩn/hiện nhãn
- 🚀 **Khởi động cùng Windows** (bật trong menu chuột phải)
- 📥 Thu nhỏ xuống **khay hệ thống (system tray)**
- 💾 Tự lưu vị trí & cài đặt

## ⚡ Cài đặt 1 dòng lệnh (khuyên dùng)

Mở **PowerShell** rồi dán đúng 1 dòng này và Enter:

```powershell
irm https://raw.githubusercontent.com/thenewnet/windows-widget-cpu/main/install.ps1 | iex
```

Script sẽ tự động: tải mã nguồn từ GitHub (**không cần clone repo**), tạo môi
trường Python riêng, cài thư viện, tạo shortcut ở Start Menu + Desktop và **chạy
widget luôn**. Nếu máy chưa có Python, script sẽ thử cài giúp qua `winget`.

> Nếu PowerShell chặn do ExecutionPolicy, dùng dòng này:
> ```powershell
> powershell -ExecutionPolicy Bypass -Command "irm https://raw.githubusercontent.com/thenewnet/windows-widget-cpu/main/install.ps1 | iex"
> ```

## 🔄 Cập nhật (nếu bạn đã cài rồi)

Chỉ cần **chạy lại đúng lệnh cài đặt** — nó tự tải bản mới nhất, cập nhật thư
viện, và khởi động lại widget. Cài đặt cũ (vị trí, màu, chế độ ổ cứng…) **được
giữ nguyên**.

```powershell
irm https://raw.githubusercontent.com/thenewnet/windows-widget-cpu/main/install.ps1 | iex
```

Lệnh này sẽ:
1. Tắt widget đang chạy (nếu có)
2. Tải lại `float_monitor.py` phiên bản mới nhất từ GitHub
3. Cập nhật thư viện trong môi trường sẵn có (nhanh, không tải lại từ đầu)
4. Mở lại widget với bản mới

> Không cần gỡ cài rồi cài lại. Chạy lại lệnh trên là đủ để lên bản mới.

**Gỡ cài đặt** cũng bằng 1 dòng:

```powershell
irm https://raw.githubusercontent.com/thenewnet/windows-widget-cpu/main/uninstall.ps1 | iex
```

## Cách chạy từ mã nguồn (nếu bạn đã clone repo)

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
**ổ cứng** · độ trong suốt · **màu sắc** · khởi động cùng Windows · thoát.

### Chế độ hiển thị ổ cứng

Chuột phải → **Ổ cứng**:
- **Dung lượng đã dùng (%)** — phần trăm dung lượng ổ hệ thống đã dùng (mặc định,
  ổn định). Nhãn hiển thị `DISK`.
- **Mức hoạt động I/O (%)** — phần trăm thời gian ổ đĩa đang bận đọc/ghi, giống
  cột *Active time* trong Task Manager. Nhãn đổi thành `I/O`.

Lựa chọn được lưu lại. (Nếu hệ thống không cung cấp số liệu I/O, mục này sẽ bị
làm mờ và widget dùng chế độ dung lượng.)

### Đổi màu

Chuột phải → **Màu sắc**:
- Chọn nhanh một trong 6 **bảng màu dựng sẵn**, hoặc
- **Tùy chỉnh màu {CPU/RAM/DISK/GPU}…** để mở bảng chọn màu và đặt màu riêng
  cho từng chỉ số. "Tùy chỉnh màu Mạng/nhấn…" đổi màu dòng tốc độ mạng và
  đường viền nhấn.

Màu, vị trí và mọi cài đặt được lưu lại tự động, giữ nguyên cho lần mở sau.

### Khởi động cùng Windows

Chuột phải → **Khởi động cùng Windows** (bật/tắt). Khi bật, widget tự chạy mỗi
lần đăng nhập (đăng ký ở `HKCU\...\Run`, không cần quyền admin).

## Ghi chú

- **Disk** mặc định hiển thị phần trăm **dung lượng đã dùng**. Bạn có thể đổi
  sang phần trăm **hoạt động I/O** trong menu chuột phải → **Ổ cứng**.
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
