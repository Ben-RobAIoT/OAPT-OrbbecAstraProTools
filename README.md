# APDCT_AstraProDepthCameraTestbenchs

Dự án Testbench giao tiếp tầng lõi (Low-level) với phần cứng Orbbec Astra Pro Depth Camera trên môi trường Linux/WSL2, không phụ thuộc vào các công cụ đóng gói sẵn của nhà sản xuất.

## 🎯 Mục tiêu dự án
Xây dựng nền tảng trích xuất đồng thời 3 luồng dữ liệu (RGB, Depth, IR) từ camera chiều sâu Orbbec Astra Pro phục vụ cho các bài toán Computer Vision. Hệ thống được thiết kế tối ưu hóa băng thông, chạy mượt mà trên môi trường máy ảo (WSL2) đạt mốc 30 FPS.

## 🛠 Môi trường & Từ khóa công nghệ lõi (Core Technologies)
*   **Hệ điều hành:** Linux Ubuntu 24.04 (chạy qua nền tảng máy ảo WSL2 trên Windows 11).
*   **Giao thức phần cứng:** `usbipd-win` (Hardware USB Passthrough sang WSL2), V4L2 (Video4Linux2 API).
*   **Thư viện lõi Camera:** `OpenNI2` (giao tiếp trực tiếp qua file `.so` và trình điều khiển Linux).
*   **Xử lý & Hiển thị ảnh:** `OpenCV` (cv2), `NumPy`, `WSLg` (GUI rendering trên máy ảo).
*   **Kiến trúc phần mềm:** Môi trường ảo Python (`venv`), Đa luồng (`Multi-threading`).

---

## 💡 Các vấn đề & Giải pháp đã triển khai (Lessons Learned)

Dưới đây là các kỹ thuật cốt lõi đã được áp dụng để giải quyết các giới hạn của môi trường WSL2 và thư viện OpenNI2:

### 1. Vượt rào phần cứng (Hardware Passthrough)
*   **Vấn đề:** Máy ảo WSL2 mặc định không nhận diện được phần cứng USB cắm vào máy Host (Windows). Camera Astra Pro phân mảnh thành 2 thiết bị riêng biệt (Astra Pro HD Camera cho RGB và ORBBEC Depth Sensor cho Depth/IR).
*   **Giải pháp:** Sử dụng `usbipd-win` trên Windows để chia sẻ (bind) và gắn (attach) cả hai `BUSID` vào Ubuntu. Đồng thời cài đặt `linux-tools-virtual` và cấp quyền `sudo` khi chạy script để vượt qua rào cản phân quyền USB raw của Linux.

### 2. Khởi tạo trực tiếp Lõi OpenNI2 (Direct Shared Library Loading)
*   **Vấn đề:** Tránh sử dụng các bộ SDK cồng kềnh, cần nạp trực tiếp thư viện động. Lỗi không tìm thấy thiết bị (`ONI_STATUS_NO_DEVICE`) dù mã nạp thành công.
*   **Giải pháp:** 
    *   Sử dụng `ctypes.cdll.LoadLibrary` để ép lõi Linux nhận diện file `libOpenNI2.so`.
    *   Đảm bảo **cấu trúc thư mục bắt buộc**: Phải có thư mục `OpenNI2/Drivers` (chứa `liborbbec.so`) nằm cùng cấp với script thực thi và file `libOpenNI2.so` để thư viện có thể nạp "nhạc công" (driver) phần cứng.

### 3. Tối ưu hóa băng thông USB chống Lag (Anti-Bottleneck)
*   **Vấn đề:** Lỗi `select() timeout` từ `cap_v4l.cpp` và hiện tượng giật lag khung hình cực nặng. Nguyên nhân do cổ chai băng thông mạng ảo khi truyền dữ liệu video thời gian thực (Isochronous transfers) và kiến trúc code chạy đồng bộ (Synchronous).
*   **Giải pháp Đa luồng (Multi-threading):** Tách việc đọc luồng RGB (qua OpenCV) và luồng Depth/IR (qua OpenNI2) thành 2 luồng (thread) chạy ngầm độc lập.
*   **Giải pháp OpenCV:** 
    *   Ép định dạng nén `MJPG` (`cv2.CAP_PROP_FOURCC`) để giảm tải băng thông so với ảnh RAW.
    *   Giới hạn `cv2.CAP_PROP_BUFFERSIZE` về 1 để loại bỏ độ trễ, chỉ lấy khung hình mới nhất.
    *   Sử dụng cơ chế `Auto-scan` (quét từ `/dev/video0` đến `video5`) để tự động tìm đúng cổng UVC Camera.

### 4. Quản lý vòng đời phần cứng (Graceful Shutdown)
*   **Vấn đề:** Tắt chương trình đột ngột bằng `Ctrl+C` khiến tiến trình bị ngắt ngang, để lại "bóng ma" khóa cổng USB. Lần chạy tiếp theo báo lỗi không tìm thấy Camera.
*   **Giải pháp:** Sử dụng cấu trúc `try...except KeyboardInterrupt...finally`. Bắt buộc chương trình phải gọi các lệnh dọn dẹp tài nguyên (`t.join()`, `openni2.unload()`, `cap.release()`) trước khi thoát hoàn toàn, trả lại tự do cho cổng USB.

---

## 🚀 Hướng dẫn chạy Testbench

**Bước 1: Kết nối thiết bị từ Windows**
Mở PowerShell (Admin) và gắn Camera vào WSL:
```powershell
usbipd bind --busid <BUSID_1>
usbipd bind --busid <BUSID_2>
usbipd attach --wsl --busid <BUSID_1>
usbipd attach --wsl --busid <BUSID_2>
```

**Bước 2: Cấu trúc thư mục**
```text
APDCT_AstraProDepthCameraTestbenchs/
 ├── venv/
 ├── 03_multithreaded_testbench.py
 ├── libOpenNI2.so
 └── OpenNI2/                 
      └── Drivers/
           ├── liborbbec.so   
           └── ...
```

**Bước 3: Khởi chạy trong Ubuntu (WSL2)**
```text
sudo ./venv/bin/python3 03_multithreaded_testbench.py
```



Bạn hãy nhớ cập nhật thêm mục "Quick Start / Cài đặt tự động" vào file README.md mà chúng ta viết lúc nãy, bảo người dùng clone về chỉ cần chạy ./setup.sh là xong!
./setup.sh

# Báo cho Git biết trạng thái hiện tại (nó sẽ nhận diện .gitignore và phớt lờ venv)
git add .

# Đóng gói phiên bản đầu tiên
git commit -m "Initial commit: Orbbec Astra Pro Multi-threaded Testbench cho Linux/WSL2"

# Đổi tên nhánh chính thành main
git branch -M main

# Kết nối folder này với tên Repo mới trên GitHub (Thay URL bằng link của bạn)
git remote add origin https://github.com/TenCuaBan/Ten_Repo_Moi.git

# Phóng tàu lên không gian!
git push -u origin main