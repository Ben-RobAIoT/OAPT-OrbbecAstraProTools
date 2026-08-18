# Chạy Orbbec Astra Pro trên WSL2 (Ubuntu 24.04 + ROS2 Jazzy) từ Windows 11 — Guide đầy đủ

Trước khi vào chi tiết, có 2 điểm mấu chốt cần hiểu rõ vì chúng chính là nguồn gốc "xung đột" bạn hay gặp:

1. **Astra Pro có 2 cảm biến USB tách biệt**: một camera **RGB chuẩn UVC** (nhận diện như webcam bình thường) và một module **Depth/IR** (ánh sáng cấu trúc, giao tiếp qua OpenNI2/libuvc riêng). Windows/WSL2 sẽ thấy đây là **2 thiết bị USB khác nhau**, cần passthrough cả hai.
2. **Depth và IR dùng chung 1 sensor vật lý** → hầu hết driver (astra_camera, OrbbecSDK) **không cho chạy Depth + IR raw cùng lúc**, đây là giới hạn phần cứng chứ không phải lỗi cấu hình. Bạn chỉ chạy song song được **RGB + Depth** hoặc **RGB + IR**, không phải cả 3 cùng lúc theo kiểu raw.

---

## Bước 1 — Passthrough USB từ Windows sang WSL2

WSL2 không thấy USB trực tiếp, cần `usbipd-win`.

**Trên PowerShell (Admin) ở Windows:**
```powershell
winget install usbipd
usbipd list
```
Bạn sẽ thấy 2 dòng cho Astra Pro, ví dụ:
```
2-3  2bc5:0403  Orbbec RGB Camera
2-4  2bc5:0501  Orbbec Depth/IR Sensor
```
Gắn cả hai vào WSL2:
```powershell
usbipd bind --busid 2-3
usbipd bind --busid 2-4
usbipd attach --wsl --busid 2-3
usbipd attach --wsl --busid 2-4
```
> Mẹo: viết 1 file `.ps1` để attach cả 2 mỗi lần bật máy, vì `usbipd attach` không tự nhớ sau reboot.

**Kiểm tra trong Ubuntu (WSL2):**
```bash
lsusb
```
Phải thấy cả 2 thiết bị Orbbec (vendor `2bc5` hoặc `05a9` tùy bản Astra Pro).

---

## Bước 2 — udev rules trong Ubuntu 24.04

```bash
sudo tee /etc/udev/rules.d/99-orbbec-astra.rules > /dev/null <<'EOF'
SUBSYSTEM=="usb", ATTR{idVendor}=="2bc5", MODE:="0666", OWNER:="root", GROUP:="video"
SUBSYSTEM=="usb", ATTR{idVendor}=="05a9", MODE:="0666", OWNER:="root", GROUP:="video"
EOF

sudo usermod -aG video $USER
sudo udevadm control --reload-rules
sudo udevadm trigger
```
Lưu ý: WSL2 không có systemd-udevd chạy full như máy thật, nên nếu quyền vẫn bị từ chối, thêm dòng khởi động thủ công `sudo udevadm trigger --attr-match=subsystem=usb` mỗi lần attach thiết bị, hoặc đơn giản `sudo chmod 666 /dev/bus/usb/00X/00Y` tương ứng.

---

## Bước 3 — Chọn driver ROS2 phù hợp Jazzy

`ros-jazzy-astra-camera` **chưa có binary chính thức** (repo `ros-drivers/astra_camera` dừng ở Humble/Iron). Với Jazzy, dùng driver chính chủ Orbbec:

```bash
mkdir -p ~/ros2_ws/src && cd ~/ros2_ws/src
git clone https://github.com/orbbec/OrbbecSDK_ROS2.git
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install --event-handlers console_direct+
echo "source ~/ros2_ws/install/setup.bash" >> ~/.bashrc
source ~/.bashrc
```
Package này build sẵn hỗ trợ Jazzy và cover cả dòng Astra/Astra Pro/Gemini.

---

## Bước 4 — Launch file cấu hình RGB / Depth / IR không xung đột

Tạo `~/ros2_ws/src/astra_pro_launch/launch/astra_pro.launch.py`:

```python
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('depth_mode', default_value='true'),
        DeclareLaunchArgument('ir_mode', default_value='false'),

        Node(
            package='orbbec_camera',
            executable='orbbec_camera_node',
            name='astra_pro',
            output='screen',
            parameters=[{
                'camera_name': 'astra_pro',
                'enable_color': True,
                'enable_depth': LaunchConfiguration('depth_mode'),
                'enable_ir': LaunchConfiguration('ir_mode'),
                'depth_registration': True,   # căn Depth khớp RGB
                'color_width': 640, 'color_height': 480, 'color_fps': 30,
                'depth_width': 640, 'depth_height': 480, 'depth_fps': 30,
                'uvc_backend': 'libuvc',
            }]
        ),
    ])
```

Chạy 2 profile khác nhau (không bao giờ bật cả depth+ir cùng lúc):
```bash
ros2 launch astra_pro_launch astra_pro.launch.py depth_mode:=true  ir_mode:=false   # RGB + Depth
ros2 launch astra_pro_launch astra_pro.launch.py depth_mode:=false ir_mode:=true    # RGB + IR
```
Nếu cần đổi mode khi node đang chạy mà không restart, dùng `ros2 param set` (nếu driver hỗ trợ dynamic param) hoặc script bash toggle giữa 2 launch trên — **tuyệt đối không mở 2 node cùng claim 1 USB interface**, đó là nguyên nhân lỗi `Resource busy` / `libusb_claim_interface failed` bạn có thể đang gặp.

---

## Bước 5 — Xem hình ảnh "trong" VSCode mà không đụng driver

Có 2 cách, chọn theo nhu cầu:

### Cách A — Nhanh, dùng WSLg (khuyên dùng để test)
Windows 11 + WSL2 có sẵn WSLg → GUI Linux tự hiện ra như app Windows, chạy song song cửa sổ VSCode, **không xung đột** vì chỉ subscribe topic chứ không mở lại thiết bị:
```bash
ros2 run rqt_image_view rqt_image_view   # chọn topic /astra_pro/color/image_raw, /depth/image_raw, /ir/image_raw
# hoặc
rviz2
```

### Cách B — Thực sự nhúng vào tab VSCode (Foxglove qua Simple Browser)
Cách này cho cảm giác "mở trên VSCode" đúng nghĩa vì hiển thị ngay trong 1 tab editor:

```bash
sudo apt install ros-jazzy-rosbridge-suite
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
```
Trong VSCode: `Ctrl+Shift+P` → **Simple Browser: Show** → nhập `https://app.foxglove.dev` → kết nối tới `ws://localhost:9090` → tạo 3 panel **Image** trỏ tới:
- `/astra_pro/color/image_raw`
- `/astra_pro/depth/image_raw`
- `/astra_pro/ir/image_raw` (chỉ hiện khi bật ir_mode)

→ Xem cả RGB/Depth/IR ngay trong 1 tab VSCode, không cần app rời, không tranh chấp USB vì mọi thứ đi qua topic ROS2.

---

## Checklist tránh xung đột thường gặp

| Triệu chứng | Nguyên nhân | Cách xử lý |
|---|---|---|
| `Device or resource busy` | 2 node cùng mở camera, hoặc chưa `usbipd detach` lần trước | Chỉ 1 node driver duy nhất, `usbipd detach`/`attach` lại |
| Depth và IR đều trống | Bật cả `enable_depth` + `enable_ir` cùng lúc | Chỉ bật 1 trong 2 (giới hạn phần cứng) |
| Mất kết nối USB sau khi Windows sleep | usbip không tự reconnect | Viết script PowerShell attach lại sau khi resume |
| Permission denied /dev/bus/usb | udev rule chưa áp dụng trong WSL2 | `sudo chmod 666` thủ công hoặc chạy lại `udevadm trigger` |
| FPS thấp/giật khi qua WSL2 | USB/IP tunnel qua TCP nội bộ có overhead | Giảm xuống 640x480@30fps thay vì 1280x720 |

Bạn muốn mình viết luôn file `.ps1` auto-attach cả 2 thiết bị Astra Pro khi khởi động Windows, hoặc soạn sẵn `tasks.json`/`launch.json` cho VSCode để bấm 1 phím chạy toàn bộ pipeline (usbipd attach → colcon build → ros2 launch → mở Foxglove) không?

This response was generated by Apollo AI, an internal AI assistant. Please validate important outputs against official Apollo documents, systems, and responsible teams before acting on them.
