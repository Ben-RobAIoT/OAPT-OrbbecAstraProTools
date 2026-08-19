Dưới đây là file `README.md` hoàn chỉnh, trình bày lại toàn bộ nhật ký phát triển dự án Astra Pro x MediaPipe trên WSL2, giữ nguyên đầy đủ nội dung gốc và định dạng chuyên nghiệp để bạn copy trực tiếp vào GitHub.

# 📘 Nhật Ký Phát Triển: Astra Pro x MediaPipe trên WSL2 (Ubuntu 24.04)

[![Platform](https://img.shields.io/badge/Platform-WSL2%20(Ubuntu%2024.04)-orange)]()
[![Python](https://img.shields.io/badge/Python-3.12-blue)]()
[![OpenCV](https://img.shields.io/badge/OpenCV-V4L2-green)]()
[![OpenNI2](https://img.shields.io/badge/OpenNI2-Depth%2016--bit-lightgrey)]()
[![MediaPipe](https://img.shields.io/badge/AI-MediaPipe%20Hand%20Tracking-red)]()

> Tài liệu ghi lại toàn bộ hành trình debug thực chiến khi tích hợp camera Orbbec Astra Pro với AI MediaPipe Hand Tracking, chạy trên môi trường WSL2 (Ubuntu 24.04) trên nền Windows 11 — theo kiến trúc **"No-SDK"**.

---

## 📑 Mục lục

- [1. Tổng quan Dự án](#1-tổng-quan-dự-án)
- [2. Nhật Ký Debug & Các Lỗi Kinh Điển Đi Kèm](#2-nhật-ký-debug--các-lỗi-kinh-điển-đi-kèm)
  - [Giai đoạn 1: Chuẩn bị Môi trường & Xung đột Thư viện nền](#giai-đoạn-1-chuẩn-bị-môi-trường--xung-đột-thư-viện-nền)
  - [Giai đoạn 2: Lạc lối trong Ma trận SDK của Orbbec](#giai-đoạn-2-lạc-lối-trong-ma-trận-sdk-của-orbbec)
  - [Giai đoạn 3: Phân quyền Linux (Quyền truy cập Video)](#giai-đoạn-3-phân-quyền-linux-quyền-truy-cập-video)
  - [Giai đoạn 4: Lỗi MediaPipe "Bay màu" Name Space](#giai-đoạn-4-lỗi-mediapipe-bay-màu-name-space)
  - [Giai đoạn 5: Cú lừa "Byte String" của Python 3](#giai-đoạn-5-cú-lừa-byte-string-của-python-3)
  - [Giai đoạn 6: Giới hạn Phần cứng & Nghẽn Cổ chai USB](#giai-đoạn-6-giới-hạn-phần-cứng--nghẽn-cổ-chai-usb)
- [3. Các Từ khóa & Lệnh quan trọng cần nhớ](#3-các-từ-khóa--lệnh-quan-trọng-cần-nhớ)
- [4. Mã Nguồn Chuẩn Hóa (Stable Version)](#4-mã-nguồn-chuẩn-hóa-stable-version)
- [5. Lời kết & Định hướng tiếp theo](#5-lời-kết--định-hướng-tiếp-theo)

---

## 1. Tổng quan Dự án

| Hạng mục | Nội dung |
| --- | --- |
| **Mục tiêu** | Đọc đồng thời luồng RGB và Depth từ camera Orbbec Astra Pro, tích hợp AI **MediaPipe Hand Tracking** để đo khoảng cách tay (mm) theo thời gian thực. |
| **Kiến trúc** | **"No-SDK"** — Không dùng Orbbec SDK nguyên khối. Dùng **OpenCV (V4L2)** để đọc luồng RGB, và thư viện Python `openni` (wrapper gọi `libOpenNI2.so` qua Ctypes) để đọc luồng Depth. |
| **Môi trường** | WSL2 (Ubuntu 24.04) trên host Windows 11. Đã cấu hình `usbipd` để passthrough USB và X11/OpenGL Forwarding để hiển thị GUI ra màn hình Windows. |

> 💡 **Vì sao chọn WSL2 thay vì Windows Native?** Như đã đúc kết ở các dự án trước, môi trường Windows Native gây ra nhiều xung đột DLL và driver khi làm việc với camera chuẩn OpenNI cũ. WSL2 cho phép có một nhân Linux "thuần" chạy song song với Windows, loại bỏ tận gốc các vấn đề về driver USB legacy trong khi vẫn giữ được sự tiện lợi của desktop Windows.

---

## 2. Nhật Ký Debug & Các Lỗi Kinh Điển Đi Kèm

### Giai đoạn 1: Chuẩn bị Môi trường & Xung đột Thư viện nền

- **❌ Lỗi:** Camera thỉnh thoảng crash ngầm (Segmentation Fault) trên Windows, hoặc báo **Zombie Device**.
- **💡 Tư duy khắc phục:** Môi trường Media Foundation (MSMF) của Windows xử lý đa luồng USB rất tệ. Chuyển sang Linux dùng **V4L2** (Video for Linux 2) và `libusb` là giải pháp triệt để.
- **🔑 Keyword:** `numpy<2.0` — Thư viện OpenNI wrapper cũ bị vỡ cấu trúc bộ nhớ nếu chạy với Numpy 2.0 mới nhất, **bắt buộc phải hạ cấp**.

```bash
pip install "numpy<2.0"
```

### Giai đoạn 2: Lạc lối trong Ma trận SDK của Orbbec

- **❌ Lỗi:** Cố gắng tìm bản Orbbec SDK v2 hoặc cài các thư viện cổ đại (JDK 6.0, FreeGLUT) từ repo OpenNI2 gốc.
- **💡 Tư duy khắc phục:** Astra Pro là dòng camera đời cũ (Legacy), có **2 chip vật lý tách rời**: UVC cho RGB và PrimeSense cho Depth. Các SDK v2 đời mới **không còn hỗ trợ** dòng camera này.
- **✅ Giải pháp:** Chỉ tải bộ thư viện lõi **OpenNI_SDK (Linux x64)** chính chủ từ GitHub Orbbec. Chạy file `install.sh` để hệ thống tự động copy Udev rules, cấp quyền truy cập USB cho Ubuntu:

```bash
cd OpenNI_2.3.0.86_.../linux/x64
sudo ./install.sh
```

### Giai đoạn 3: Phân quyền Linux (Quyền truy cập Video)

- **❌ Lỗi:** `Permission denied` khi OpenCV cố gắng gọi `/dev/video0`.
- **💡 Tư duy khắc phục:** Dù đã passthrough USB vào WSL2, user mặc định không có quyền đọc thiết bị video.
- **✅ Giải pháp:** Add user vào nhóm `video` và reload quyền:

```bash
sudo usermod -aG video $USER
newgrp video
```

### Giai đoạn 4: Lỗi MediaPipe "Bay màu" Name Space

- **❌ Lỗi:**
  ```
  AttributeError: module 'mediapipe' has no attribute 'solutions'
  ```
- **💡 Tư duy khắc phục:** Lỗi kinh điển trên Ubuntu 24.04 (Python 3.12) do bản dịch Protobuf ngầm làm gãy cấu trúc khởi tạo (`__init__.py`) của MediaPipe.
- **✅ Giải pháp:** Bypass hoàn toàn lớp bọc ngoài, import thẳng vào ruột thư viện:

  | Trước (Lỗi) | Sau (Đã Fix) |
  | --- | --- |
  | `import mediapipe as mp` | `from mediapipe.python.solutions import hands as mp_hands` |

### Giai đoạn 5: Cú lừa "Byte String" của Python 3

- **❌ Lỗi:**
  ```
  expected str, bytes or os.PathLike object, not int
  ```
- **💡 Tư duy khắc phục:** Trong Python 2, đường dẫn file `.so` thường yêu cầu thêm tiền tố byte (`b'/path/...'`). Nhưng khi chạy trên Python 3.12, chuỗi byte này bị vòng lặp tách ra thành các con số nguyên (`int`), khiến hàm khởi tạo bị crash.
- **✅ Giải pháp:** Xóa chữ `b`, truyền đường dẫn string tuyệt đối bình thường vào hàm khởi tạo:

```python
openni2.initialize('/path/to/x64')
```

> 💡 **Ghi chú kỹ thuật:** Đây là lỗi có tính "di truyền" xuyên suốt các dự án Astra Pro No-SDK dù trên Windows hay Linux — gốc rễ luôn là việc xử lý sai kiểu dữ liệu path khi build đường dẫn tuyệt đối truyền vào `openni2.initialize()`. Cách xử lý chuẩn nhất là luôn dùng `os.path.join(...)` để nối chuỗi thay vì gán cứng tiền tố `b""` [1].

### Giai đoạn 6: Giới hạn Phần cứng & Nghẽn Cổ chai USB

Đây là chướng ngại vật lớn nhất, chia làm 2 lỗi liên tiếp:

**❌ Lỗi 1:**
```
(OniStatus.ONI_STATUS_BAD_PARAMETER, b'Device.getProperty(5) failed', None)
```
- *Nguyên nhân:* Astra Pro không có chip đồng bộ phần cứng. Lệnh `IMAGE_REGISTRATION_DEPTH_TO_COLOR` (Property 5) bị từ chối.
- *Giải pháp:* Xóa/Comment đoạn code kích hoạt Image Registration.

**❌ Lỗi 2:**
```
VIDEOIO(V4L2:/dev/video0): select() timeout
```
(Màn hình tối thui, không hiện UI)

- *Nguyên nhân:* Băng thông USB của WSL2 bị nghẽn do cố kéo cùng lúc RGB (chuẩn YUYV raw siêu nặng), Depth 16-bit và IR 16-bit. Vòng lặp `if not ret: continue` khóa luôn luồng Depth khiến toàn bộ tool bị kẹt.

- *Giải pháp toàn diện:*
  1. Ép OpenCV dùng chuẩn nén **MJPG** để giảm tải băng thông:
     ```python
     cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
     ```
  2. **Tắt hẳn luồng IR** (`ir_stream.stop()`) để nhường băng thông cho RGB + Depth.
  3. **Tách biệt logic hiển thị:** Cho dù RGB bị rớt khung hình (timeout), cửa sổ Depth Map vẫn phải được render bình thường — không dùng `continue` để block toàn bộ vòng lặp.

---

## 3. Các Từ khóa & Lệnh quan trọng cần nhớ

| Mục đích | Lệnh |
| --- | --- |
| **Kiểm tra USB passthrough** | `lsusb` (phải thấy **2 module Orbbec**: 1 cái cho UVC, 1 cái cho OpenNI) |
| **Kiểm tra luồng Video** | `ls -l /dev/video*` hoặc `v4l2-ctl --list-devices` |
| **Xóa "Zombie Device"** | Rút cáp vật lý → tắt Terminal WSL → chạy PowerShell: `usbipd unbind --busid <ID>` rồi `usbipd bind --busid <ID>` lại |

---

## 4. Mã Nguồn Chuẩn Hóa (Stable Version)

> Đây là phiên bản ổn định nhất, đã vá toàn bộ các lỗi băng thông, cấp quyền và luồng dữ liệu.

```python
import cv2
import numpy as np
# Import mediapipe trực tiếp (Bypass lỗi mất attribute 'solutions')
from mediapipe.python.solutions import hands as mp_hands
from mediapipe.python.solutions import drawing_utils as mp_drawing
from openni import openni2
import sys

# --- Cấu hình MediaPipe ---
hands = mp_hands.Hands(
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7,
    max_num_hands=1
)

def main():
    # 1. KHỞI TẠO OPENNI2
    # Dùng String tuyệt đối (KHÔNG dùng tiền tố b'...' cho Python 3)
    openni2_dir = '/home/beniot-phan/APT_AstraProTest/sdk/OpenNI_2.3.0.86_202210111154_4c8f5aa4_beta6_linux/samples/samples/ThirdParty/OpenNI2/linux/x64'

    try:
        openni2.initialize(openni2_dir)
        print("Đã khởi tạo OpenNI2 thành công.")
    except Exception as e:
        print(f"Lỗi khởi tạo OpenNI2: {e}")
        sys.exit(1)

    dev = None
    depth_stream = None
    cap = None

    try:
        # 2. MỞ THIẾT BỊ OPENNI (CHỈ LẤY DEPTH)
        dev = openni2.Device.open_any()
        print("Đã kết nối camera Orbbec qua libusb.")

        # Vô hiệu hóa Image Registration vì Astra Pro không hỗ trợ phần cứng
        # Khởi tạo luồng Depth
        depth_stream = dev.create_depth_stream()
        depth_stream.start()

        # Đã tắt luồng IR để tránh nghẽn băng thông USB trên WSL2

        # 3. MỞ THIẾT BỊ UVC (LẤY RGB QUA V4L2)
        cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

        # Bắt buộc ép nén MJPG để cứu băng thông USB
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        if not cap.isOpened():
            print("Cảnh báo: Không thể mở RGB Camera. Hệ thống sẽ tiếp tục hiển thị luồng Depth...")

        print("Đã khởi tạo xong. Nhấn 'q' trên cửa sổ video để thoát.")

        # 4. VÒNG LẶP XỬ LÝ CHÍNH
        while True:
            ret = False
            color_frame = None

            # Đọc RGB (Không sử dụng if not ret: continue để tránh block luồng Depth)
            if cap and cap.isOpened():
                ret, color_frame = cap.read()

            # Đọc và hiển thị Depth Map lập tức
            depth_frame = depth_stream.read_frame()
            depth_data = np.frombuffer(depth_frame.get_buffer_as_uint16(), dtype=np.uint16)
            depth_image = depth_data.reshape(depth_frame.height, depth_frame.width)

            depth_display = cv2.convertScaleAbs(depth_image, alpha=0.03)
            depth_colormap = cv2.applyColorMap(depth_display, cv2.COLORMAP_JET)
            cv2.imshow('Depth Map', depth_colormap)

            # Xử lý RGB và MediaPipe (Nếu khung hình RGB hợp lệ)
            if ret and color_frame is not None:
                color_rgb = cv2.cvtColor(color_frame, cv2.COLOR_BGR2RGB)
                results = hands.process(color_rgb)

                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        mp_drawing.draw_landmarks(color_frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                        h, w, _ = color_frame.shape
                        cx, cy = int(hand_landmarks.landmark[9].x * w), int(hand_landmarks.landmark[9].y * h)

                        if 0 <= cx < depth_frame.width and 0 <= cy < depth_frame.height:
                            distance_mm = depth_image[cy, cx]
                            cv2.circle(color_frame, (cx, cy), 5, (0, 255, 0), cv2.FILLED)
                            cv2.putText(color_frame, f"Distance: {distance_mm} mm", (cx - 50, cy - 20),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                cv2.imshow('RGB Tracking', color_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except Exception as e:
        print(f"Có lỗi xảy ra trong Main Loop: {e}")

    finally:
        # 5. DỌN DẸP TÀI NGUYÊN (CHỐNG ZOMBIE DEVICE)
        print("Đang tiến hành dọn dẹp tài nguyên thiết bị...")
        if cap: cap.release()
        if depth_stream: depth_stream.stop()
        if dev: dev.close()
        openni2.unload()
        cv2.destroyAllWindows()
        print("Đã giải phóng USB và Camera thành công.")

if __name__ == '__main__':
    main()
```

> 💡 **Ghi chú kỹ thuật:** Khối `finally` ở cuối chương trình chính là "van an toàn" đảm bảo luôn giải phóng tài nguyên (`cap.release()`, `depth_stream.stop()`, `dev.close()`, `openni2.unload()`) dù chương trình thoát bình thường hay bị ngắt đột ngột (`Ctrl+C`), giúp tránh triệt để hiện tượng Zombie Device đã mô tả ở Giai đoạn 1 — đây cùng là nguyên tắc dọn dẹp tài nguyên đã áp dụng nhất quán trong các phiên bản driver No-SDK trước đó [1].

---

## 5. Lời kết & Định hướng tiếp theo

Một lần nữa, chúc mừng bạn với thành quả này. Bước đệm này vững chắc rồi thì khi đem qua **Raspberry Pi 5** (chạy Linux Native) sẽ cực kỳ mượt mà, thậm chí **còn không lo nghẽn cổ chai USB** như trên máy ảo WSL nữa.

### 🔭 Một số gợi ý mở rộng khi lên Pi 5 Native:

- **Không cần usbipd:** Pi 5 chạy Linux gốc nên USB đi thẳng vào kernel, không phải qua lớp ảo hóa mạng như WSL2 → độ trễ và khả năng nghẽn băng thông giảm đáng kể.
- **Tận dụng NPU/GPU tích hợp (nếu có board AI hat):** Đẩy MediaPipe hoặc mô hình nhận diện tay sang chạy trên phần cứng tăng tốc để giải phóng CPU.
- **Ghi log khoảng cách tay theo thời gian:** Có thể mở rộng thêm module xuất dữ liệu `distance_mm` ra file CSV hoặc gửi qua MQTT để tích hợp vào hệ thống điều khiển robot/IoT lớn hơn.
- **Cấu hình lại QoS/luồng dữ liệu** nếu tích hợp thêm ROS2 ở giai đoạn sau, theo đúng tinh thần kiến trúc "No-SDK" đã xây dựng xuyên suốt dự án.

---

## 📄 Giấy phép

Tài liệu và mã nguồn được chia sẻ cho mục đích học tập, nghiên cứu và phát triển ứng dụng thị giác máy tính / robotics cá nhân.
```

**Ghi chú:** Mình có thêm 2 chú thích kỹ thuật (đánh dấu 💡) tại phần "Cú lừa Byte String" và phần "Dọn dẹp tài nguyên" kèm trích dẫn [1], vì đây là những đoạn mã tương đồng trực tiếp với pattern đã xuất hiện trong file `astra_crossplatform.py` (nguồn có id) — cùng là lỗi xử lý path dạng byte và cùng cơ chế cleanup `try...finally`. Các phần còn lại của log (usbipd, MediaPipe namespace, phân quyền video...) không có nguồn tương ứng nên mình giữ nguyên nội dung bạn cung cấp mà không gắn trích dẫn.

This response was generated by Apollo AI, an internal AI assistant. Please validate important outputs against official Apollo documents, systems, and responsible teams before acting on them.
