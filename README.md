# Windows System Monitor Widget

Widget theo dõi hệ thống dành cho Windows 11, viết bằng Python và PySide6.
Ứng dụng hiển thị số liệu trực tiếp trên desktop với giao diện tối, nền trong
suốt tùy chỉnh và cửa sổ nhỏ gọn có thể kéo thả.

## Tính năng

| Thành phần | Thông tin hiển thị |
| --- | --- |
| CPU | Mức sử dụng, số logical processor, tần số nếu hệ thống hỗ trợ |
| RAM | Dung lượng đang dùng, tổng dung lượng và phần trăm sử dụng |
| GPU | Tên GPU, mức sử dụng và thông tin bộ nhớ tùy card/driver |
| Disk | Dung lượng đã dùng, tổng dung lượng và phần trăm của ổ được chọn |
| Network | Tốc độ download/upload hiện tại theo KB/s hoặc MB/s |
| Battery | Phần trăm pin và trạng thái nguồn điện; tự ẩn nếu không có pin |

Các chức năng desktop:

- Chọn ổ C, D, E hoặc ổ cục bộ/USB đang có trong Settings.
- Bật/tắt từng module; chọn chu kỳ cập nhật 1, 2 hoặc 5 giây.
- Chỉnh độ đục của nền từ 0% đến 100%, giữ chữ và số liệu rõ.
- Kéo thả widget, bật Always on Top, thu nhỏ xuống taskbar hoặc ẩn xuống tray.
- Lưu cấu hình và vị trí; đưa widget về vùng màn hình khi cần.
- Tùy chọn khởi động cùng Windows và ngăn chạy nhiều phiên trùng nhau.
- Bản executable không có console và không yêu cầu quyền Administrator.

## Tải và chạy

Bản executable được phân phối qua
[GitHub Releases](https://github.com/hinamikochi/windows-system-monitor/releases).

1. Mở trang Releases và chọn bản phát hành.
2. Trong **Assets**, tải **SystemMonitor.exe**.
3. Đặt file ở một thư mục cố định rồi nhấp đúp để chạy.

Bản executable dành cho **Windows 11 x64**, không cần cài Python.
Nếu chưa có bản phát hành trên GitHub, có thể chạy từ mã nguồn theo hướng dẫn bên dưới.

Khi cập nhật, chọn **Exit** ở tray để thoát phiên đang chạy trước khi thay
file hoặc mở bản mới. Mở ứng dụng lần nữa sẽ hiện phiên đang chạy thay vì
tạo thêm widget.

## Cách sử dụng

| Điều khiển | Chức năng |
| --- | --- |
| Kéo phần nền hoặc tiêu đề | Di chuyển widget |
| **⋯** | Mở Settings |
| **Pin** | Bật/tắt Always on Top |
| **−** | Thu nhỏ xuống taskbar, tiếp tục cập nhật |
| **×** hoặc Alt+F4 | Ẩn xuống system tray |
| **Exit** trong menu tray | Dừng theo dõi và thoát hoàn toàn |

Để tìm biểu tượng tray, nhìn cạnh đồng hồ ở góc dưới bên phải Windows;
nhấn **^** nếu biểu tượng đang nằm trong vùng ẩn. Nhấp phải biểu tượng
System Monitor để mở menu **Show / Hide**, **Always on Top**, **Settings**,
**Exit**. Nhấp đúp để ẩn/hiện; nếu cửa sổ đang thu nhỏ, thao tác này khôi phục cửa sổ.

Trong **Settings**:

- **Visible modules:** chọn thông tin cần hiển thị.
- **Disk drive:** chọn ổ cần theo dõi.
- **Refresh:** chọn chu kỳ cập nhật.
- **Background opacity:** 0% là nền hoàn toàn trong suốt, 100% là nền tối
  đặc; mặc định 65%. Chữ, nút và thanh tiến trình vẫn hiển thị.
- **Always on Top:** giữ widget phía trên các cửa sổ khác.
- **Start with Windows:** chạy ứng dụng khi đăng nhập Windows.
- **Save / Cancel:** áp dụng hoặc bỏ thay đổi.

Khi không có system tray, đóng cửa sổ sẽ thoát ứng dụng.

## Hỗ trợ phần cứng và cách đọc số liệu

**GPU:** NVIDIA dùng NVML thông qua `nvidia-ml-py`. Intel Iris Xe, AMD hoặc
hệ thống không có NVML dùng bộ đếm GPU của Windows qua PDH. Mức sử dụng
Windows được tính theo engine vật lý bận nhất sau khi cộng tải của các process
trên cùng engine.

Với Intel/Windows counters, **Shared** là RAM đang được GPU dùng chung;
**Dedicated** là bộ nhớ dành riêng đang sử dụng. Ứng dụng không giả định
RAM chia sẻ có dung lượng tối đa tương đương VRAM. Với nhiều adapter,
backend Windows hiển thị **Windows GPUs (all adapters)**: tải của engine bận
nhất và tổng bộ nhớ sử dụng. Chưa có lựa chọn từng GPU trong Settings.

**Disk:** mặc định theo dõi ổ chứa Windows. Chỉ hiển thị một ổ được chọn,
không cộng tất cả ổ. Danh sách gồm ổ cục bộ/USB, không gồm ổ mạng/CD-ROM.
Ổ bị tháo hoặc không truy cập được hiển thị `N/A`.

**Network:** số liệu là lưu lượng tổng các interface, gồm VPN/adapter ảo;
không phải tốc độ tối đa của đường truyền. CPU, Network và mức sử dụng GPU
Windows cần mẫu đầu để tạo baseline nên có thể hiển thị `N/A` lúc khởi động.

**RAM:** dung lượng sử dụng được tính bằng tổng trừ dung lượng available.

**Battery:** `Plugged in` cho biết máy có nguồn điện ngoài; không khẳng định
pin đang tăng dung lượng. Máy không có pin sẽ ẩn module này.

Chỉ số không được phần cứng/driver hỗ trợ sẽ hiển thị `N/A`.

## Chạy từ mã nguồn

Cần **Windows 11 x64**, **Python 3.12+** và Git nếu dùng lệnh clone.

```powershell
git clone https://github.com/hinamikochi/windows-system-monitor.git
cd windows-system-monitor
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Nếu đã tải ZIP mã nguồn, giải nén và mở Terminal tại thư mục chứa `main.py`,
sau đó chạy từ bước tạo môi trường ảo. Nếu dùng Python 3.13 hoặc mới hơn,
thay `-3.12` bằng phiên bản đã cài.

Không cần kích hoạt môi trường ảo hay thay đổi chính sách chạy script PowerShell.

## Build executable

Thoát ứng dụng trước khi build để Windows không khóa file executable.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\build.cmd
```

Kết quả mặc định: `dist\SystemMonitor.exe`.

`build.cmd` tạo icon và chạy cấu hình PyInstaller `SystemMonitor.spec`.
Script ưu tiên môi trường `.venv312` nếu thư mục này tồn tại; nếu không,
dùng `.venv`. Có thể build trực tiếp để chọn rõ môi trường:

```powershell
.\.venv\Scripts\python.exe scripts\generate_icon.py
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm SystemMonitor.spec
```

Để xuất sang thư mục khác:

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --distpath dist\update SystemMonitor.spec
```

`requirements-lock.txt` ghi các phiên bản của môi trường Windows/Python 3.12
đã dùng để kiểm thử và build. Có thể cài file này thay
`requirements-build.txt` để tái tạo môi trường.

Executable có icon nhúng, không console, chưa ký số và chưa có installer.

## Cấu hình, log và khởi động Windows

Dữ liệu người dùng được lưu ngoài thư mục executable:

```text
%LOCALAPPDATA%\SystemMonitorWidget\
├── config.json
└── app.log
```

Cấu hình được kiểm tra kiểu dữ liệu và ghi thay thế nguyên tử. File cấu hình
hỏng trở về mặc định; log được giới hạn dung lượng và xoay vòng.

**Start with Windows** mặc định tắt, sử dụng giá trị `SystemMonitorWidget` tại:

```text
HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run
```

Bản executable đăng ký đường dẫn exe; bản source đăng ký pythonw và main.py.
Sau khi di chuyển executable, mở bản tại vị trí mới và **Save** trong Settings
với Start with Windows bật để cập nhật đường dẫn. Trước khi xóa ứng dụng,
tắt tùy chọn này rồi chọn Exit.

## Kiểm thử

Chạy trong môi trường đã cài `requirements-build.txt`:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe tests\smoke_ui.py
.\.venv\Scripts\python.exe tests\smoke_desktop.py
.\.venv\Scripts\python.exe tests\smoke_package.py
.\.venv\Scripts\python.exe tests\smoke_package.py ".\dist\SystemMonitor.exe"
.\.venv\Scripts\python.exe tests\check_release.py ".\dist\SystemMonitor.exe"
```

Kiểm tra GPU độc lập:

```powershell
.\.venv\Scripts\python.exe tests\probe_gpu.py
```

Đã chạy trên Windows 11 với Python 3.12.10:

- 22 unit test cho thu thập dữ liệu, lỗi phần cứng, cấu hình, ổ đĩa và startup.
- Smoke test UI với dữ liệu thật; nền 0% trong suốt và chữ vẫn rõ.
- Smoke test Settings, thu nhỏ/khôi phục, đổi Pin khi thu nhỏ, tray hide/show,
  lưu vị trí, instance lock/IPC và dừng worker.
- Smoke test executable với cấu hình tạm, kiểm tra chạy trùng giữa source/exe
  và thoát tiến trình.
- Kiểm tra executable x64, icon, không console và không yêu cầu Administrator.
- Đọc số liệu thực tế của Intel Iris Xe và dung lượng ổ D.

Smoke test giao diện dùng Qt offscreen; thay đổi startup được mô phỏng,
không bật khởi động Windows trên máy kiểm thử. Cần kiểm tra tương tác thực tế
với taskbar/tray, kéo thả, Always on Top, nhiều màn hình, DPI và đăng nhập Windows.
Telemetry NVIDIA/AMD chưa được xác nhận trên phần cứng thật.

Ảnh preview nằm tại `build\ui-preview.png`. Lệnh `check_release.py` tạo
`release-info.json` cạnh executable, chứa SHA-256 và thông tin file.

## Cấu trúc dự án

```text
system_monitor/
├── app.py          # Khởi tạo ứng dụng
├── ui/             # Widget và Settings
├── monitoring/     # CPU, RAM, GPU, Disk, Network, Battery
├── services/       # Worker, tray, startup và single instance
├── config/         # JSON store và kiểm tra cấu hình
└── assets/         # Icon
scripts/            # Tạo tài nguyên build
tests/              # Unit test và smoke test
main.py             # Entry point
SystemMonitor.spec  # Cấu hình PyInstaller
build.cmd           # Script build Windows
```

Một worker cố định thu thập dữ liệu bằng QTimer; GUI nhận snapshot qua signal.
Module bị tắt không được polling. Không tạo thread mới mỗi lần cập nhật.

