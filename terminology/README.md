# 📖 Bảng Chú giải Thuật ngữ Kỹ thuật (Terminology Glossary)
> Tài liệu giải thích chi tiết toàn bộ thuật ngữ chuyên môn xuất hiện trong dự án
> "Orbbec Astra Pro trên ROS2 Jazzy & Edge Computing". Dùng để tra cứu nhanh khi đọc
> README.md chính hoặc khi trao đổi kỹ thuật với người khác.

---

## 📑 Mục lục

1. [Công nghệ Cảm biến & Quang học 3D](#1-công-nghệ-cảm-biến--quang-học-3d)
2. [Giao thức & Chuẩn Kết nối Phần cứng](#2-giao-thức--chuẩn-kết-nối-phần-cứng)
3. [Hệ điều hành, Ảo hóa & Mạng (WSL2 / USB-IP)](#3-hệ-điều-hành-ảo-hóa--mạng-wsl2--usb-ip)
4. [ROS2, Middleware & Kiến trúc Phần mềm](#4-ros2-middleware--kiến-trúc-phần-mềm)
5. [Toán học Camera & Hiệu chỉnh (Calibration)](#5-toán-học-camera--hiệu-chỉnh-calibration)
6. [Edge Computing & Tối ưu Hệ thống Nhúng](#6-edge-computing--tối-ưu-hệ-thống-nhúng)
7. [Thuật toán, AI & Ứng dụng Bậc cao](#7-thuật-toán-ai--ứng-dụng-bậc-cao)
8. [Thuật ngữ Lập trình & Công cụ Chung](#8-thuật-ngữ-lập-trình--công-cụ-chung)

---

## 1. Công nghệ Cảm biến & Quang học 3D

### **RGB-D Camera**
Loại camera phát ra đồng thời hai luồng dữ liệu: **RGB** (ảnh màu thông thường như webcam) và **D – Depth** (bản đồ khoảng cách/chiều sâu của từng điểm ảnh tới camera). Orbbec Astra Pro là một camera RGB-D. "D" chính là thứ làm nên khả năng "nhìn thấy không gian 3 chiều" thay vì chỉ ảnh phẳng 2D.

### **Structured Light (Ánh sáng cấu trúc)**
Công nghệ đo chiều sâu bằng cách **chiếu một mẫu ánh sáng đã biết trước** (thường là hồng ngoại, mắt người không thấy) lên vật thể, rồi quan sát mẫu ánh sáng đó bị **biến dạng** thế nào khi phản chiếu lại. Từ độ biến dạng, hệ thống suy ra hình dạng 3D của vật thể. Đây là công nghệ mà Astra Pro sử dụng — khác với Kinect v2 (dùng Time-of-Flight).

### **Time-of-Flight (ToF)**
Công nghệ đo chiều sâu khác, hoạt động bằng cách đo **thời gian ánh sáng bay đi và phản xạ về** cảm biến (giống radar/lidar nhưng bằng ánh sáng). Tốc độ ánh sáng đã biết, nên đo thời gian = tính được khoảng cách. Ưu điểm: đo nhanh, xa. Nhược điểm: độ chính xác tuyệt đối thường kém hơn Structured Light ở tầm gần.

### **Stereo Vision (Thị giác lập thể)**
Công nghệ đo chiều sâu bằng cách dùng **hai camera đặt cách nhau một khoảng cố định** (giống hai mắt người), so sánh sự khác biệt vị trí của cùng một điểm trên hai ảnh để tính khoảng cách bằng tam giác lượng giác. Không cần phát sáng chủ động như Structured Light hay ToF.

### **IR Projector (Máy chiếu hồng ngoại)**
Bộ phận phần cứng trong Astra Pro phát ra **tia hồng ngoại (infrared)** mang theo mẫu điểm sáng (speckle pattern) chiếu vào vật thể. Đây là "nguồn sáng chủ động" phục vụ cho việc đo Depth, hoàn toàn tách biệt với đèn LED hay ánh sáng môi trường dùng cho camera RGB.

### **IR Camera (Cảm biến hồng ngoại)**
Cảm biến chuyên thu nhận ánh sáng hồng ngoại (khác với cảm biến RGB thu ánh sáng khả kiến). Nó "chụp lại" mẫu điểm sáng do IR Projector phát ra sau khi đã bị vật thể làm biến dạng, làm nguyên liệu đầu vào để tính Depth.

### **ASIC (Application-Specific Integrated Circuit)**
Một loại **chip vi mạch được thiết kế chuyên biệt** cho một tác vụ duy nhất (ở đây là tính toán Depth từ ảnh IR), khác với CPU/GPU đa dụng. ASIC xử lý nhanh và tiết kiệm năng lượng hơn nhưng không thể lập trình lại chức năng gốc. Đây chính là "bộ não" nằm ngay trong thân camera Astra Pro, thực hiện phép toán biến ảnh IR thô thành bản đồ Depth trước khi gửi ra máy tính.

### **Speckle Pattern (Mẫu điểm sáng lốm đốm)**
Mảng hàng chục nghìn chấm sáng hồng ngoại được mã hóa theo cấu trúc giả ngẫu nhiên (pseudo-random), do IR Projector chiếu ra. "Giả ngẫu nhiên" nghĩa là nhìn có vẻ lộn xộn nhưng thực chất đã biết trước và cố định, giúp ASIC dễ dàng nhận diện khu vực nào của mẫu bị lệch đi bao nhiêu.

### **Disparity (Độ lệch/thị sai)**
Độ lệch vị trí giữa điểm sáng ở **mẫu gốc đã lưu sẵn** trong phần cứng và **mẫu thu được thực tế** sau khi phản xạ từ vật thể. Disparity càng lớn thì vật càng gần (hoặc càng xa, tùy chiều), đây là đại lượng trung gian để tính ra khoảng cách thực (đơn vị mm).

### **Block Matching**
Một thuật toán xử lý ảnh dùng để **so khớp từng khối nhỏ (block) pixel** giữa hai ảnh (hoặc giữa ảnh thu và mẫu gốc) nhằm tìm ra độ lệch (disparity) tương ứng. Là một trong hai thuật toán ASIC của Astra Pro có thể dùng để tính Depth.

### **Semi-Global Matching (SGM)**
Một thuật toán so khớp nâng cao hơn Block Matching, tối ưu hóa độ lệch (disparity) không chỉ dựa trên từng khối riêng lẻ mà còn xét đến **sự liên tục/mượt mà giữa các điểm lân cận** trên toàn ảnh, cho kết quả Depth chính xác và ít nhiễu hơn nhưng tốn tính toán hơn.

### **Metrological Qualification (Đánh giá đo lường học)**
Quá trình kiểm định khoa học về **độ chính xác và độ tin cậy** của một thiết bị đo (ở đây là camera Depth), thường so sánh với thước đo chuẩn thực tế. Kết quả cho biết sai số (ví dụ ±2.5mm) trong điều kiện cụ thể, giúp người dùng biết camera đáng tin đến mức nào cho một ứng dụng nhất định.

### **Pose Estimation (Ước lượng tư thế)**
Bài toán xác định **vị trí và hướng** của một vật thể/con người trong không gian 3D (ví dụ: tư thế cơ thể người, góc quay của tay robot) dựa trên dữ liệu cảm biến như Depth camera.

---

## 2. Giao thức & Chuẩn Kết nối Phần cứng

### **UVC (USB Video Class)**
Một **chuẩn giao thức quốc tế** cho phép các thiết bị video (webcam) giao tiếp với máy tính mà **không cần cài driver riêng** — hệ điều hành đã có sẵn driver chuẩn (`uvcvideo` trên Linux). Kênh RGB của Astra Pro tuân theo chuẩn này, nên có thể coi nó như một webcam thông thường.

### **OpenNI / OpenNI2**
Một **thư viện phần mềm mã nguồn mở** (ban đầu do tổ chức OpenNI phát triển, sau này PrimeSense/Occipital tiếp quản) chuyên dùng để giao tiếp với các camera Depth dùng công nghệ Structured Light (như Astra, Kinect v1). Đây là lớp phần mềm trung gian nhẹ, thay thế cho các SDK độc quyền nặng nề của Orbbec.

### **libusb**
Thư viện lập trình mã nguồn mở cho phép ứng dụng ở **tầng người dùng (userspace)** giao tiếp trực tiếp với thiết bị USB mà không cần viết driver kernel riêng. OpenNI dùng libusb để nói chuyện với luồng Depth/IR của Astra Pro.

### **libuvc**
Thư viện mã nguồn mở tương tự libusb nhưng **chuyên biệt cho chuẩn UVC**, giúp phần mềm điều khiển webcam/camera RGB ở mức thấp (đọc/ghi tham số, định dạng khung hình...). Astra Pro dùng thư viện này cho kênh màu.

### **V4L2 (Video4Linux2)**
API/chuẩn giao tiếp của **nhân Linux (kernel)** dành cho các thiết bị video (webcam, capture card...). Khi camera UVC được cắm vào máy Linux, nó sẽ xuất hiện dưới dạng file thiết bị như `/dev/video0`, và các ứng dụng (như OpenCV) đọc dữ liệu qua API V4L2.

### **Media Foundation**
Framework xử lý đa phương tiện (âm thanh/video) của **Microsoft Windows**, đóng vai trò tương tự V4L2 nhưng trên Windows — là lớp trung gian giúp Windows truy xuất camera UVC mà không cần driver riêng.

### **Device Descriptor**
Một khối dữ liệu nhỏ mà mọi thiết bị USB phải gửi cho máy chủ khi cắm vào, mô tả **thông tin nhận dạng cơ bản**: nhà sản xuất, loại thiết bị, khả năng hỗ trợ... Hệ điều hành dựa vào đây để biết cần nạp driver nào.

### **Vendor ID (VID) / Product ID (PID)**
Hai mã số (thường ở dạng hex, ví dụ `2bc5` cho Orbbec) được gán cố định cho **hãng sản xuất** (Vendor ID) và **từng dòng sản phẩm cụ thể** (Product ID) của hãng đó. Hệ điều hành và các quy tắc udev dùng cặp mã này để nhận diện chính xác thiết bị nào đang cắm vào, từ đó áp dụng driver/quyền phù hợp.

### **EEPROM (Electrically Erasable Programmable Read-Only Memory)**
Một loại bộ nhớ nhỏ, **không mất dữ liệu khi mất điện**, gắn ngay trên bo mạch camera, lưu trữ các thông số hiệu chỉnh gốc (calibration data) như tiêu cự, độ méo ống kính... được nạp sẵn từ nhà máy. Nếu driver đọc lỗi EEPROM này (thường do giới hạn USB 2.0), dữ liệu camera_info sẽ bị sai (dẫn đến lỗi NaN đã nêu ở phần 2.2 README gốc).

---

## 3. Hệ điều hành, Ảo hóa & Mạng (WSL2 / USB-IP)

### **WSL2 (Windows Subsystem for Linux 2)**
Công nghệ của Microsoft cho phép chạy một **nhân Linux thật** (không phải giả lập) bên trong Windows, gần như một máy ảo nhẹ tích hợp sâu vào hệ điều hành. Cho phép chạy Ubuntu 24.04 + ROS2 ngay trên máy Windows mà không cần cài song song hai hệ điều hành (dual-boot).

### **DLL Hell**
Thuật ngữ dân gian mô tả tình trạng **xung đột giữa các thư viện liên kết động (.dll)** trên Windows — khi hai phần mềm khác nhau cần các phiên bản khác nhau của cùng một thư viện, dẫn đến crash, lỗi không tương thích. SDK cũ của Orbbec (biên dịch bằng MSVC cũ) hay gặp vấn đề này.

### **VC_redist (Visual C++ Redistributable)**
Gói thư viện runtime của Microsoft mà nhiều phần mềm Windows (kể cả SDK của Orbbec) cần có để chạy được. Có nhiều phiên bản khác nhau (2013, 2015, 2019...) và việc cài chồng chéo nhiều phiên bản dễ gây xung đột (một dạng của DLL Hell).

### **usbipd-win**
Phần mềm mã nguồn mở (dự án `dorssel/usbipd-win`) chạy trên Windows, cho phép **"chia sẻ" một thiết bị USB vật lý qua mạng ảo** để một máy khác (ở đây là WSL2) có thể sử dụng như thể nó cắm trực tiếp vào máy đó.

### **USB/IP (USB over IP)**
Giao thức mạng cho phép **đóng gói dữ liệu USB thành các gói tin TCP/IP** để truyền qua mạng (kể cả mạng ảo nội bộ), từ đó "tách" thiết bị USB khỏi vị trí vật lý của nó. usbipd-win chính là cài đặt của giao thức này trên Windows.

### **URB (USB Request Block)**
Đơn vị dữ liệu cơ bản mà hệ điều hành dùng để **giao tiếp lệnh với thiết bị USB** ở tầng thấp (ví dụ: "gửi dữ liệu này", "yêu cầu trạng thái"...). USB/IP hoạt động bằng cách chặn và chuyển tiếp các URB này qua mạng.

### **Hyper-V Virtual Switch**
Một "công tắc mạng ảo" do công nghệ ảo hóa Hyper-V của Windows tạo ra, dùng để **kết nối mạng giữa Windows host và các máy ảo/WSL2** bên trong nó. USB/IP tận dụng hạ tầng mạng ảo này để truyền dữ liệu USB.

### **BUSID**
Mã định danh (ví dụ `1-1`, `2-3`) mà `usbipd` gán cho từng **cổng/vị trí vật lý** nơi thiết bị USB đang cắm vào, dùng để chỉ định chính xác thiết bị nào cần bind/attach trong các câu lệnh `usbipd`.

### **bind / attach (trong usbipd)**
- **Bind**: "Khóa" hoặc đăng ký một thiết bị USB để nó sẵn sàng được chia sẻ qua mạng ảo (nhưng Windows tạm thời nhường quyền kiểm soát).
- **Attach**: Thực sự "đẩy" thiết bị đã bind đó vào một máy khác (ở đây là WSL2) để máy đó sử dụng.

### **Udev / Udev Rules**
`udev` là hệ thống quản lý thiết bị tự động của Linux (userspace /dev — device manager). **Udev rules** là các tệp cấu hình định nghĩa hành vi khi một thiết bị được cắm vào/gỡ ra, ví dụ: tự động cấp quyền đọc/ghi, đổi tên file thiết bị (symlink)... Cần thiết để ROS2 (chạy với quyền user thường) có thể truy cập camera mà không cần `sudo`.

### **Permission Denied / MODE 0666**
Lỗi xảy ra khi chương trình cố truy cập một file thiết bị (`/dev/...`) mà không đủ quyền hệ thống cấp cho. `MODE 0666` là ký hiệu quyền Unix cho phép **mọi người dùng đọc và ghi** vào file đó — thường được thiết lập qua udev rules để "mở khóa" quyền truy cập camera cho tài khoản thường.

### **Symlink (Symbolic Link)**
"Liên kết tượng trưng" — một file đặc biệt trong Linux **trỏ đến một file khác**, giống lối tắt (shortcut). Udev rule tạo symlink (ví dụ `orbbec_camera0`) để dễ nhận diện thiết bị bằng tên cố định thay vì tên `/dev/videoX` có thể thay đổi mỗi lần cắm lại.

---

## 4. ROS2, Middleware & Kiến trúc Phần mềm

### **ROS2 (Robot Operating System 2)**
Không phải hệ điều hành theo nghĩa truyền thống, mà là một **framework/middleware phần mềm** cho robot, cung cấp cơ chế giao tiếp giữa các thành phần (node), quản lý cấu hình, công cụ trực quan hóa... ROS2 Jazzy là một phiên bản phát hành cụ thể của framework này, đi kèm Ubuntu 24.04.

### **Node (trong ROS2)**
Một **tiến trình (process) độc lập** trong hệ thống ROS2, thường đảm nhận một chức năng cụ thể (ví dụ: node đọc camera, node xử lý ảnh, node điều khiển động cơ). Các node giao tiếp với nhau qua topic/service.

### **Topic**
"Kênh truyền dữ liệu" trong ROS2 mà các node dùng để gửi (publish) hoặc nhận (subscribe) thông tin, ví dụ topic `/camera/depth/image_raw` chứa ảnh Depth thô.

### **Nodelet**
Một kiểu node đặc biệt được thiết kế để chạy **chung một tiến trình hệ điều hành** với các nodelet khác (thay vì mỗi node một tiến trình riêng), giúp tiết kiệm chi phí sao chép dữ liệu (memory copy) khi xử lý dữ liệu lớn như ảnh/point cloud.

### **Middleware**
Lớp phần mềm trung gian nằm giữa hệ điều hành và ứng dụng, chịu trách nhiệm cho việc giao tiếp, đồng bộ hóa dữ liệu. Trong ROS2, middleware truyền thông chính là **DDS**.

### **DDS (Data Distribution Service)**
Chuẩn giao tiếp publish-subscribe theo thời gian thực mà ROS2 sử dụng làm nền tảng truyền dữ liệu giữa các node (thay vì dùng chuẩn ROS1 cũ). Có nhiều "hãng" triển khai DDS khác nhau như **FastDDS**, **CycloneDDS**.

### **FastDDS / CycloneDDS**
Hai bộ triển khai (implementation) cụ thể phổ biến của chuẩn DDS mà ROS2 có thể chọn dùng làm middleware truyền thông mặc định — quyết định cách các gói tin thực sự di chuyển qua mạng/bộ nhớ.

### **QoS (Quality of Service)**
Tập hợp các **chính sách cấu hình việc truyền dữ liệu** trong DDS/ROS2, ví dụ:
- **Reliable**: đảm bảo mọi gói tin đều đến nơi, gửi lại nếu bị mất — an toàn nhưng có thể gây trễ/nghẽn khi mạng yếu.
- **Best Effort**: gửi "cố hết sức", nếu mất gói thì bỏ qua, không gửi lại — nhanh, phù hợp dữ liệu cảm biến thời gian thực.
- **SENSOR_DATA**: một "profile" (bộ cấu hình QoS dựng sẵn) tối ưu cho dữ liệu cảm biến, thường dùng Best Effort + hàng đợi ngắn, giúp hệ thống luôn ưu tiên dữ liệu mới nhất thay vì cố truyền lại dữ liệu cũ.

### **PointCloud2 (`sensor_msgs/msg/PointCloud2`)**
Kiểu dữ liệu chuẩn của ROS2 dùng để biểu diễn **đám mây điểm 3D** — một tập hợp rất nhiều điểm, mỗi điểm có tọa độ không gian (x, y, z) và có thể kèm màu sắc (r, g, b), được tạo ra từ ảnh Depth kết hợp ảnh RGB.

### **CameraInfo (`sensor_msgs/msg/CameraInfo`)**
Kiểu bản tin ROS2 chứa **thông số hiệu chỉnh của camera** (ma trận K, P, hệ số méo ống kính...), đi kèm mỗi ảnh để các node xử lý phía sau biết cách "giải mã" hình học của ảnh đó thành tọa độ không gian thực.

### **cv_bridge**
Thư viện cầu nối giúp **chuyển đổi qua lại** giữa định dạng ảnh của ROS2 (`sensor_msgs/msg/Image`) và định dạng ảnh của OpenCV (`cv::Mat`), để lập trình viên có thể dùng các hàm xử lý ảnh của OpenCV trên dữ liệu ROS2.

### **image_geometry / pinhole_camera_model**
Thư viện ROS2 cung cấp các công cụ toán học liên quan đến **mô hình camera lỗ kim (pinhole camera model)** — mô hình toán học cơ bản mô tả cách một điểm 3D trong không gian được chiếu thành một điểm 2D trên ảnh, dùng ma trận K/P từ CameraInfo.

### **rclcpp**
Thư viện client C++ chính thức của ROS2 (viết tắt "ROS Client Library C++"), cung cấp các API để viết node, topic, tham số... bằng ngôn ngữ C++.

### **Dynamic Parameters / `add_on_set_parameters_callback`**
Cơ chế cho phép một node ROS2 **thay đổi giá trị cấu hình khi đang chạy** (không cần khởi động lại), và đăng ký một hàm callback để xử lý mỗi khi tham số bị thay đổi. API cụ thể để đăng ký callback này đã thay đổi giữa các phiên bản ROS2, gây lỗi biên dịch khi nâng cấp lên Jazzy.

### **depth_image_proc**
Một gói phần mềm (package) chuẩn của ROS2, chứa các node/nodelet chuyên xử lý ảnh Depth: chuyển ảnh Depth 2D thành đám mây điểm 3D (PointCloud2), đăng ký (registration) Depth khớp với RGB, v.v.

### **Back-projection (Chiếu ngược)**
Phép toán học **chuyển một điểm ảnh 2D (pixel) + giá trị chiều sâu thành tọa độ 3D thực** trong không gian, dùng ma trận Projection (P) làm công cụ tính toán. Đây là bước lõi để tạo ra PointCloud từ ảnh Depth.

### **IPC (Intra-process Communication) / Shared Memory (shm)**
Cơ chế cho phép các tiến trình (hoặc các phần trong cùng tiến trình) trao đổi dữ liệu **qua vùng bộ nhớ dùng chung** thay vì sao chép qua lại — nhanh hơn nhiều so với gửi qua mạng. ROS2 dùng cơ chế này để tối ưu hiệu năng khi truyền ảnh/point cloud dung lượng lớn giữa các node trên cùng máy.

### **Semaphore**
Một cơ chế đồng bộ hóa trong lập trình hệ thống, dùng để **kiểm soát quyền truy cập** vào tài nguyên dùng chung (như shared memory), tránh xung đột khi nhiều tiến trình cùng đọc/ghi. Nếu semaphore "tồn đọng" (không được giải phóng đúng cách khi tắt ROS2 đột ngột), hệ thống có thể bị lỗi ở lần chạy sau.

### **TF Tree (Transform Tree / Cây tọa độ)**
Cấu trúc dữ liệu dạng cây trong ROS2 mô tả **mối quan hệ vị trí/hướng (transform)** giữa các hệ quy chiếu (frame) khác nhau trên robot (ví dụ: frame của camera, frame của bánh xe, frame gốc của robot). Cần thiết để biết dữ liệu từ một cảm biến nằm ở "đâu" trong không gian tổng thể của robot.

### **Fixed Frame**
Trong công cụ RViz2, đây là **hệ quy chiếu gốc** mà mọi dữ liệu hiển thị sẽ được quy đổi về đó. Chọn sai Fixed Frame (ví dụ chọn `map` trong khi camera chưa có frame đó) sẽ khiến RViz2 không hiển thị được gì.

### **Optical Frame vs base_link**
- **Optical Frame** (ví dụ `camera_depth_optical_frame`): hệ tọa độ theo quy ước của ống kính quang học, trục Z hướng ra phía trước ống kính.
- **base_link**: hệ tọa độ gốc của thân robot theo quy ước robot học (thường trục Z hướng lên trên).
Hai quy ước trục khác nhau này là nguyên nhân phổ biến gây hiển thị sai lệch nếu cấu hình nhầm.

---

## 5. Toán học Camera & Hiệu chỉnh (Calibration)

### **Intrinsic Matrix (Ma trận K)**
Ma trận 3x3 mô tả các **thông số nội tại của camera**: tiêu cự (focal length, fx/fy) và tọa độ tâm quang học (principal point, cx/cy). Đây là thông số "riêng" của từng camera, không phụ thuộc vị trí đặt camera trong không gian.

### **Projection Matrix (Ma trận P)**
Ma trận 3x4 mở rộng từ ma trận K, dùng để **chiếu một điểm 3D thành điểm 2D trên ảnh đã được nắn chỉnh (rectified)**. Là thông số bắt buộc để `depth_image_proc` tính toán back-projection tạo PointCloud.

### **Rectification Matrix**
Ma trận dùng để "nắn thẳng" (rectify) ảnh gốc, loại bỏ các biến dạng do lắp ráp cơ khí (ví dụ hai ống kính không hoàn toàn song song), giúp các phép toán hình học sau này đơn giản và chính xác hơn.

### **Distortion Coefficients / Distortion Model (plumb_bob)**
Bộ hệ số mô tả **độ méo hình học của ống kính** (như hiệu ứng mắt cá — fisheye, méo hình thùng — barrel distortion). `plumb_bob` là tên một mô hình méo ống kính tiêu chuẩn (còn gọi là mô hình Brown-Conrady) được ROS dùng phổ biến.

### **NaN (Not a Number)**
Giá trị đặc biệt trong toán học máy tính đại diện cho **kết quả không xác định/không hợp lệ** (ví dụ 0/0). Khi ma trận K/P chứa NaN, mọi phép tính hình học dựa trên nó (như back-projection) sẽ cho kết quả vô nghĩa hoặc làm crash chương trình.

### **Calibration Data (Dữ liệu hiệu chỉnh)**
Tập hợp các thông số toán học (ma trận K, P, hệ số méo...) mô tả đặc tính quang học riêng của một camera cụ thể, thường được đo đạc và nạp sẵn vào EEPROM từ nhà máy hoặc tính toán lại bằng công cụ hiệu chỉnh (calibration tool).

---

## 6. Edge Computing & Tối ưu Hệ thống Nhúng

### **Edge Computing (Tính toán biên)**
Mô hình xử lý dữ liệu **ngay tại hoặc gần nơi phát sinh dữ liệu** (ví dụ ngay trên robot, dùng Raspberry Pi) thay vì gửi lên máy chủ/đám mây trung tâm để xử lý. Giúp giảm độ trễ và không phụ thuộc kết nối internet.

### **ARM64 (AArch64)**
Kiến trúc tập lệnh (instruction set architecture) 64-bit của dòng chip ARM, được dùng trong Raspberry Pi và nhiều thiết bị nhúng — khác với kiến trúc **x86_64** phổ biến trên PC/laptop. Sự khác biệt kiến trúc này đôi khi gây ra vấn đề tương thích phần mềm/thư viện.

### **NPU (Neural Processing Unit)**
Một loại chip xử lý chuyên dụng cho các phép toán mạng nơ-ron (AI/deep learning), giúp chạy các mô hình AI nhanh và tiết kiệm năng lượng hơn CPU thông thường.

### **Edge TPU**
Một sản phẩm chip tăng tốc AI cụ thể của Google, được thiết kế để chạy mô hình học sâu (deep learning) hiệu quả ngay trên thiết bị biên (edge), thường dùng dạng USB stick (Coral USB Accelerator) gắn vào Raspberry Pi.

### **OOM (Out of Memory) / OOM Killer**
- **OOM**: Tình trạng hệ thống hết bộ nhớ RAM khả dụng.
- **OOM Killer**: Cơ chế của nhân Linux tự động **"giết" (kết thúc)** một hoặc nhiều tiến trình đang chiếm nhiều RAM nhất để cứu hệ thống khỏi bị treo hoàn toàn khi hết bộ nhớ — thường xảy ra khi biên dịch mã nguồn C++ nặng trên máy có RAM hạn chế như Raspberry Pi.

### **Swap Space (Không gian hoán đổi)**
Một vùng trên ổ đĩa được dùng như **"RAM ảo"** — khi RAM vật lý đầy, hệ điều hành tạm chuyển một phần dữ liệu ít dùng ra đĩa để giải phóng RAM cho tác vụ khác. Chậm hơn RAM thật nhưng giúp tránh crash do OOM.

### **colcon build**
Công cụ build (biên dịch) chính thức của hệ sinh thái ROS2, dùng để biên dịch nhiều package cùng lúc trong một workspace, quản lý thứ tự phụ thuộc giữa các package.

### **MAKEFLAGS / `-j` (jobs song song)**
Cờ cấu hình cho công cụ `make`/`cmake` quy định **số luồng biên dịch chạy song song**. Số càng cao thì biên dịch càng nhanh nhưng tốn càng nhiều RAM cùng lúc — cần giảm xuống (`-j2`) trên các máy yếu như Raspberry Pi để tránh OOM.

### **Sequential Executor (`--executor sequential`)**
Tùy chọn của `colcon build` yêu cầu biên dịch **từng package một, lần lượt** thay vì nhiều package song song, giúp giảm áp lực bộ nhớ trên máy cấu hình thấp.

### **Eigen3**
Thư viện C++ mã nguồn mở chuyên về **đại số tuyến tính** (ma trận, vector), được nhiều thư viện thị giác máy tính/robot học (bao gồm OpenCV, ROS2) sử dụng làm nền tảng tính toán toán học.

### **OpenCV (Open Source Computer Vision Library)**
Thư viện mã nguồn mở phổ biến nhất cho **xử lý ảnh và thị giác máy tính**, cung cấp hàng nghìn hàm xử lý ảnh, video, nhận diện vật thể... Được dùng xuyên suốt trong kiến trúc No-SDK để đọc/hiển thị ảnh RGB và Depth mà không cần SDK riêng.

### **ldconfig**
Lệnh của Linux dùng để **cập nhật bộ nhớ đệm (cache) chứa danh sách các thư viện chia sẻ (`.so`)** đã cài trên hệ thống, cần chạy sau khi cài đặt thủ công một thư viện mới (như libuvc) để hệ điều hành nhận diện được nó.

### **Docker Compose**
Công cụ cho phép định nghĩa và chạy **nhiều container Docker cùng lúc** thông qua một file cấu hình (thường là YAML), giúp đóng gói môi trường phần mềm (kèm mọi phụ thuộc) một cách nhất quán, dễ triển khai lại trên máy khác.

---

## 7. Thuật toán, AI & Ứng dụng Bậc cao

### **SLAM (Simultaneous Localization and Mapping)**
Bài toán kinh điển trong robot học: robot vừa phải **xây dựng bản đồ môi trường xung quanh** vừa phải **tự xác định vị trí của mình** trên bản đồ đó cùng một lúc, chỉ dựa vào dữ liệu cảm biến (camera, lidar...) mà không cần bản đồ có sẵn từ trước.

### **rtabmap (Real-Time Appearance-Based Mapping)**
Một gói phần mềm SLAM mã nguồn mở phổ biến trong ROS2, chuyên dùng dữ liệu RGB-D (ảnh màu + chiều sâu) để dựng bản đồ 3D và định vị robot theo thời gian thực.

### **Odometry**
Thông tin ước lượng **sự thay đổi vị trí/vận tốc** của robot theo thời gian, thường tính từ cảm biến chuyển động (bánh xe, IMU) hoặc từ chính hình ảnh camera (visual odometry).

### **IMU (Inertial Measurement Unit)**
Cảm biến đo **gia tốc và tốc độ góc** (thường tích hợp gia tốc kế + con quay hồi chuyển), giúp ước lượng chuyển động và hướng nghiêng của robot.

### **Loop Closure (Đóng vòng lặp)**
Kỹ thuật trong SLAM giúp hệ thống **nhận ra rằng nó đã quay lại một vị trí đã từng đi qua trước đó**, từ đó điều chỉnh lại toàn bộ bản đồ để sửa các sai số tích lũy theo thời gian, giúp bản đồ chính xác và nhất quán hơn.

### **Occupancy Grid (Lưới chiếm chỗ)**
Một dạng bản đồ 2D chia không gian thành các ô lưới (grid cell) nhỏ, mỗi ô đánh dấu trạng thái: **trống, bị chiếm bởi vật cản, hay chưa biết** — dùng làm nền tảng cho các thuật toán tránh vật cản và tìm đường đi (path planning).

### **Semantic Perception (Nhận thức ngữ nghĩa)**
Khả năng của hệ thống không chỉ "thấy" hình ảnh mà còn **hiểu được ý nghĩa/danh tính của vật thể** trong ảnh đó (ví dụ: đây là cái ghế, đây là con người), thường nhờ các mô hình AI thị giác máy tính.

### **LangSAM (Language Segment Anything Model)**
Một mô hình AI kết hợp giữa mô tả bằng ngôn ngữ tự nhiên (ví dụ: "quả táo màu đỏ") và mô hình phân đoạn ảnh Segment Anything (SAM) của Meta, cho phép **khoanh vùng chính xác một vật thể trong ảnh chỉ bằng câu lệnh mô tả bằng lời**.

### **Mask 2D (Mặt nạ phân đoạn)**
Kết quả đầu ra của thuật toán phân đoạn ảnh (segmentation) — một lớp "mặt nạ" đánh dấu chính xác **những pixel nào thuộc về vật thể** cần quan tâm, dùng để cắt/lọc dữ liệu tương ứng (ví dụ áp lên PointCloud để lấy tọa độ 3D của riêng vật thể đó).

### **Nav2 (Navigation2)**
Bộ gói phần mềm chính thức của ROS2 chuyên trách **điều hướng tự động cho robot di động**: lập kế hoạch đường đi, tránh vật cản, điều khiển bám theo quỹ đạo.

### **Costmap**
Một dạng bản đồ (tương tự Occupancy Grid nhưng có thêm "chi phí" — cost) mà Nav2 dùng để biểu diễn mức độ "nguy hiểm/khó đi" của từng khu vực, giúp thuật toán lập kế hoạch chọn đường đi an toàn và tối ưu nhất.

### **MoveIt2**
Bộ phần mềm chính thức của ROS2 dùng để **lập kế hoạch chuyển động (motion planning) cho cánh tay robot** (robot arm/manipulator), tính toán quỹ đạo di chuyển các khớp sao cho không va chạm và đạt được mục tiêu (ví dụ cầm nắm vật thể).

### **Grasping (Bám nắm)**
Hành vi robot dùng tay gắp/cánh tay để **cầm, nắm lấy một vật thể** — một bài toán kinh điển trong robot học kết hợp cả nhận diện thị giác (biết vật ở đâu) và điều khiển chuyển động (MoveIt2).

### **YOLO (You Only Look Once)**
Một họ mô hình AI phát hiện vật thể (object detection) nổi tiếng vì tốc độ xử lý nhanh, phù hợp chạy thời gian thực trên các thiết bị edge như Raspberry Pi.

### **SAM (Segment Anything Model)**
Mô hình AI của Meta AI có khả năng phân đoạn (khoanh vùng chính xác) **bất kỳ vật thể nào** trong ảnh mà không cần huấn luyện riêng cho từng loại vật thể cụ thể.

---

## 8. Thuật ngữ Lập trình & Công cụ Chung

### **SDK (Software Development Kit)**
Bộ công cụ phần mềm do nhà sản xuất cung cấp (ví dụ Orbbec-SDK/Astra-SDK) bao gồm thư viện, tài liệu, ví dụ mã nguồn... giúp lập trình viên dễ dàng tương tác với phần cứng của họ. Trong dự án này, mục tiêu là **tránh phụ thuộc vào SDK** vì nó nặng nề và khó tùy biến.

### **No-SDK Architecture (Kiến trúc "không SDK")**
Cách tiếp cận thiết kế phần mềm **không dùng bộ SDK độc quyền của nhà sản xuất**, mà thay vào đó dùng trực tiếp các chuẩn giao tiếp mở của hệ điều hành (V4L2/UVC cho RGB) và các thư viện mã nguồn mở nhẹ (OpenNI2 cho Depth), giúp hệ thống nhẹ hơn, minh bạch hơn, dễ kiểm soát lỗi hơn.

### **Bloatware**
Thuật ngữ chỉ phần mềm **cồng kềnh, chứa nhiều tính năng thừa thãi không cần thiết** cho mục đích sử dụng cụ thể của người dùng, làm hệ thống nặng nề, khó bảo trì hơn mức cần thiết.

### **Repository (Kho lưu trữ mã nguồn) / Fork (Nhánh rẽ)**
- **Repository**: Nơi lưu trữ toàn bộ mã nguồn của một dự án phần mềm (thường trên GitHub).
- **Fork**: Một bản sao độc lập của một repository gốc, do người khác/nhóm khác tự phát triển tiếp theo hướng riêng của họ (ví dụ nhánh rẽ cộng đồng `iru-han/ros2_astra_camera` từ bản gốc của Orbbec).

### **Branch (Nhánh)**
Một "phiên bản phát triển song song" trong cùng một repository (ví dụ nhánh `main` và nhánh `v2-main`), cho phép phát triển các tính năng khác nhau mà không ảnh hưởng lẫn nhau, sau này có thể gộp lại (merge) hoặc giữ tách biệt vĩnh viễn.

### **YAML (YAML Ain't Markup Language)**
Một định dạng file văn bản dùng để **lưu trữ dữ liệu cấu hình** theo cấu trúc dễ đọc cho con người (dùng thụt lề, dấu `:`, `-`...). ROS2 dùng YAML rất nhiều để cấu hình tham số (parameters), camera_info, launch file...

### **Launch File (`.launch.py`)**
File cấu hình bằng Python trong ROS2, định nghĩa **những node nào cần khởi chạy cùng lúc** và với tham số gì — giống như một "kịch bản khởi động" cho toàn bộ hệ thống hoặc một phần hệ thống (ví dụ khởi động camera với các tham số độ phân giải, FPS cụ thể).

### **Bandwidth Bottleneck (Nghẽn cổ chai băng thông)**
Tình trạng **tổng lượng dữ liệu cần truyền vượt quá khả năng truyền tải** của đường truyền (ví dụ cổng USB 2.0 hoặc mạng Wi-Fi), gây ra hiện tượng chậm, giật, hoặc mất dữ liệu.

### **FoV (Field of View — Trường nhìn/Góc nhìn)**
Góc không gian mà một cảm biến/camera có thể "nhìn thấy" được. Camera RGB và camera Depth trên Astra Pro thường có FoV hơi khác nhau do đặt ở vị trí vật lý khác nhau trên thân máy, cần "đăng ký" (registration) để khớp góc nhìn của chúng lại với nhau.

### **Depth Registration (Đăng ký chiều sâu)**
Quá trình xử lý toán học để **"uốn" ảnh Depth khớp chính xác với góc nhìn (FoV) của ảnh RGB**, sao cho mỗi điểm ảnh Depth tương ứng đúng vị trí với điểm ảnh màu cùng tọa độ — điều kiện bắt buộc để tạo ra "đám mây điểm có màu" (Colored Point Cloud).

### **HAL (Hardware Abstraction Layer — Lớp trừu tượng hóa phần cứng)**
Một lớp phần mềm trung gian giúp **che giấu sự phức tạp/khác biệt của phần cứng thực tế**, cung cấp cho lập trình viên một giao diện lập trình (API) đơn giản, thống nhất, không cần quan tâm chi tiết phần cứng bên dưới hoạt động ra sao. OpenNI2 đóng vai trò HAL cho các camera Depth Structured Light.
