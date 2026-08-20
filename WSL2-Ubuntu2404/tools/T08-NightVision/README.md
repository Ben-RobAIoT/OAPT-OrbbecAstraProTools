Dưới đây là nội dung file **README.md** hoàn chỉnh, bạn có thể copy thẳng vào repo. Mình đã giữ bố cục gọn, tập trung vào ý tưởng – nguyên lý – mô hình toán học – cú pháp, không lan man.

# 🌙 IR Night Vision Human Detection System

Hệ thống phát hiện người trong bóng tối bằng ảnh **hồng ngoại (IR)** kết hợp **AI (YOLOv8)** và **cảm biến độ sâu (Depth)** từ camera Orbbec Astra Pro, chạy trên WSL2.

## 1. Ý tưởng chương trình

Camera RGB thường không nhìn thấy gì trong bóng tối, nhưng cảm biến **IR** và **Depth** (dựa trên chiếu tia hồng ngoại structured-light) vẫn hoạt động bình thường vì không phụ thuộc ánh sáng khả kiến. Ý tưởng cốt lõi:

1. Không dùng luồng RGB (tắt hẳn để tiết kiệm băng thông USB) [1].
2. Lấy ảnh **IR 16-bit**, "đánh lừa" mô hình YOLO (vốn được huấn luyện trên ảnh màu 3 kênh) bằng cách nhân bản kênh xám thành ảnh giả RGB [1].
3. Chạy YOLOv8 để phát hiện người trên ảnh IR đó.
4. Lấy tọa độ tâm bounding box, tra ngược sang **Depth map** để biết khoảng cách thực (mm).
5. Áp luật cảnh báo an toàn theo khoảng cách.

## 2. Pipeline xử lý

```
Depth Stream ─┐
              ├─► đọc frame → reshape → Depth Map (hiển thị JET colormap)
IR Stream ────┘
      │
      ▼
convertScaleAbs (16bit→8bit) → GRAY2BGR (giả RGB)
      │
      ▼
YOLOv8n.predict(classes=[0]=person)
      │
      ▼
Tính tâm bbox (cx, cy) → tra Depth[cy, cx] = Z (mm)
      │
      ▼
So sánh ngưỡng Z → vẽ cảnh báo (an toàn / nguy hiểm)
```

## 3. Công nghệ sử dụng & lý do chọn

| Công nghệ | Vai trò | Lý do dùng |
|---|---|---|
| **OpenNI2** (`openni2`) | Đọc luồng Depth + IR từ Orbbec Astra Pro | Astra Pro dùng chuẩn OpenNI, SDK chính thức để truy xuất raw sensor stream |
| **OpenCV (cv2)** | Xử lý ảnh, hiển thị, colormap | Thư viện chuẩn, tốc độ tốt trên CPU, hỗ trợ convertScaleAbs, applyColorMap |
| **NumPy** | Chuyển buffer thô thành ma trận ảnh | Dữ liệu OpenNI trả về dạng buffer byte, cần `frombuffer` + `reshape` để thao tác ma trận nhanh |
| **YOLOv8n (Ultralytics)** | Phát hiện người (class 0) | Bản "nano" nhẹ, chạy được real-time trên CPU, đủ chính xác cho demo |
| **Biến môi trường WSL2 shield** | Tắt GPU/OpenCL, ép số luồng CPU = 1 | WSL2 không có driver GPU đầy đủ → dễ crash nếu OpenCV/PyTorch cố dùng OpenCL/đa luồng BLAS xung đột [1] |

## 4. Nguyên lý kỹ thuật chi tiết

### 4.1. Vì sao đánh lừa được YOLO bằng ảnh IR?
YOLOv8 chỉ yêu cầu input là tensor 3 kênh đúng kích thước, nó không "biết" đó là RGB hay IR. Ảnh IR grayscale được nhân bản thành 3 kênh giống hệt nhau:

```python
ir_fake_rgb = cv2.cvtColor(ir_8bit, cv2.COLOR_GRAY2BGR)
```
[1]

Về mặt hình học, người vẫn có biên dạng (contour) tương phản rõ trong ảnh IR (nhờ phản xạ hồng ngoại khác giữa da/quần áo và nền), nên mô hình học đặc trưng biên dạng/texture của YOLO vẫn nhận diện được, dù độ chính xác thấp hơn ảnh RGB gốc.

### 4.2. Mô hình toán học chuyển đổi 16-bit → 8-bit

Ảnh IR gốc là **16-bit** (giá trị cường độ cao, thường tối vì camera IR nhạy sáng thấp). OpenCV dùng công thức tuyến tính:

```
dst(x,y) = saturate_uint8( | src(x,y) × alpha + beta | )
```

Trong code: `alpha = 0.1`, `beta = 0` [1]:

```python
ir_8bit = cv2.convertScaleAbs(ir_image, alpha=0.1)
```

Đây là một phép **scale tuyến tính + clip (saturation)** về khoảng [0, 255], giúp ảnh 16-bit tối trở nên "sáng" và hiển thị/predict được.

Tương tự với Depth map, dùng `alpha=0.03` để nén dải giá trị mm (thường 0–8000mm) về 0–255 nhằm áp `COLORMAP_JET` trực quan hóa [1].

### 4.3. Tính tâm bounding box và tra cứu độ sâu

Sau khi YOLO trả về `box.xyxy = (x1, y1, x2, y2)`, tâm được tính bằng trung bình cộng tọa độ (phép chiếu tâm hình chữ nhật):

```
cx = (x1 + x2) / 2
cy = (y1 + y2) / 2
```
[1]

Vì Depth stream và IR stream **cùng độ phân giải và đã được camera align phần cứng**, tọa độ pixel (cx, cy) trên ảnh IR tương ứng trực tiếp với ma trận Depth:

```
Z(mm) = DepthMap[cy, cx]
```
[1]

Đây chính là bước "fusion" 2D detection (YOLO) với thông tin 3D (Depth) mà không cần tính lại phép chiếu camera (vì OpenNI đã đồng bộ hệ tọa độ).

### 4.4. Hàm phân loại cảnh báo (piecewise function)

```
f(Z) = "NGUY HIEM" nếu 0 < Z < 1000 mm
     = "AN TOAN"   nếu Z ≥ 1000 mm
```
[1]

Ngưỡng `Z=0` bị loại (điều kiện `z_mm > 0`) vì cảm biến ToF/structured-light trả về 0 khi không đo được (vùng bóng, quá gần/xa dải đo) — đây là non-value chứ không phải khoảng cách thật.

## 5. Cú pháp Python đáng chú ý & lý do dùng

| Cú pháp | Ý nghĩa | Vì sao chọn |
|---|---|---|
| `os.environ[...] = '1'` trước khi `import cv2` | Ép cấu hình runtime trước khi thư viện native load | Một số flag OpenCV/OpenBLAS chỉ đọc biến môi trường **lúc import**, phải set trước |
| `np.frombuffer(...).copy()` | Ép buffer C thành mảng NumPy, `.copy()` tránh buffer bị ghi đè bởi frame sau | An toàn bộ nhớ khi vòng lặp đọc frame liên tục |
| `.reshape(height, width)` | Chuyển mảng 1D thành ma trận ảnh 2D | Dữ liệu stream trả về dạng phẳng (flat) |
| `try/except/finally` | Đảm bảo giải phóng thiết bị (`dev.close()`, `openni2.unload()`) dù có lỗi hay `Ctrl+C` | Camera phần cứng cần release đúng cách, tránh treo cổng USB |
| `for r in results: for box in r.boxes` | Duyệt kết quả YOLO (mỗi ảnh có nhiều box) | Theo API chuẩn của Ultralytics trả về list `Results` |
| f-string (`f"Z: {z_mm} mm"`) | Format text hiển thị | Ngắn gọn, dễ đọc hơn `.format()` |
| `classes=[0], conf=0.4` trong `model.predict` | Lọc chỉ class "person" (index 0 trong COCO), ngưỡng tin cậy 40% | Giảm nhiễu, tăng tốc vì chỉ cần phát hiện người |

## 6. Hạn chế & hướng phát triển
- Độ chính xác YOLO trên ảnh IR thấp hơn RGB vì model không được huấn luyện riêng cho domain IR → có thể fine-tune thêm.
- `alpha` cố định (0.1 / 0.03) chưa thích nghi theo điều kiện sáng thực tế → có thể dùng auto-contrast (CLAHE, min-max normalize).
- Chạy CPU (`device='cpu'`) nên tốc độ giới hạn — có thể tối ưu bằng ONNX/TensorRT nếu triển khai trên Jetson/Pi có NPU.
```

Vài lưu ý khi bạn đăng lên GitHub:
- Có thể thêm ảnh screenshot demo (IR + Depth window) vào phần đầu README để trực quan hơn.
- Nếu muốn, mình có thể viết thêm phần "Cách chạy" (requirements.txt, hướng dẫn cài OpenNI2 SDK) — hiện code có hardcode đường dẫn SDK theo máy cá nhân [1], bạn nên đổi thành biến môi trường hoặc argparse trước khi public để người khác dùng được.

This response was generated by Apollo AI, an internal AI assistant. Please validate important outputs against official Apollo documents, systems, and responsible teams before acting on them.
