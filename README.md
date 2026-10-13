# Windows 11 System Monitor Widget

Ứng dụng desktop Python/PySide6, đã triển khai Phase 1–4: CPU, RAM, GPU,
Disk, Network, Battery; Settings; System Tray; lưu cấu hình và vị trí; chống
chạy trùng; tích hợp khởi động Windows; đóng gói executable không có console.

## Chạy ngay

**Bản mới có nền trong suốt, nút thu nhỏ và lựa chọn ổ C/D/E:** mở `dist\update\SystemMonitor.exe`.
Bản cũ ở `dist\SystemMonitor.exe` đang chạy nên Windows khóa file khi build;
bản cập nhật được xuất vào thư mục riêng. Chọn **Exit** ở tray trước khi mở
bản mới. Nếu đã bật Start with Windows, mở Settings của bản mới và Save với
tùy chọn đó bật để cập nhật đường dẫn khởi động.

Mở file exe bằng cách nhấp đúp. Bản đóng gói không cần cài
Python. Nếu widget đang chạy từ mã nguồn, hãy chọn **Exit** ở tray trước khi
mở bản exe; nếu mở lần nữa, ứng dụng chỉ hiện phiên đang chạy.

Để chạy từ mã nguồn trong môi trường Python 3.12 đã chuẩn bị:

```powershell
cd "D:\System Monitor Widget"
.\.venv312\Scripts\python.exe main.py
```

Môi trường `.venv` cũ (Python 3.11) vẫn dùng được, nhưng bản release được
build và kiểm thử bằng Python 3.12.10 trong `.venv312`.

## Sử dụng

- Kéo phần nền hoặc tiêu đề để di chuyển widget.
- **Pin** bật/tắt Always on Top.
- **⋯** mở Settings; chọn module, **Background opacity** 0–100%, chu kỳ 1/2/5 giây,
  Always on Top, hoặc Start with Windows. **Save** áp dụng; **Cancel** bỏ thay đổi.
- **×** hoặc Alt+F4 ẩn widget xuống tray và tiếp tục theo dõi.
- **−** thu nhỏ xuống taskbar; nhấp biểu tượng ở taskbar hoặc Show / Hide
  trong tray để khôi phục. Khi thu nhỏ, dữ liệu vẫn cập nhật và vị trí bình
  thường của cửa sổ được lưu.
- Nền mặc định có độ đục 65%. Chọn 0% để nền hoàn toàn trong suốt, 100% để
  nền tối đặc. Chữ, số và nút giữ độ rõ; thanh tiến trình vẫn có màu. Thiết lập
  opacity cũ của toàn cửa sổ được thay bằng Background opacity riêng cho nền.
- Nhấp phải biểu tượng tray: **Show / Hide**, **Always on Top**, **Settings**,
  **Exit**. Nhấp đúp biểu tượng để ẩn/hiện.
- **Exit** dừng timer, giải phóng GPU, dừng worker và thoát tiến trình.
- Nếu không có system tray, đóng cửa sổ sẽ thoát; widget không bị ẩn mất.
- Vị trí được lưu khi ẩn hoặc thoát. Khi mở lại, thay đổi độ phân giải hoặc
  tháo màn hình, vị trí được giới hạn về vùng màn hình còn sử dụng.

## Dữ liệu và phần cứng

CPU/network hiển thị N/A ở mẫu đầu để tạo baseline. Network là lưu lượng
tổng các interface, gồm cả VPN/adapter ảo, không phải tốc độ đường truyền tối đa.
RAM sử dụng được tính bằng tổng trừ available. Trong Settings, chọn **Disk drive**
để chuyển giữa C, D, E hoặc các ổ cục bộ/USB đang có. Mặc định là ổ chứa Windows.
Ổ đã chọn được lưu khi mở lại; nếu ổ bị tháo hoặc không truy cập được, Disk
hiển thị N/A. Không cộng dung lượng các ổ và không liệt kê ổ mạng/CD-ROM.

GPU dùng `nvidia-ml-py`/NVML với GPU NVIDIA đầu tiên được driver cung cấp.
Mức sử dụng và VRAM phụ thuộc card/driver; chỉ số không hỗ trợ hiển thị N/A.
Với Intel Iris Xe/AMD hoặc không có NVML, ứng dụng dùng bộ đếm GPU Engine
và GPU Adapter Memory qua PDH của Windows, không gọi PowerShell mỗi giây.
Tên adapter được lấy bằng EnumDisplayDevices. Mức sử dụng cộng các process
trên từng engine vật lý rồi chọn engine bận nhất, giới hạn 0–100%.
Shared là RAM đang dùng chung cho GPU; Dedicated là bộ nhớ GPU dành riêng
đang sử dụng. Không giả định dung lượng tối đa của RAM chia sẻ là VRAM.
Mẫu đầu hoặc driver/bộ đếm không hỗ trợ sẽ hiển thị N/A.
Nếu Windows liệt kê nhiều adapter, nhãn là Windows GPUs (all adapters):
mức sử dụng là engine bận nhất giữa các adapter, bộ nhớ là tổng sử dụng.
Chưa có chọn từng GPU trong Settings.

Battery tự ẩn nếu máy không có pin. Trạng thái plugged-in cho biết có nguồn
điện ngoài, không khẳng định pin đang tăng dung lượng.

Module bị tắt không được polling. Một worker cố định và một QTimer thu thập
dữ liệu; GUI nhận snapshot qua signal. Thanh tiến trình animate 350 ms.
Không yêu cầu Administrator.

## Cấu hình và khởi động cùng Windows

Cấu hình: `%LOCALAPPDATA%\SystemMonitorWidget\config.json`.
Log có giới hạn dung lượng: `%LOCALAPPDATA%\SystemMonitorWidget\app.log`.
JSON được kiểm tra kiểu dữ liệu và ghi thay thế nguyên tử; file hỏng trở về
mặc định. Lock và kênh IPC cục bộ ngăn chạy trùng giữa source và exe.

Start with Windows chỉ thay đổi giá trị `SystemMonitorWidget` ở:
`HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`.
Mặc định tắt. Từ source, đường dẫn pythonw và main.py được đăng ký; từ exe,
đường dẫn exe được đăng ký. Hãy đặt exe ở vị trí cố định trước khi bật.
Nếu di chuyển exe, tắt rồi bật lại tùy chọn này tại vị trí mới.
Trước khi xóa ứng dụng, tắt Start with Windows rồi chọn Exit.

## Cài đặt mới và build

Cần Windows 11 x64, Python 3.12+.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\build.cmd
```

`build.cmd` ưu tiên `.venv312` nếu có, nếu không dùng `.venv`.
Có cả `build.ps1`, nhưng máy có chính sách chặn script PowerShell thì dùng
`build.cmd` hoặc lệnh trực tiếp:

```powershell
.\.venv312\Scripts\python.exe scripts\generate_icon.py
.\.venv312\Scripts\python.exe -m PyInstaller --noconfirm SystemMonitor.spec
```

Kết quả: `dist\SystemMonitor.exe`, một file exe, không console.
Icon được nhúng; cấu hình luôn nằm ngoài thư mục giải nén tạm của PyInstaller.
`requirements-lock.txt` ghi phiên bản chính xác của môi trường build hiện tại.
Có thể cài file này thay requirements-build.txt để tái tạo môi trường.
Exe chưa ký số và chưa có installer.

## Kiểm thử

```powershell
.\.venv312\Scripts\python.exe -m unittest discover -s tests -v
.\.venv312\Scripts\python.exe tests\smoke_ui.py
.\.venv312\Scripts\python.exe tests\smoke_desktop.py
.\.venv312\Scripts\python.exe tests\smoke_package.py
.\.venv312\Scripts\python.exe tests\smoke_package.py ".\dist\update\SystemMonitor.exe" 'D:\'
.\.venv312\Scripts\python.exe tests\check_release.py ".\dist\update\SystemMonitor.exe"
```

Smoke tests dùng Qt offscreen và thư mục cấu hình tạm. Kiểm thử Settings
mô phỏng thay đổi registry, không bật khởi động Windows trên máy kiểm thử.
Ảnh preview được tạo tại `build\ui-preview.png`.

Đã chạy trên Windows 11/Python 3.12.10: 22 unit test, UI cập nhật dữ liệu thật,
worker shutdown, Settings, lọc module, Pin flag, tray hide/show, JSON, phục hồi
vị trí và instance lock/IPC đều qua. Kiểm thử ảnh xác nhận nền 0% có alpha 0,
chữ vẫn rõ. Thu nhỏ, đổi Pin khi thu nhỏ, giữ vị trí bình thường và khôi phục
qua tray đã qua smoke test offscreen; taskbar Windows vẫn cần kiểm tra tương tác.
Đã đọc thực tế Intel(R) Iris(R) Xe Graphics:
khoảng 3.4–3.6% sử dụng, khoảng 1.6 GiB shared và 0 dedicated tại thời điểm
probe. Số liệu thay đổi theo tải máy. Không khẳng định đã thử telemetry trên
GPU NVIDIA/AMD. Probe độc lập: `python tests/probe_gpu.py`.

Chính bản exe cập nhật Intel đã qua smoke test với 10 mẫu dữ liệu thật, đọc
mức sử dụng và shared memory của Iris Xe, lưu cấu hình, chặn
phiên source mở trùng và thoát hoàn toàn. Kiểm tra PE xác nhận x64, có icon,
GUI subsystem (không console) và manifest asInvoker (không yêu cầu Admin).
File release khoảng 36.8 MiB; SHA-256 và thông tin build có trong
`dist/update/release-info.json`.

Cần kiểm tra thủ công: kéo thả native, tương tác tray Windows, Always on Top
trên ứng dụng khác, DPI 100/150/200%, nhiều màn hình và khởi động sau đăng nhập.
Smoke offscreen không xác nhận các hành vi này.

## Kiến trúc

- `ui/`: widget, progress animation và Settings dialog.
- `monitoring/`: psutil collector và GPU provider.
- `services/`: worker lifecycle, tray/controller, startup và single instance.
- `config/`: schema validation, JSON store và đường dẫn dữ liệu.
- `assets/`: icon; `scripts/`: tạo icon; `tests/`: kiểm thử.
