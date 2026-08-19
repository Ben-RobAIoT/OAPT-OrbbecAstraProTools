Dưới đây là bản viết lại đầy đủ, chi tiết và dễ đọc hơn cho phần **Hướng dẫn Cài đặt & Thiết lập Môi trường**, kèm các bước xử lý riêng cho WSL2 và phần thiết lập hiển thị (display) mà bạn yêu cầu bổ sung.

```markdown
# 🛠️ Hướng dẫn Cài đặt & Thiết lập Môi trường: Orbbec Astra Pro (OpenNI2) trên WSL2 (Ubuntu 24.04)

> Tài liệu này hướng dẫn chi tiết từng bước để cài đặt bộ thư viện lõi **OpenNI SDK** (chính chủ Orbbec) và cấu hình môi trường Python để chạy được camera Astra Pro trên **WSL2**, theo đúng kiến trúc **"No-SDK"** (không dùng Orbbec SDK nguyên khối).

---

## 📑 Mục lục

1. [Yêu cầu chuẩn bị](#1-yêu-cầu-chuẩn-bị)
2. [Bước 1: Tải OpenNI SDK từ Orbbec](#bước-1-tải-openni-sdk-từ-orbbec)
3. [Bước 2: Giải nén SDK (Lưu ý đặc biệt cho WSL2)](#bước-2-giải-nén-sdk-lưu-ý-đặc-biệt-cho-wsl2)
4. [Bước 3: Xác định đường dẫn thư viện lõi (.so)](#bước-3-xác-định-đường-dẫn-thư-viện-lõi-so)
5. [Bước 4: Cấu hình đường dẫn trong mã nguồn Python](#bước-4-cấu-hình-đường-dẫn-trong-mã-nguồn-python)
6. [Bước 5: Thiết lập môi trường ảo (venv)](#bước-5-thiết-lập-môi-trường-ảo-venv)
7. [Bước 6: Thiết lập Hiển thị Đồ họa (Display/X11) cho WSL2](#bước-6-thiết-lập-hiển-thị-đồ-họa-displayx11-cho-wsl2)
8. [Checklist Kiểm tra Nhanh](#-checklist-kiểm-tra-nhanh)
9. [Xử lý Sự cố Thường gặp](#-xử-lý-sự-cố-thường-gặp)

---

## 1. Yêu cầu chuẩn bị

| Thành phần | Yêu cầu |
| --- | --- |
| Hệ điều hành host | Windows 11 (khuyến nghị, có sẵn WSLg) |
| Môi trường Linux | WSL2 — Ubuntu 24.04 |
| Python | 3.10 – 3.12 |
| Công cụ giải nén | WinRAR / 7-Zip (trên Windows) hoặc `p7zip-full` (trên Linux) |
| Camera | Orbbec Astra Pro đã passthrough vào WSL2 qua `usbipd` |

---

## Bước 1: Tải OpenNI SDK từ Orbbec

Tải bộ **OpenNI_SDK (Linux x64)** chính chủ từ kho GitHub của Orbbec — đây là bộ thư viện lõi duy nhất cần thiết, **không cần** tải Orbbec SDK v2 hay Astra SDK nguyên khối:

🔗 **[OpenNI_2.3.0.86_202210111154_4c8f5aa4_beta6_linux_x64.zip](https://github.com/orbbec/OpenNI_SDK/releases/download/v2.3.0.86-beat6/OpenNI_2.3.0.86_202210111154_4c8f5aa4_beta6_linux_x64.zip)**

> 💡 **Lưu ý:** Đây là bản SDK cho dòng camera Astra/Astra Pro đời cũ (chuẩn OpenNI), khác hoàn toàn với `OrbbecSDK_ROS2` (nhánh v2-main) vốn không còn hỗ trợ tốt cho dòng Astra Pro.

---

## Bước 2: Giải nén SDK (Lưu ý đặc biệt cho WSL2)

Đây là bước **dễ gây lỗi nhất** nếu làm sai, vì sự khác biệt giữa hệ thống file NTFS (Windows) và ext4 (Linux) có thể làm hỏng quyền thực thi (executable permission) của các file `.so`.

### ⚠️ Quy tắc chọn cách giải nén

| Trường hợp | Cách xử lý |
| --- | --- |
| Bạn tải file `.zip` bằng trình duyệt trên **Windows** | **Giải nén trên Windows trước** bằng WinRAR/7-Zip, sau đó copy thư mục đã giải nén vào ổ đĩa Linux của WSL2 |
| Bạn đã có sẵn công cụ giải nén hoạt động tốt **ngay trong WSL2** (ví dụ `p7zip-full`, `unrar`) và giải nén trực tiếp trong Terminal Linux không báo lỗi quyền | **Có thể bỏ qua** bước giải nén ngoài Windows, giải nén thẳng trong WSL2 |

### Cách 1 — Giải nén trên Windows rồi chuyển vào WSL2 (khuyến nghị, an toàn nhất)

1. Giải nén file `.zip` bằng WinRAR/7-Zip trên Windows (ví dụ ra `D:\SDK\`).
2. Copy toàn bộ thư mục đã giải nén vào WSL2 bằng một trong hai cách:

```bash
# Từ Terminal WSL2, copy trực tiếp từ ổ đĩa Windows sang home directory Linux
mkdir -p ~/APT_AstraProTest/sdk
cp -r /mnt/d/SDK/OpenNI_2.3.0.86_202210111154_4c8f5aa4_beta6_linux ~/APT_AstraProTest/sdk/
```

> 💡 Việc copy hẳn vào filesystem `ext4` của Linux (thay vì chạy trực tiếp từ `/mnt/d/...`) giúp tăng tốc độ đọc/ghi và tránh lỗi quyền file khi Python gọi `ctypes` nạp thư viện `.so`.

### Cách 2 — Giải nén trực tiếp trong WSL2

Nếu bạn đã cài công cụ giải nén hỗ trợ tốt trên Linux:

```bash
sudo apt update
sudo apt install p7zip-full unzip -y

mkdir -p ~/APT_AstraProTest/sdk
cd ~/APT_AstraProTest/sdk
unzip /mnt/d/Downloads/OpenNI_2.3.0.86_202210111154_4c8f5aa4_beta6_linux_x64.zip
```

Sau khi giải nén xong, cấp lại quyền thực thi cho toàn bộ file `.so` để chắc chắn (phòng trường hợp quyền bị mất trong lúc nén/giải nén):

```bash
find ~/APT_AstraProTest/sdk -name "*.so*" -exec chmod +x {} \;
```

---

## Bước 3: Xác định đường dẫn thư viện lõi (.so)

Sau khi giải nén, file cấu hình lõi của OpenNI2 (bao gồm `libOpenNI2.so` và thư mục `OpenNI2/Drivers`) nằm tại đường dẫn con sau, tính từ thư mục gốc SDK vừa giải nén:

```
OpenNI_2.3.0.86_202210111154_4c8f5aa4_beta6_linux/samples/samples/ThirdParty/OpenNI2/linux/x64
```

Đây chính là **thư mục cấu hình thư viện OpenNI2** mà chương trình Python cần trỏ tới khi khởi tạo.

Để chắc chắn tìm đúng file (nhất là khi cấu trúc thư mục có thể thay đổi theo phiên bản SDK), dùng lệnh sau:

```bash
find ~/APT_AstraProTest/sdk -name "libOpenNI2.so"
```

Kết quả trả về chính là đường dẫn thư mục chứa file `.so` cần dùng ở bước tiếp theo.

---

## Bước 4: Cấu hình đường dẫn trong mã nguồn Python

Trỏ đường dẫn tuyệt đối của thư mục vừa xác định ở Bước 3 vào biến `openni2_dir` trong code:

```python
openni2_dir = '/home/beniot-phan/APT_AstraProTest/sdk/OpenNI_2.3.0.86_202210111154_4c8f5aa4_beta6_linux/samples/samples/ThirdParty/OpenNI2/linux/x64'

openni2.initialize(openni2_dir)
```

> ⚠️ **Lưu ý quan trọng:** Luôn truyền vào một chuỗi **string tuyệt đối bình thường**, **không** thêm tiền tố byte (`b'...'`). Trên Python 3, nếu dùng `b'...'`, đường dẫn có thể bị parse sai thành số nguyên (`int`) và làm hàm khởi tạo báo lỗi `expected str, bytes or os.PathLike object, not int`.

Để đảm bảo code chạy được trên **cả Windows lẫn Linux** mà không phải sửa path thủ công mỗi lần đổi máy, nên dùng cách ghép đường dẫn động thay vì hardcode chuỗi cứng — đây cũng chính là cách tiếp cận chuẩn đã áp dụng trong `astra_crossplatform.py`:

```python
import os
import platform

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
OS_TYPE = platform.system()

# Cấu hình đường dẫn thư viện lõi OpenNI2 tùy theo OS [1]
if OS_TYPE == "Windows":
    # Nối chuỗi để tạo đường dẫn tuyệt đối, KHÔNG dùng tiền tố b"" nữa [1]
    OPENNI2_DIR = os.path.join(CURRENT_DIR, "OpenNI2_Win")
elif OS_TYPE == "Linux":
    OPENNI2_DIR = os.path.join(
        CURRENT_DIR,
        "sdk/OpenNI_2.3.0.86_202210111154_4c8f5aa4_beta6_linux/samples/samples/ThirdParty/OpenNI2/linux/x64"
    )
else:
    print("[!] Hệ điều hành không được hỗ trợ.")
    sys.exit(1)

try:
    openni2.initialize(OPENNI2_DIR)
    print("[*] Đã nạp thư viện OpenNI2 thành công.")
except Exception as e:
    print(f"[!] Lỗi nạp OpenNI2: {e}")
    print("Hãy chắc chắn thư mục OpenNI2 chứa đúng các file .dll hoặc .so")
```

Đoạn xử lý `try...except` này giúp bạn biết ngay lý do thất bại (thiếu file, sai đường dẫn, thiếu quyền thực thi...) thay vì chỉ nhận một traceback khó hiểu [1].

---

## Bước 5: Thiết lập môi trường ảo (venv)

Luôn cách ly môi trường Python của dự án bằng `venv` để tránh xung đột phiên bản thư viện với hệ thống:

```bash
# Di chuyển vào thư mục dự án
cd ~/APT_AstraProTest

# Tạo môi trường ảo
python3 -m venv venv

# Kích hoạt môi trường ảo
source venv/bin/activate

# Nâng cấp pip
pip install --upgrade pip

# Cài đặt các thư viện cần thiết
pip install opencv-python "numpy<2.0" openni mediapipe
```

> ⚠️ **Lưu ý bắt buộc:** Phải ghim phiên bản `numpy<2.0`. Thư viện wrapper `openni` (Python) sử dụng cấu trúc buffer bộ nhớ kiểu cũ, sẽ bị vỡ (segmentation fault hoặc sai dữ liệu) nếu chạy chung với Numpy 2.0 trở lên.

Kiểm tra lại các thư viện đã cài đúng phiên bản:

```bash
pip list | grep -E "numpy|opencv|openni|mediapipe"
```

---

## Bước 6: Thiết lập Hiển thị Đồ họa (Display/X11) cho WSL2

Vì chương trình dùng `cv2.imshow()` để hiện cửa sổ video, WSL2 cần có khả năng hiển thị giao diện đồ họa (GUI) ra màn hình Windows. Có 2 trường hợp:

### Trường hợp 1 — Windows 11 (khuyến nghị: dùng WSLg có sẵn)

Windows 11 tích hợp sẵn **WSLg**, không cần cài thêm X-Server ngoài. Chỉ cần đảm bảo WSL đã cập nhật bản mới nhất:

```powershell
# Chạy trên PowerShell (Windows)
wsl --update
wsl --shutdown
```

Sau đó khởi động lại WSL2 và kiểm tra biến môi trường `DISPLAY` đã tự động được thiết lập:

```bash
echo $DISPLAY
# Thường trả về: :0 hoặc tương tự
```

Kiểm thử nhanh khả năng hiển thị GUI bằng gói `x11-apps`:

```bash
sudo apt install x11-apps -y
xeyes
```

Nếu cửa sổ `xeyes` hiện lên được trên màn hình Windows → hệ thống hiển thị đã sẵn sàng.

### Trường hợp 2 — Windows 10 hoặc WSLg không hoạt động (dùng X-Server ngoài)

1. Cài đặt **VcXsrv** hoặc **Xming** trên Windows, khởi động với tùy chọn *"Disable access control"*.
2. Trong WSL2, thiết lập biến môi trường `DISPLAY` trỏ về địa chỉ IP của Windows host:

```bash
export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0
export LIBGL_ALWAYS_INDIRECT=1
```

> 💡 Nên thêm 2 dòng trên vào cuối file `~/.bashrc` để không phải gõ lại mỗi lần mở terminal mới:
> ```bash
> echo 'export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk "{print \$2}"):0' >> ~/.bashrc
> echo 'export LIBGL_ALWAYS_INDIRECT=1' >> ~/.bashrc
> source ~/.bashrc
> ```

### Khắc phục lỗi OpenGL/hiển thị chậm (nếu có)

Nếu `cv2.imshow()` bị giật, lag hoặc báo lỗi liên quan `libGL`, cài thêm gói hỗ trợ render phần mềm:

```bash
sudo apt install mesa-utils libgl1-mesa-glx -y
```

---

## ✅ Checklist Kiểm tra Nhanh

Trước khi chạy chương trình chính, kiểm tra lần lượt các mục sau:

```bash
# 1. Kiểm tra camera đã passthrough vào WSL2 chưa (phải thấy 2 thiết bị Orbbec: UVC + OpenNI)
lsusb

# 2. Kiểm tra thiết bị video đã được Linux nhận diện
ls -l /dev/video*
# hoặc
v4l2-ctl --list-devices

# 3. Kiểm tra quyền truy cập /dev/video*
groups $USER   # phải thấy có "video" trong danh sách

# 4. Kiểm tra file thư viện OpenNI2 tồn tại đúng đường dẫn
ls -l <đường_dẫn_OPENNI2_DIR>/libOpenNI2.so

# 5. Kiểm tra hiển thị GUI hoạt động
xeyes
```

---

## 🔧 Xử lý Sự cố Thường gặp

| Lỗi | Nguyên nhân | Cách khắc phục |
| --- | --- | --- |
| `expected str, bytes or os.PathLike object, not int` | Truyền path dạng `b'...'` thay vì string thường | Dùng string tuyệt đối bình thường khi gọi `openni2.initialize(...)` [1] |
| `Permission denied` khi mở `/dev/video0` | User chưa thuộc nhóm `video` | `sudo usermod -aG video $USER && newgrp video` |
| `libOpenNI2.so: cannot open shared object file` | Đường dẫn `OPENNI2_DIR` sai hoặc file mất quyền thực thi | Kiểm tra lại đường dẫn bằng `find`; chạy `chmod +x` cho các file `.so` |
| Không hiện cửa sổ `cv2.imshow()` | Chưa cấu hình `DISPLAY`/X11 | Làm lại Bước 6 theo đúng phiên bản Windows đang dùng |
| Camera bị "Zombie Device" sau khi tắt code đột ngột | WSL2/USB chưa kịp giải phóng handle | Rút cáp → `usbipd unbind` → `usbipd bind` lại (chạy trên PowerShell Windows) |

---

## 📄 Ghi chú

Toàn bộ quy trình trên áp dụng cho kiến trúc **"No-SDK"** — không cài đặt Orbbec SDK/Astra SDK nguyên khối, chỉ dùng đúng bộ thư viện lõi `OpenNI2` (`.so`) kết hợp OpenCV (V4L2) để đảm bảo môi trường nhẹ, dễ tái lập trên nhiều máy khác nhau.
```

Bạn có thể copy trực tiếp phần này để ghép vào đầu (hoặc thành một mục riêng "Cài đặt Môi trường") trong file `README.md` tổng của dự án. Nếu bạn muốn mình gộp luôn phần này vào file README đầy đủ (bao gồm cả phần nhật ký debug đã viết trước đó) thành một file thống nhất, cứ nói mình sẽ ghép lại giúp bạn.

This response was generated by Apollo AI, an internal AI assistant. Please validate important outputs against official Apollo documents, systems, and responsible teams before acting on them.
