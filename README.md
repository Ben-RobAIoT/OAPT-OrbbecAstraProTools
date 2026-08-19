Dưới đây là toàn bộ nội dung đã được biên tập thành file `README.md` hoàn chỉnh, chuyên nghiệp, với các liên kết được định dạng markdown sẵn để bạn copy trực tiếp vào GitHub.

# 🎥 Orbbec Astra Pro trên ROS2 Jazzy & Edge Computing

> **Báo cáo Kỹ thuật Chuyên sâu:** Triển khai, Tối ưu hóa và Xây dựng Nền tảng Độc lập (No-SDK) cho Camera 3D Orbbec Astra Pro trên Hệ sinh thái ROS2 Jazzy, WSL2 và Edge Computing (Raspberry Pi 4/5).

[![ROS2](https://img.shields.io/badge/ROS2-Jazzy-blue)](https://docs.ros.org/en/jazzy/)
[![Ubuntu](https://img.shields.io/badge/Ubuntu-24.04-orange)](https://releases.ubuntu.com/24.04/)
[![Platform](https://img.shields.io/badge/Platform-WSL2%20%7C%20Raspberry%20Pi-lightgrey)]()
[![License](https://img.shields.io/badge/License-MIT-green)]()

---

## 📑 Mục lục

1. [Tổng quan Kiến trúc Phần cứng và Cơ chế Hoạt động của Orbbec Astra Pro](#1-tổng-quan-kiến-trúc-phần-cứng-và-cơ-chế-hoạt-động-của-orbbec-astra-pro)
2. [Đánh giá Hiện trạng các Nền tảng Mã nguồn mở trên Github](#2-đánh-giá-hiện-trạng-các-nền-tảng-mã-nguồn-mở-trên-github)
3. [Chiến lược Triển khai 1: Bypassing Windows qua WSL2](#3-chiến-lược-triển-khai-1-bypassing-windows-qua-wsl2-ubuntu-2404--ros2-jazzy)
4. [Chiến lược Triển khai 2: Edge Computing trên Raspberry Pi 4/5](#4-chiến-lược-triển-khai-2-nền-tảng-tính-toán-biên-edge-computing-trên-raspberry-pi-45)
5. [Kiến trúc "No-SDK": Truy xuất Phần cứng Trực tiếp](#5-kiến-trúc-no-sdk-trực-tiếp-truy-xuất-phần-cứng-và-phát-triển-ứng-dụng-độc-lập)
6. [Xây dựng Trình Điều Khiển Tùy Biến trên ROS2 Jazzy](#6-xây-dựng-trình-điều-khiển-tùy-biến-custom-driver-trên-ros2-jazzy)
7. [Trực quan Hóa Không Gian 3D và Ứng dụng Bậc Cao](#7-trực-quan-hóa-không-gian-3d-và-ứng-dụng-bậc-cao)
8. [Khuyến nghị và Tổng kết Kiến trúc](#8-khuyến-nghị-và-tổng-kết-kiến-trúc)
9. [Nguồn Tham khảo](#9-nguồn-tham-khảo)

---

## 1. Tổng quan Kiến trúc Phần cứng và Cơ chế Hoạt động của Orbbec Astra Pro

Việc làm chủ một thiết bị phần cứng không phụ thuộc vào các bộ công cụ phát triển phần mềm (SDK) nguyên bản đòi hỏi một sự thấu hiểu sâu sắc về kiến trúc vật lý và nguyên lý quang học của thiết bị đó. Orbbec Astra Pro là một trong những dòng camera RGB-D (Red, Green, Blue - Depth) phổ biến, được thiết kế dựa trên công nghệ ánh sáng cấu trúc (Structured Light) thay vì công nghệ Time-of-Flight (ToF) hay Stereo Vision truyền thống. Sự phân định rõ ràng về luồng dữ liệu ở cấp độ phần cứng là cơ sở cốt lõi để loại bỏ các SDK cồng kềnh như Astra-SDK hay Orbbec-SDK, từ đó xây dựng các ứng dụng độc lập, nhẹ và tối ưu cho các hệ thống nhúng.

### 1.1. Công nghệ Ánh sáng Cấu trúc (Structured Light) và Trích xuất Chiều sâu

Công nghệ Structured Light trên Astra Pro hoạt động dựa trên ba thành phần cốt lõi: một máy chiếu tia hồng ngoại (IR Projector), một cảm biến hồng ngoại (IR Camera) và một bộ xử lý tính toán hình ảnh nội bộ (ASIC). Máy chiếu hồng ngoại phát ra một mảng các điểm sáng (speckle pattern) vô hình với mắt người, bao gồm hàng chục nghìn điểm được mã hóa theo cấu trúc giả ngẫu nhiên vào không gian. Khi các tia sáng này va chạm với bề mặt vật thể, mạng lưới điểm sáng sẽ bị biến dạng (warping) dựa trên hình học không gian của vật thể đó.

Cảm biến hồng ngoại thu nhận hình ảnh của mảng điểm sáng biến dạng này. Thông qua độ lệch chuẩn (disparity) giữa mẫu gốc được lưu trong bộ nhớ phần cứng và mẫu thu được, chip ASIC trên camera áp dụng các thuật toán đối sánh khối (Block Matching) hoặc Semi-Global Matching (SGM) để tính toán ra khoảng cách (Depth) cho từng điểm ảnh. Hệ quả kỹ thuật của cơ chế này là luồng dữ liệu Depth và IR thực chất có chung một nguồn gốc phần cứng vật lý. Dữ liệu hồng ngoại (IR) chính là phổ cường độ ánh sáng thô, trong khi dữ liệu chiều sâu (Depth) là kết quả toán học sau khi ASIC xử lý phổ cường độ đó. Do giới hạn về băng thông của giao thức USB 2.0 trên Astra Pro, việc truy xuất đồng thời cả ba luồng (Depth, IR, RGB) ở tần số quét cao nhất (30 FPS) thường dẫn đến hiện tượng nghẽn cổ chai dữ liệu.

Về mặt đo lường học (Metrological qualification), cấu trúc ánh sáng của Astra Pro cung cấp độ chính xác đo lường rất cao ở cự ly gần và trung bình (từ 0.6m đến 6.0m), đặc biệt phù hợp cho các bài toán định vị không gian hẹp hoặc theo dõi chuyển động con người (pose estimation). Các nghiên cứu so sánh chỉ ra rằng trong khi Time-of-Flight (như Kinect v2) có lợi thế về độ phân giải thời gian, công nghệ Structured Light của Astra Pro lại vượt trội về độ chính xác tuyệt đối (accuracy) với sai số tịnh tiến dưới 2.5 mm trong điều kiện tối ưu. Tuy nhiên, công nghệ này gặp hạn chế khi hoạt động dưới ánh sáng mặt trời mạnh hoặc trên các bề mặt phản xạ/hấp thụ tia hồng ngoại.

### 1.2. Sự Tách biệt giữa Kênh RGB (UVC) và Kênh Depth/IR (OpenNI)

Một khía cạnh thiết kế quan trọng làm nên tính đa dụng của Astra Pro là sự tách biệt hoàn toàn về mặt giao thức giữa kênh màu (RGB) và kênh chiều sâu. Trong khi luồng Depth và IR yêu cầu giao thức truyền thông qua thư viện `libusb` để tương tác với phần cứng xử lý OpenNI độc quyền, kênh màu (RGB) lại được triển khai hoàn toàn tuân theo tiêu chuẩn UVC (USB Video Class).

Sự phân tách này giải thích tại sao người dùng cảm thấy việc sử dụng Astra-SDK hay Orbbec-SDK trở nên nặng nề và khó sử dụng. Các bộ SDK này cố gắng đóng gói cả hai giao thức (UVC và OpenNI) vào một middleware duy nhất, dẫn đến các vòng lặp xử lý đồng bộ hóa (synchronization overhead) phức tạp. Trên thực tế, luồng RGB có thể được truy xuất trực tiếp thông qua V4L2 (Video4Linux2) trên Ubuntu hoặc Media Foundation trên Windows như một chiếc webcam thông thường mà không cần tải bất kỳ trình điều khiển bổ sung nào. Hiểu được sự độc lập của hai luồng dữ liệu này mở ra cánh cửa cho việc phát triển kiến trúc **"No-SDK"**, nơi ứng dụng chỉ trích xuất chính xác những gì hệ thống cần với độ trễ xấp xỉ bằng không.

---

## 2. Đánh giá Hiện trạng các Nền tảng Mã nguồn mở trên Github

Để không phải bắt đầu lại từ đầu, việc khảo sát các dự án đã triển khai Astra Pro trên thế giới là bước đi chiến lược. Hệ sinh thái ROS2 Jazzy (phiên bản phát hành cùng Ubuntu 24.04) đã mang lại nhiều thay đổi lớn về tiêu chuẩn C++ và API lõi, tạo ra sự phân hóa rõ rệt trong cộng đồng mã nguồn mở.

### 2.1. Phân tích Các Kho lưu trữ (Repository) Cốt lõi

Các kỹ sư trên thế giới hiện đang phân mảnh việc hỗ trợ Orbbec Astra Pro thành nhiều luồng dự án khác nhau. Việc lựa chọn một nền tảng cơ sở (base platform) đòi hỏi sự cân nhắc kỹ lưỡng về tính tương thích lâu dài.

| **Tên Dự án / Kho lưu trữ** | **Trạng thái Hỗ trợ ROS2 Jazzy** | **Ưu điểm Kiến trúc** | **Điểm Nghẽn Kỹ thuật** |
| --- | --- | --- | --- |
| [`orbbec/OrbbecSDK_ROS2`](https://github.com/orbbec/OrbbecSDK_ROS2) | Tốt (chỉ trên nhánh `v2-main`) | Chính chủ, cập nhật liên tục, hỗ trợ đa cấu hình thiết bị hiện đại | Bỏ rơi các dòng Astra cũ chuẩn OpenNI. Người dùng Astra Pro bị buộc dùng nhánh `main` cũ. Lỗi ma trận `NaN` |
| [`orbbec/ros2_astra_camera`](https://github.com/orbbec/ros2_astra_camera) | Lỗi biên dịch nguyên bản | Tối ưu chuyên biệt cho kiến trúc Astra Pro truyền thống, nhẹ và không chứa bloatware của v2 | Lỗi tương thích API C++ trên Jazzy (đặc biệt thư viện `cv_bridge` và `image_geometry`) |
| `iru-han/ros2_astra_camera` (nhánh rẽ cộng đồng) | Đã được cộng đồng vá lỗi | Khắc phục được các lỗi thư viện, cấu trúc lại quy trình quản lý thông số (parameters) | Yêu cầu phải biên dịch thủ công thư viện `libuvc` từ mã nguồn |
| [`icclab/icclab_summit_xl`](https://github.com/icclab/icclab_summit_xl) | Native Jazzy | Trình diễn tích hợp hệ thống lớn: SLAM, Nav2, AI Segmentation (SAM) điều khiển tay máy | Là một dự án robot hoàn chỉnh, cần bóc tách các file launch liên quan đến camera để tái sử dụng |
| [`CollaborativeRoboticsLab/astra_legacy_ros`](https://github.com/CollaborativeRoboticsLab/astra_legacy_ros) | Tương thích qua Docker Compose | Thiết lập file cấu hình YAML cực kỳ chi tiết cho độ phân giải và tần số quét | Thiết kế chủ yếu xoay quanh môi trường ROS2 Humble, cần điều chỉnh biến môi trường cho Jazzy |

### 2.2. Điểm yếu của Trình điều khiển Chính thức trên Hệ thống Cũ

Dự án chính thức `OrbbecSDK_ROS2` vừa trải qua một đợt tái cấu trúc lớn với nhánh `v2-main` nhằm hỗ trợ bộ thư viện thế hệ thứ 2. Tuy nhiên, tài liệu kỹ thuật của hãng ghi rõ Astra Pro và các thiết bị chuẩn OpenNI cũ chỉ nhận được "limited maintenance" (bảo trì hạn chế) và không được hỗ trợ trên nhánh v2 mới. Khi người dùng cố gắng khởi chạy Astra Pro thông qua driver chính thức, một lỗi logic nội bộ liên tục xuất hiện: ma trận nội sinh của camera (K matrix và P matrix) chứa các giá trị Not-a-Number (NaN).

Theo tiêu chuẩn `sensor_msgs/msg/CameraInfo` của ROS, ma trận K (Intrinsic matrix) mô tả tiêu cự và tâm quang học của ảnh thô, trong khi ma trận P (Projection matrix) mô tả hình học ảnh sau khi đã được nắn chỉnh (rectified). Do trình điều khiển Orbbec không xử lý chính xác cấu trúc dữ liệu hiệu chuẩn (calibration data) từ EEPROM của camera Astra Pro thông qua chuẩn USB 2.0, các bản tin `camera_info` bị phá vỡ. Hậu quả là chuỗi xử lý hình ảnh phía sau (`depth_image_proc`) không có thông số toán học để thực hiện phép chiếu ngược (back-projection) từ tọa độ pixel 2D sang không gian 3D, khiến các phần mềm như RViz2 không thể hiển thị đám mây điểm.

### 2.3. Vấn đề Nâng cấp Kiến trúc C++ trên ROS2 Jazzy

Nếu lựa chọn dự án `ros2_astra_camera` làm nền tảng cốt lõi (vì nó tối ưu chuyên sâu cho Astra), hệ thống sẽ đối mặt với các rào cản tương thích của Ubuntu 24.04. Cụ thể, hệ sinh thái ROS2 Jazzy đã tái cấu trúc các thư viện liên quan đến thị giác máy tính. Các header cốt lõi như `cv_bridge.h` và `pinhole_camera_model.h` đã được đổi đuôi mở rộng thành `.hpp` (`cv_bridge.hpp`, `pinhole_camera_model.hpp`).

Hơn thế nữa, cơ chế quản lý tham số động (Dynamic Parameters) trong `rclcpp` bị thay đổi. Cấu trúc `rclcpp::node_interfaces::NodeParametersInterface::OnParametersSetCallbackType` không còn tồn tại trong Jazzy, dẫn đến tiến trình biên dịch (compile) bị gián đoạn và báo lỗi "has not been declared". Việc vá lỗi (patching) các module mã nguồn này là yêu cầu bắt buộc trước khi phát triển các tính năng tùy biến.

---

## 3. Chiến lược Triển khai 1: Bypassing Windows qua WSL2 (Ubuntu 24.04 + ROS2 Jazzy)

Môi trường phát triển trên hệ điều hành Windows thường mang lại những trở ngại sâu sắc liên quan đến xung đột thư viện liên kết động (DLL Hell). Cụ thể, người dùng báo cáo lỗi xung đột với bộ phân phối `VC_redist` (Visual C++ Redistributable). Các bộ SDK của Astra Pro (đặc biệt là OpenNI2) thường được biên dịch bằng các công cụ MSVC cũ. Khi chạy chung với các ứng dụng hiện đại hoặc hệ thống quản lý gói trên Windows 11, không gian bộ nhớ của các DLL này xảy ra xung đột, làm ứng dụng bị treo (crash) hoặc không nhận diện được thiết bị. Giải pháp cô lập phần cứng thông qua Windows Subsystem for Linux 2 (WSL2) là một chiến lược kiến trúc xuất sắc để vượt qua giới hạn này.

### 3.1. Cơ chế Ánh xạ Phần cứng qua Giao thức USB/IP

Khác với các hệ điều hành ảo hóa nguyên khối (như VMware hay VirtualBox), WSL2 mặc định không có quyền truy cập trực tiếp vào bus USB vật lý của máy chủ Windows. Khi một camera được cắm vào, Windows Kernel tiến hành quá trình liệt kê (enumeration), yêu cầu khối mô tả thiết bị (Device Descriptor) để lấy mã Nhà cung cấp (Vendor ID) và mã Sản phẩm (Product ID), sau đó nạp driver Windows tương ứng. Để chuyển hướng thiết bị này vào WSL2, hệ thống cần một phần mềm trung gian chặn luồng dữ liệu USB Request Blocks (URBs).

Dự án mã nguồn mở [`usbipd-win`](https://github.com/dorssel/usbipd-win) đảm nhận vai trò này. Phần mềm này bóc tách các gói dữ liệu USB ở tầng thấp, đóng gói chúng thành các khung tin TCP/IP, và định tuyến qua công tắc mạng ảo (Hyper-V Virtual Switch) để đưa thẳng vào Kernel của môi trường Ubuntu 24.04 chạy bên trong WSL2.

### 3.2. Quy trình Thực thi Cầu nối USB/IP

**Trên máy chủ Windows 11 (Mở PowerShell với quyền Administrator):**

**1. Cài đặt công cụ chia sẻ USB qua trình quản lý gói của Windows:**

```powershell
winget install --interactive --exact dorssel.usbipd-win
```

**2. Liệt kê toàn bộ các thiết bị USB đang kết nối** để tìm mã `BUSID` của Orbbec Astra Pro (thông thường hiển thị dưới dạng APX hoặc Orbbec Device):

```powershell
usbipd list
```

**3. Khóa (bind) thiết bị** vào dịch vụ chia sẻ mạng ảo, ví dụ `BUSID` là `1-1` hoặc `1-2`:

```powershell
usbipd bind --busid 1-1
```

**4. Đẩy (attach) phần cứng vào WSL.** Sử dụng tham số `--auto-attach` là một kỹ thuật quan trọng để đảm bảo rằng nếu cáp camera bị lỏng hoặc reset, WSL2 vẫn tự động nhận lại thiết bị mà không cần gõ lại lệnh:

```powershell
usbipd attach --wsl --busid 1-1 --auto-attach
```

> ⚠️ **Lưu ý xử lý sự cố:** Nếu hệ thống báo lỗi `Device busy (exported)` hoặc cảnh báo thiết bị đang bị Windows chiếm dụng, cần tắt toàn bộ các ứng dụng chụp ảnh trên Windows (Skype, Windows Camera) và sử dụng tham số cưỡng bức `--force` nếu cần thiết.

### 3.3. Cấu hình Không gian Người dùng (Userspace) trên WSL2 Ubuntu 24.04

Mặc dù luồng dữ liệu USB đã đi vào Kernel của WSL2, hệ điều hành Ubuntu vẫn cần các công cụ không gian người dùng để diễn giải giao thức mạng ảo này. Nếu Kernel WSL không hỗ trợ, thiết bị sẽ không hiển thị.

**Trên Terminal của Ubuntu 24.04 (WSL2):**

Cập nhật danh sách gói và cài đặt các công cụ quản lý nhân Linux:

```bash
sudo apt update
sudo apt install linux-tools-generic hwdata
sudo update-alternatives --install /usr/local/bin/usbip usbip /usr/lib/linux-tools/*-generic/usbip 20
```

Kiểm tra xem camera Astra Pro đã tồn tại trong không gian Linux hay chưa bằng lệnh `lsusb`.

### 3.4. Quản trị Phân quyền (Udev Rules)

Một nguyên nhân phổ biến khiến ROS2 khởi tạo camera thất bại trên Linux là lỗi phân quyền (Permission Denied). Udev (userspace /dev) là hệ thống quản lý thiết bị tự động. Nếu không có quy tắc (rules) cụ thể, Linux mặc định chỉ cho phép tài khoản root (`sudo`) đọc luồng dữ liệu USB, điều này vi phạm nguyên tắc bảo mật khi chạy các node ROS2.

Phải thiết lập file cấu hình udev để cấp quyền đọc/ghi (`0666`) cho tất cả các thiết bị mang Vendor ID của Orbbec (`2bc5`):

```bash
sudo nano /etc/udev/rules.d/99-obsensor-libusb.rules
```

Chèn nội dung cấu hình cấp quyền thuộc tính (Attributes):

```
SUBSYSTEM=="usb", ATTR{idVendor}=="2bc5", MODE:="0666", OWNER:="root", GROUP:="video", SYMLINK+="orbbec_camera%n"
```

Nạp lại cấu hình vào nhân hệ điều hành:

```bash
sudo udevadm control --reload-rules && sudo udevadm trigger
```

Sau bước này, kiến trúc WSL2 đã trở thành một nền tảng Linux "thuần khiết", hoàn toàn cách ly khỏi các xung đột phần mềm của Windows, sẵn sàng để biên dịch và vận hành ROS2 Jazzy.

---

## 4. Chiến lược Triển khai 2: Nền tảng Tính toán Biên (Edge Computing trên Raspberry Pi 4/5)

Việc dịch chuyển toàn bộ hệ thống lên các thiết bị Edge Computing như Raspberry Pi 4 hoặc 5 (phiên bản RAM 8GB) kết hợp Ubuntu 24.04 và ROS2 Jazzy là xu hướng tối ưu cho robot di động tự hành. Khác biệt với kiến trúc x86_64 trên PC, hệ sinh thái ARM64 đối mặt với ba bài toán khốc liệt: quá tải bộ nhớ khi biên dịch mã nguồn (Out of Memory - OOM), thiếu vắng thư viện xử lý video lớp thấp (Low-level video libraries), và hiện tượng nghẽn mạng do luồng dữ liệu 3D khổng lồ.

### 4.1. Tối ưu hóa Chu trình Biên dịch (Colcon Build Optimization)

Các gói phần mềm ROS2 quản lý luồng dữ liệu camera chiều sâu thường phụ thuộc nặng nề vào kiến trúc khuôn mẫu (templates) của ngôn ngữ C++, cùng với các ma trận toán học khổng lồ từ thư viện Eigen3 và OpenCV. Khi tiến hành lệnh `colcon build` trên Raspberry Pi, hệ thống sẽ cố gắng phân luồng để sử dụng tối đa 4 nhân CPU. Tuy nhiên, mỗi luồng biên dịch có thể ngốn tới 2-3 GB RAM. Dù Pi có 8GB RAM, hệ thống vẫn dễ dàng đóng băng hoặc tự động ngắt tiến trình (OOM Killer) sau hàng giờ chạy.

Để giải quyết vấn đề này, các chuyên gia phải can thiệp vào cách thức `colcon` phân bổ tài nguyên:

- **Thứ nhất:** tạo không gian hoán đổi (Swap Space) tối thiểu 4GB trên ổ cứng thẻ nhớ hoặc SSD NVMe để làm vùng đệm chống tràn RAM.
- **Thứ hai:** ép buộc `colcon` chỉ xử lý các gói tuần tự (sequential) và giới hạn số luồng (jobs) song song của `cmake`:

```bash
# Thiết lập cờ môi trường giới hạn luồng của Make
export MAKEFLAGS="-j2"
# Khởi chạy biên dịch tuần tự, tắt giao diện dòng lệnh nặng nề
colcon build --event-handlers console_direct+ --cmake-args -DCMAKE_BUILD_TYPE=Release --executor sequential
```

### 4.2. Khắc phục Sự cố Thư viện Lõi (libuvc Integration)

Dòng camera Astra Pro dựa vào thư viện `libuvc` (USB Video Class Library) để giao tiếp không đồng bộ (asynchronous) với phần cứng RGB. Tuy nhiên, các bản phân phối `libuvc-dev` có sẵn trên kho lưu trữ `apt` của Ubuntu ARM64 thường lỗi thời hoặc thiếu các phần mở rộng định dạng khối (format blocks) cần thiết của Orbbec. Hậu quả là driver liên tục báo lỗi không thể truy vấn thông tin thiết bị.

Giải pháp bắt buộc là người dùng phải nạp mã nguồn mở của [`libuvc`](https://github.com/libuvc/libuvc) từ Github và tự biên dịch để tương thích chính xác với hạt nhân (Kernel) của Raspberry Pi:

```bash
cd ~
git clone https://github.com/libuvc/libuvc.git
cd libuvc
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j4
sudo make install
sudo ldconfig # Cập nhật bộ nhớ cache liên kết thư viện chia sẻ (shared libraries)
```

Sau khi liên kết lại bộ thư viện hệ thống, driver ROS2 của Orbbec mới có khả năng bám (hook) vào phần cứng UVC.

### 4.3. Quản trị Băng thông và Mạng DDS (Data Distribution Service)

Kiến trúc ROS2 dựa trên lớp trung gian DDS (thường là FastDDS hoặc CycloneDDS) để phân phối bản tin. Các mảng dữ liệu 3D (`PointCloud2`) chứa hàng triệu điểm tọa độ (x, y, z, màu sắc) phát sinh ở mức 30 khung hình/giây sẽ dễ dàng tiêu thụ hàng trăm megabit băng thông. Nếu cấu hình QoS (Quality of Service) mặc định được giữ ở trạng thái `Reliable` (đảm bảo truyền tin tin cậy), bất kỳ gói tin bị rớt nào (packet loss) qua mạng Wi-Fi của Raspberry Pi cũng sẽ bắt buộc hệ thống truyền lại. Quá trình này tạo ra hiệu ứng hòn tuyết lăn, làm sập toàn bộ bộ định tuyến mạng và tăng độ trễ lên mức hàng giây.

Hệ thống phải được cấu hình QoS Profile về trạng thái `SENSOR_DATA` (Best Effort). Ở cấu hình này, nếu mạng quá tải, gói tin cũ sẽ bị vứt bỏ (drop) để nhường chỗ cho khung hình mới nhất, đảm bảo tính thời gian thực (real-time) của tín hiệu đầu vào cho các thuật toán dẫn đường.

---

## 5. Kiến trúc "No-SDK": Trực tiếp Truy xuất Phần cứng và Phát triển Ứng dụng Độc lập

Đáp ứng yêu cầu trực tiếp từ người dùng về việc không muốn bị ràng buộc bởi các bộ công cụ phát triển (SDK) phức tạp và khó cấu hình của nhà sản xuất, việc xây dựng một kiến trúc "No-SDK" là giải pháp tối ưu cho việc kiểm thử và triển khai các ứng dụng nhẹ. Bản chất kiến trúc này khai thác tối đa sự phân tách giao thức vật lý giữa RGB và Depth/IR của Astra Pro, sử dụng các thư viện tính toán chuẩn của thế giới mà không cần bất kỳ middleware riêng biệt nào.

### 5.1. Khai thác Kênh Màu (RGB) bằng OpenCV thuần túy

Như đã trình bày, kênh màu của Astra Pro hoàn toàn tuân thủ chuẩn UVC. Điều này có nghĩa là hạt nhân Linux (hoặc môi trường WSL2) tự động cài đặt driver `uvcvideo` và gán thiết bị vào hệ thống tệp tin dạng thiết bị ký tự (ví dụ: `/dev/video0` hoặc `/dev/video1`).

Thay vì gọi hàng chục API phức tạp của Orbbec-SDK, hệ thống chỉ cần dùng thư viện Computer Vision mã nguồn mở phổ biến nhất - OpenCV.

Đoạn mã Python tham chiếu sau đây mô phỏng việc trích xuất luồng ảnh đa đích, bỏ qua hoàn toàn chi phí (overhead) của SDK:

```python
import cv2

# Khởi tạo VideoCapture liên kết trực tiếp với Device Node của Linux
# Người dùng có thể chạy 'v4l2-ctl --list-devices' để xác định chỉ mục chính xác
camera_index = 0
cap = cv2.VideoCapture(camera_index, cv2.CAP_V4L2)

# Thiết lập cưỡng bức độ phân giải tiêu chuẩn của Astra Pro
# Giảm tải tính toán nếu ứng dụng AI không cần độ phân giải HD
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Lỗi truy xuất luồng UVC")
        break

    # Tại đây có thể nạp thẳng ma trận 'frame' vào mạng YOLO hoặc SAM
    # mà không cần phải chuyển đổi kiểu dữ liệu ROS Image Message.
    cv2.imshow("Astra Pro RGB Native Stream", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

Kiến trúc này cho phép các ứng dụng trên Edge Computing như Raspberry Pi 5 đẩy luồng ảnh trực tiếp vào vi xử lý NPU (Neural Processing Unit) hoặc bộ tăng tốc Edge TPU, giảm thiểu độ trễ từ lúc camera chụp đến lúc AI đưa ra kết quả phát hiện vật thể.

### 5.2. Khai thác Chiều Sâu (Depth) và Hồng Ngoại (IR) với Cốt lõi OpenNI2

Việc truy xuất dữ liệu từ cảm biến chiều sâu dựa vào ánh sáng cấu trúc yêu cầu giao tiếp thông qua giao diện `libusb`. Tuy nhiên, thay vì cài đặt toàn bộ Astra-SDK, nền tảng phát triển chỉ cần lớp trừu tượng hóa phần cứng (Hardware Abstraction Layer) mã nguồn mở là `OpenNI2`. Hiện nay, hệ sinh thái Python cung cấp các gói liên kết (bindings) cực kỳ nhẹ cho thư viện này.

**Khởi tạo Môi trường:**

```bash
pip install openni opencv-python numpy
```

**Mã nguồn Python Trực xuất Dữ liệu Độ Sâu Toán học:**

Dữ liệu trả về từ cảm biến IR sau khi qua chip ASIC không phải là một bức ảnh thông thường, mà là một ma trận hai chiều (2D Array) chứa các số nguyên 16-bit. Mỗi giá trị số nguyên này đại diện cho khoảng cách vật lý (đo bằng milimet) từ mặt phẳng thấu kính đến bề mặt vật thể.

```python
from openni import openni2, c_api
import numpy as np
import cv2

# Nạp thư viện lõi OpenNI2 (Yêu cầu đường dẫn chứa file libOpenNI2.so hoặc .dll)
openni2.initialize("/usr/lib/")

# Kết nối trực tiếp vào Astra Pro thông qua giao diện USB
dev = openni2.Device.open_any()

# Yêu cầu phần cứng cấp luồng dữ liệu chiều sâu
depth_stream = dev.create_depth_stream()
depth_stream.start()
# Thiết lập định dạng điểm ảnh 16-bit (mm)
depth_stream.set_video_mode(
    c_api.OniVideoMode(
        pixelFormat=c_api.OniPixelFormat.ONI_PIXEL_FORMAT_DEPTH_1_MM,
        resolutionX=640,
        resolutionY=480,
        fps=30
    )
)

while True:
    frame = depth_stream.read_frame()
    frame_data = frame.get_buffer_as_uint16()

    # Định hình lại mảng dữ liệu 1D thành ma trận Numpy 2D
    depth_matrix = np.ndarray((frame.height, frame.width), dtype=np.uint16, buffer=frame_data)

    # Xử lý hình ảnh trực quan (Visual normalization)
    # Rút gọn dải động (dynamic range) từ 16-bit xuống 8-bit để màn hình có thể hiển thị
    img_8bit = cv2.normalize(depth_matrix, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)

    # Áp dụng bản đồ màu giả (Pseudo-color map) để làm nổi bật sự thay đổi khoảng cách
    img_color = cv2.applyColorMap(img_8bit, cv2.COLORMAP_JET)

    cv2.imshow("Astra Pro Depth Matrix", img_color)
    if cv2.waitKey(1) & 0xFF == ord('c'):
        break

depth_stream.stop()
openni2.unload()
cv2.destroyAllWindows()
```

Việc sở hữu ma trận Numpy 16-bit nguyên bản mở ra vô vàn tiềm năng. Người lập trình có thể triển khai các thuật toán loại bỏ nhiễu biên (Edge-preserving filters), bộ lọc không gian (Spatial filter), hoặc tính toán thể tích vật thể mà không bị khóa chặt vào các hàm tiền xử lý (preprocessing) không rõ mã nguồn của Orbbec.

Nếu dự án yêu cầu tầm nhìn xuyên thấu trong bóng tối, lập trình viên chỉ cần thay đổi API `create_depth_stream()` thành `create_ir_stream()`. Khi đó, phần cứng sẽ bỏ qua quá trình đối sánh khối toán học và truyền thẳng phổ cường độ ánh sáng của tia hồng ngoại. Đây là tính năng sống còn cho các robot hoạt động trong hầm lò hoặc các hệ thống nhận diện mốc phản quang (reflective markers).

---

## 6. Xây dựng Trình Điều Khiển Tùy Biến (Custom Driver) trên ROS2 Jazzy

Dựa trên quá trình phân tích kho lưu trữ ở Phần 2, giải pháp thiết thực nhất để tạo ra một Base Platform tái sử dụng trên Ubuntu 24.04 (Jazzy) là kế thừa kho lưu trữ `ros2_astra_camera` và thực hiện vá lỗi sâu ở tầng ngôn ngữ C++. Điều này cho phép tận dụng khả năng giao tiếp của ROS2, cấu hình linh hoạt thông qua `.yaml`, nhưng vẫn loại bỏ được các lỗi rác của thư viện chính hãng.

### 6.1. Quy trình Cập nhật và Vá lỗi API C++

Do ROS2 Jazzy nâng cấp bộ chuẩn C++, thư viện `image_geometry` và `cv_bridge` đã thay đổi phương thức gọi header.

Người dùng tạo một workspace và tải mã nguồn:

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
# Sử dụng kho lưu trữ gốc (cần tự vá) hoặc kho lưu trữ đã được cộng đồng cập nhật sơ bộ
git clone https://github.com/iru-han/ros2_astra_camera.git
```

Quá trình rà soát mã nguồn yêu cầu:

1. **Vá Thư viện Tầm nhìn:** Tìm kiếm toàn bộ các tệp `.cpp` và `.h`, đổi `#include <cv_bridge/cv_bridge.h>` thành `#include <cv_bridge/cv_bridge.hpp>`. Đổi `#include <image_geometry/pinhole_camera_model.h>` thành `#include <image_geometry/pinhole_camera_model.hpp>`.

2. **Vá Trình xử lý Tham số Động (Dynamic Parameters):** API `rclcpp::node_interfaces::NodeParametersInterface::OnParametersSetCallbackType` không còn tồn tại trên bản cập nhật này. Lập trình viên phải định nghĩa lại con trỏ hàm callback thông qua phương thức `add_on_set_parameters_callback` theo chuẩn mới của `rclcpp::Node`.

3. **Biên dịch gói phần mềm:**

```bash
cd ~/ros2_ws
colcon build --event-handlers console_direct+ --cmake-args -DCMAKE_BUILD_TYPE=Release
source install/setup.bash
```

### 6.2. Thiết lập Cấu hình Khởi chạy (Launch Configuration)

Hành vi của camera được định đoạt bởi các tệp khởi chạy (launch files), cụ thể là tệp `astra_pro.launch.py`. Các tham số này xác định phần cứng nào được kích hoạt, tốc độ luồng dữ liệu, và cách thức căn chỉnh không gian.

| **Tham số Cấu hình (Parameter)** | **Ý nghĩa Kỹ thuật** | **Cấu hình Đề xuất cho Astra Pro** |
| --- | --- | --- |
| `color_width` / `color_height` | Độ phân giải của cảm biến ảnh RGB | `640` / `480` (Tránh dùng 1080p để giảm tải băng thông USB 2.0) |
| `depth_width` / `depth_height` | Độ phân giải của lưới chiều sâu | `640` / `480` (Đồng nhất với RGB để dễ nắn chỉnh hình học) |
| `enable_point_cloud` | Kích hoạt luồng PointCloud 3D thô | `true` (Yêu cầu phải có `depth_image_proc` ở phía sau) |
| `depth_registration` | Ép phần cứng uốn cong (warp) ảnh Depth khớp với góc nhìn (FoV) của ảnh RGB | `true` (Cực kỳ quan trọng để tạo ra đám mây điểm có màu - Colored Point Cloud) |
| `enable_ir` | Kích hoạt luồng tia hồng ngoại | `false` (Không nên bật đồng thời với Depth do chia sẻ chung băng thông luồng cảm biến vật lý) |
| `point_cloud_qos` | Thiết lập chính sách truyền mạng DDS | `SENSOR_DATA` (Hạn chế rớt mạng vòng lặp kín trên Raspberry Pi) |

Khởi chạy hệ thống bằng lệnh:

```bash
ros2 launch astra_camera astra_pro.launch.py depth_registration:=true enable_point_cloud:=true
```

### 6.3. Khắc phục Lỗi Toán Học Ma trận (NaN Intrinsic Fix)

Sau khi khắc phục lỗi biên dịch, một trở ngại vô hình thường xuyên hạ gục các nhà phát triển là dữ liệu nội sinh (intrinsic calibration). Trên cổng USB 2.0, driver thường thất bại khi đọc firmware EEPROM, trả về các ma trận K (Intrinsic) và P (Projection) chứa toán tử `NaN` (Not a Number) vào topic `/camera/color/camera_info`.

Không có tọa độ tâm quang học (cx, cy) và tiêu cự (fx, fy), các thuật toán nắn chỉnh và chiếu ngược sẽ tạo ra các vector dị thường, khiến tiến trình `depth_image_proc` hoặc PointCloud Library (PCL) kết thúc đột ngột (crash) hoặc sản sinh đám mây điểm trống rỗng.

Để giải quyết tận gốc vấn đề này và làm cho Base Platform hoạt động hoàn hảo:

Người dùng cần tạo một tệp YAML chứa ma trận tĩnh, mô phỏng các thông số chuẩn của dòng Astra Pro.

Ví dụ tệp `color_astra_pro.yaml`:

```yaml
image_width: 640
image_height: 480
camera_name: rgb_camera
camera_matrix:
  rows: 3
  cols: 3
  data: [570.34, 0.0, 314.5, 0.0, 570.34, 235.5, 0.0, 0.0, 1.0]
distortion_model: plumb_bob
distortion_coefficients:
  rows: 1
  cols: 5
  data: [0.0, 0.0, 0.0, 0.0, 0.0]
rectification_matrix:
  rows: 3
  cols: 3
  data: [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
projection_matrix:
  rows: 3
  cols: 4
  data: [570.34, 0.0, 314.5, 0.0, 0.0, 570.34, 235.5, 0.0, 0.0, 0.0, 1.0, 0.0]
```

Trong tệp `astra_pro.launch.py`, cấu hình cưỡng bức trình điều khiển nạp dữ liệu từ URL tĩnh này bằng cú pháp:

```python
{'color_info_url': 'file:///home/user/ros2_ws/src/ros2_astra_camera/config/color_astra_pro.yaml'},
{'ir_info_url': 'file:///home/user/ros2_ws/src/ros2_astra_camera/config/ir_astra_pro.yaml'}
```

Kỹ thuật này đảm bảo rằng dòng dữ liệu luôn đồng nhất và đúng chuẩn bất kể tình trạng phần cứng truyền dẫn (USB bus errors).

---

## 7. Trực quan Hóa Không Gian 3D và Ứng dụng Bậc Cao

Một khi các chuỗi cung ứng thông tin ở cấp thấp đã hoàn thiện, dữ liệu sẽ được đẩy vào đường ống xử lý bậc cao của ROS2. Hệ thống ROS cung cấp gói `depth_image_proc` bao gồm một hệ sao (constellation) các nodelets. Cụm tiến trình này tự động đăng ký vào các topic ảnh (`/camera/depth/image_raw`) và siêu dữ liệu camera (`/camera/depth/camera_info`), nạp ma trận Projection (P) và chuyển đổi không gian 2D pixel sang không gian Metric (x,y,z float 32-bit), xuất ra topic `/camera/depth/points` mang định dạng `sensor_msgs/PointCloud2`.

### 7.1. Cấu hình Công cụ Kiểm thử (Testing with RViz2)

Mọi dữ liệu sinh ra phải được kiểm chứng bằng hình ảnh. Sử dụng công cụ `rviz2` mặc định của nền tảng ROS.

Quá trình trực quan hóa (visualization) gặp lỗi phổ biến nhất liên quan đến Cây Tọa độ (TF Tree). Cảm biến trên robot không thể tồn tại độc lập mà phải có gốc tọa độ (Frame of Reference).

- Khởi động `rviz2`.
- Trong mục **Global Options**, trường **Fixed Frame** phải được trỏ đích xác vào `camera_depth_optical_frame` (hoặc tên tương ứng định nghĩa trong tham số camera) thay vì để mặc định là `map` hoặc `base_link`. Trục Z trong quang học (optical frame) hướng ra phía trước mặt ống kính, trong khi trục Z của robot học thường hướng lên trời.
- Cấu hình Policy của Display Type PointCloud2 thành `Best Effort` để tiếp nhận dữ liệu liên tục không bị nghẽn.

**Dọn dẹp hệ thống:** Kiến trúc IPC (Intra-process communication) của ROS chia sẻ bộ nhớ cục bộ (shared memory - shm). Khi người dùng khởi động và ngắt camera nhiều lần bằng lệnh `Ctrl+C`, hệ điều hành Linux (cả WSL2 và Ubuntu trên Pi) không kịp giải phóng tài nguyên. Việc chạy lệnh dọn dẹp trước mỗi chu trình test là một thói quen chuyên nghiệp cần duy trì:

```bash
ros2 run astra_camera cleanup_shm_node
```

Tiến trình này sẽ rà soát và xóa các khóa semaphore tồn đọng trong `/dev/shm/`.

### 7.2. Tích hợp Dự án Ứng dụng Bậc Cao (Downstream Applications)

Dựa trên nền tảng dữ liệu đã xây dựng, kho lưu trữ [`icclab_summit_xl`](https://github.com/icclab/icclab_summit_xl) trên Github là một hình mẫu chuẩn mực để người dùng tham chiếu cách mở rộng các tính năng của mình.

1. **Định vị và Lập bản đồ (SLAM):** Tích hợp với `rtabmap.launch.py`. Node này sẽ kết hợp luồng Odometry của robot (thông qua Wheel Encoder hoặc IMU) cùng với luồng ảnh RGB-D đã nắn chỉnh từ Astra Pro. Sử dụng các đặc trưng hình học kết hợp với phát hiện vòng lặp (Loop Closure), hệ thống tạo ra một bản đồ chiếm chỗ (Occupancy Grid) và một bản đồ 3D lưu trữ dưới tệp cơ sở dữ liệu `rtabmap.db`.

2. **Khả năng Cảm nhận Ngữ nghĩa (Semantic Perception):** Ảnh RGB có thể được phân nhánh vào một máy chủ phân đoạn (như LangSAM - Language Segment Anything) để khoanh vùng vật thể. Lớp mask 2D sau đó được phủ lên luồng PointCloud 3D của Astra Pro để cắt ra tọa độ không gian chính xác của đồ vật.

3. **Điều hướng và Thao tác Vật lý (Nav2 và MoveIt2):** Các điểm tọa độ 3D từ cảm biến sẽ cập nhật vào Costmap của Nav2 để nhận diện chướng ngại vật cục bộ. Đồng thời, tọa độ vật thể sẽ được truyền cho bộ lập kế hoạch chuyển động MoveIt2 để điều khiển cánh tay robot thực hiện hành vi bám nắm (Grasping).

---

## 8. Khuyến nghị và Tổng kết Kiến trúc

Dự án phát triển nền tảng ứng dụng từ cảm biến Orbbec Astra Pro trên hệ sinh thái ROS2 Jazzy là một bài toán tích hợp liên ngành, đòi hỏi kỹ sư xử lý rào cản từ cấp độ hệ điều hành đến ngôn ngữ lập trình và kiến trúc phân phối mạng. Dựa trên các dữ liệu phân tích:

1. **Ưu thế Cô lập Môi trường:** Tránh triển khai các bộ công cụ di sản (legacy SDKs) trực tiếp trên Windows Native để ngăn chặn tận gốc hiện tượng "DLL Hell" và xung đột `VC_redist`. Giao thức chia sẻ gói tin USB qua `usbipd` vào WSL2 là một thiết kế bảo mật và ổn định cao, mang lại môi trường Ubuntu 24.04 lõi thuần túy.

2. **Vá Lỗi Lõi Hệ Thống:** Không phụ thuộc vào nhánh `v2-main` chính thức (vốn bỏ rơi cấu trúc OpenNI). Kế thừa và tái cấu trúc mã nguồn `ros2_astra_camera` theo tiêu chuẩn C++ hiện đại của Jazzy, kết hợp kỹ thuật ghi đè thông số `camera_info` qua file YAML tĩnh là chiến lược duy nhất để luồng `PointCloud2` không bị đứt gãy do giá trị toán học `NaN`.

3. **Chiến lược "No-SDK":** Đối với các bài toán Edge AI (Trí tuệ nhân tạo biên) trên Raspberry Pi không cần mô phỏng 3D hoặc tương tác vật lý không gian, kiến trúc tách biệt luồng UVC (V4L2) qua OpenCV để chạy YOLO/SAM, và dùng giao diện mỏng OpenNI2 Python để tính toán khoảng cách đem lại hiệu năng vượt trội, loại trừ hoàn toàn các tiến trình middleware cồng kềnh.

4. **Kiểm soát Tài Nguyên Nhúng:** Các cấu trúc ARM64 của nền tảng SBC đòi hỏi quy định ngặt nghèo về không gian bộ nhớ khi dùng lệnh `colcon build`, cấu hình tự động phân quyền truy cập USB `udev rules`, và bắt buộc định tuyến băng thông QoS của ROS2 về `SENSOR_DATA` để bảo vệ năng lực kết nối không dây của toàn hệ thống. Tái sử dụng thiết kế hệ thống từ các dự án lớn như ICCLab sẽ đẩy nhanh quá trình chuyển giao công nghệ vào thực tiễn tự động hóa.

---

## 9. Nguồn Tham khảo

- [RGB-D Camera-based Human Head Motion Detection and Recognition System for PET Scanning - Preprints.org](https://www.preprints.org/)
- [A Review of Depth-based Human Motion Enhancement: Past and Present - PMC](https://pmc.ncbi.nlm.nih.gov/)
- [A Comparison of Depth Sensors for 3D Object Surface Reconstruction - CMBES Proceedings](https://proceedings.cmbes.ca/)
- [Mapping and Navigation with AgileX Limo ROS2 - ROS General - Open Robotics Discourse](https://discourse.openrobotics.org/)
- [High-Capacity Spatial Structured Light for Robust and Accurate Reconstruction - MDPI](https://www.mdpi.com/)
- [Orbbec Astra (Pro) - MRL](https://mrl.cs.vsb.cz/)
- [Dot-coded structured light for accurate and robust 3D reconstruction - Optica](https://opg.optica.org/)
- [Astra Pro: No valid camera_info published – PointCloud generation fails due to missing intrinsics · Issue #134 · orbbec/OrbbecSDK_ROS2 - GitHub](https://github.com/orbbec/OrbbecSDK_ROS2/issues/134)
- [Jetson平台Orbbec深度相机ROS驱动部署与优化实战 - CSDN博客](https://blog.csdn.net/)
- [Metrological Qualification of the Orbbec Astra S™ Structured-Light Camera - ResearchGate](https://www.researchgate.net/)
- [Helbling-Technik/HelMoRo_OrbbecSDK_ROS2 - GitHub](https://github.com/Helbling-Technik/HelMoRo_OrbbecSDK_ROS2)
- [orbbec-astra-wiki Documentation](https://astra-wiki.readthedocs.io/)
- [orbbec/OrbbecSDK_ROS2: OrbbecSDK ROS2 wrapper - GitHub](https://github.com/orbbec/OrbbecSDK_ROS2)
- [Error building astra_camera pkg on ROS2 Iron · Issue #7 · orbbec/ros2_astra_camera - GitHub](https://github.com/orbbec/ros2_astra_camera/issues/7)
- [ros2 jazzy环境下使用ros2_astra_camera - CSDN博客](https://blog.csdn.net/)
- [PC 에서 카메라 확인 - iru - Tistory](https://haniru.tistory.com/)
- [터틀봇 와플 테스트 - iru - Tistory](https://haniru.tistory.com/)
- [icclab/icclab_summit_xl: Base scripts for the Robotnik summit_xl robot at ICCLab - GitHub](https://github.com/icclab/icclab_summit_xl)
- [CollaborativeRoboticsLab/astra_legacy_ros: ROS2 wrapper for older astra camera models - GitHub](https://github.com/CollaborativeRoboticsLab/astra_legacy_ros)
- [Inconsistent intrinsic camera and projection parameters · Issue #169 · orbbec/OrbbecSDK_ROS2 - GitHub](https://github.com/orbbec/OrbbecSDK_ROS2/issues/169)
- [Understanding USB, on windows and linux in order to use DfuSe from STM - Medium](https://olof-astrand.medium.com/)
- [Windows USB/IP (usbipd) | ITOHI](https://itohi.com/)
- [SDKManager 2.0.0 File System and OS Install Error on WSL2 Ubuntu 22.04 - NVIDIA Forums](https://forums.developer.nvidia.com/)
- [Flash JetPack with WSL2 | Seeed Studio Wiki](https://wiki.seeedstudio.com/)
- [Using WSL2 for Upgrading VOXL SDK | ModalAI Technical Docs](https://docs.modalai.com/)
- [Can't attach since it keeps saying windows is using the device · Issue #1036 · dorssel/usbipd-win - GitHub](https://github.com/dorssel/usbipd-win/issues/1036)
- [docs/README_CN.md · Femto Mega Datacollector - GitLab (MSU)](https://gitlab.msu.edu/)
- [Linux环境下奥比中光摄像头开发环境搭建（基于Orbbec SDK） - 博客园](https://www.cnblogs.com/)
- [peanut-robotics/orbbec_sdk_ros1: OrbbecSDK ROS wrapper - GitHub](https://github.com/peanut-robotics/orbbec_sdk_ros1)
- [奥比中光科技集团股份有限公司/OrbbecSDK_ROS2 - Gitee](https://gitee.com/)
- [Raspberry Pi 5 ROS 2 Jazzy Setup Guide (Ubuntu 24.04) - RoboCloud Hub](https://robocloud-dashboard.vercel.app/)
- [v2-main branch failed to initialize device · Issue #80 · orbbec/OrbbecSDK_ROS2 - GitHub](https://github.com/orbbec/OrbbecSDK_ROS2/issues/80)
- [Unable to install Orbbec Astra Camera ROS2 GitHub - Robotics Stack Exchange](https://robotics.stackexchange.com/)
- [rgbd_launch - ROS Wiki](https://wiki.ros.org/rgbd_launch)
- [orbbec/ros2_astra_camera - GitHub](https://github.com/orbbec/ros2_astra_camera)
- [Nuitrack Knowledge Base](https://community.nuitrack.com/)
- [README.md · xarm7_internship - GitLab (IMT Atlantique)](https://gitlab.imt-atlantique.fr/)
- [Newest 'ros' Questions - Stack Overflow](https://stackoverflow.com/questions/tagged/ros)
- [Astra Pro深度图在RViz2中显示为全黑或无数据，如何排查？](https://ask.csdn.net/)
- [LLM-Based Semantic Navigation on a Low-Cost ROS Mobile Robot: A Hybrid Edge–Cloud Architecture - MDPI](https://www.mdpi.com/)

---

## 📄 License

Tài liệu này được cung cấp cho mục đích tham khảo kỹ thuật và giáo dục. Vui lòng dẫn nguồn khi tái sử dụng.

## 🤝 Đóng góp

Mọi đóng góp, sửa lỗi (pull requests) và thảo luận (issues) về việc vá lỗi driver `ros2_astra_camera` trên ROS2 Jazzy đều được hoan nghênh.
```

**Ghi chú khi paste vào GitHub:**
- Một số nguồn trong ảnh chụp màn hình chỉ hiển thị domain gốc (không có URL đầy đủ đến bài viết cụ thể), nên mình đã trỏ link về trang chủ của domain đó (ví dụ `preprints.org`, `pmc.ncbi.nlm.nih.gov`...). Bạn có thể thay bằng URL bài viết chính xác nếu có sẵn trong lịch sử tìm kiếm của bạn.
- Các link GitHub repo (`orbbec/OrbbecSDK_ROS2`, `orbbec/ros2_astra_camera`, `libuvc/libuvc`, `icclab/icclab_summit_xl`, `CollaborativeRoboticsLab/astra_legacy_ros`, `dorssel/usbipd-win`) đã được xác thực đúng theo tên repo được nêu trong báo cáo.

This response was generated by Apollo AI, an internal AI assistant. Please validate important outputs against official Apollo documents, systems, and responsible teams before acting on them.
