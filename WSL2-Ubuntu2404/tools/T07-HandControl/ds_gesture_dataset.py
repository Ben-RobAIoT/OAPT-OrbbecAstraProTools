# gesture_dataset.py

# Cấu trúc: [Ngón cái, Ngón trỏ, Ngón giữa, Ngón áp út, Ngón út]
# 1 = Mở, 0 = Gập, -1 = Bỏ qua (Không quan tâm)

ROBOT_GESTURES = {
    "TIEN LEN (Go)": {
        "left":  [-1, -1, -1, -1, -1], # Tay trái để sao cũng được
        "right": [ 0,  1,  0,  0,  0], # Tay phải chỉ ngón trỏ
        "color": (0, 255, 0)
    },
    "LUI LAI (Back)": {
        "left":  [ 1,  1,  1,  1,  1], # Cả 2 tay xòe 5 ngón (Đẩy ra)
        "right": [ 1,  1,  1,  1,  1],
        "color": (0, 0, 255)
    },
    "NGOI XUONG (Sit)": {
        "left":  [ 0,  0,  0,  0,  0], # Cả 2 tay nắm chặt thành nắm đấm
        "right": [ 0,  0,  0,  0,  0],
        "color": (0, 165, 255)
    },
    "DUNG LEN (Stand)": {
        "left":  [ 1,  0,  0,  0,  0], # 2 tay giơ ngón cái (Like)
        "right": [ 1,  0,  0,  0,  0],
        "color": (255, 255, 0)
    },
    "RE TRAI (Turn Left)": {
        "left":  [ 1,  1,  1,  1,  1], # Trái xòe, Phải nắm
        "right": [ 0,  0,  0,  0,  0],
        "color": (255, 100, 100)
    },
    "RE PHAI (Turn Right)": {
        "left":  [ 0,  0,  0,  0,  0], # Trái nắm, Phải xòe
        "right": [ 1,  1,  1,  1,  1],
        "color": (100, 100, 255)
    },
    "MUA BALE (Dance)": {
        "left":  [ 1,  0,  0,  0,  1], # 2 tay làm dấu Shaka (Chữ Y)
        "right": [ 1,  0,  0,  0,  1],
        "color": (255, 0, 255)
    },
    "BAN SUNG (Shoot)": {
        "left":  [-1, -1, -1, -1, -1],
        "right": [ 1,  1,  0,  0,  0], # Tay phải ngón cái + trỏ (Súng L)
        "color": (0, 0, 0)
    },
    "TANG TOC (Dash)": {
        "left":  [ 0,  1,  1,  0,  0], # 2 tay giơ chữ V (Peace)
        "right": [ 0,  1,  1,  0,  0],
        "color": (0, 255, 255)
    },
    "XIN CHAO (Hello)": {
        "left":  [-1, -1, -1, -1, -1], 
        "right": [ 1,  1,  1,  1,  1], # Tay phải xòe
        "color": (255, 255, 255)
    }
}