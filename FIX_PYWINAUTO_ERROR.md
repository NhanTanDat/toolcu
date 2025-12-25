# 🔧 Fix Lỗi: "No module named 'pywinauto'"

## ❌ Lỗi Gặp Phải

```
ERROR: Cannot import modules (core.downloadTool.*): No module named 'pywinauto'
```

## ✅ Giải Pháp (Đã Fix!)

### Bước 1: Pull Code Mới

```bash
git pull origin claude/fix-genmini-autodownload-rG8yt
```

### Bước 2: Chọn Mode Cài Đặt

#### Option A: **Chỉ Dùng Gemini API** (Khuyến nghị - nhanh gọn)

Nếu bạn chỉ cần tìm link video/ảnh với Gemini API:

```bash
pip install google-generativeai python-dotenv yt-dlp
```

**Ưu điểm:**
- ✅ Nhanh - không cần cài nhiều dependencies
- ✅ Không cần pywinauto/pywin32
- ✅ Vẫn có đầy đủ tính năng tìm link
- ✅ Dùng được trên Linux/Mac

**Hạn chế:**
- ❌ Không tự động hoá Premiere Pro

#### Option B: **Cài Đặt Đầy Đủ** (Cho automation Premiere)

Nếu bạn cần automation Premiere Pro:

```bash
pip install -r requirements.txt
```

**Lưu ý:** Nếu gặp lỗi với `pywin32==311`, chạy:
```bash
pip install pywin32 pywinauto --upgrade
```

### Bước 3: Setup API Key

```bash
# Tạo file .env
GEMINI_API_KEY=your_api_key_here
```

Lấy API key miễn phí: https://makersuite.google.com/app/apikey

### Bước 4: Chạy Tool

```bash
python GUI/mainGUI.py
```

## 🎯 Chi Tiết Fix

Code đã được sửa để làm `pywinauto` trở thành **optional**:

**Trước:**
```python
from pywinauto import Application  # ❌ Crash nếu không có
```

**Sau:**
```python
try:
    from pywinauto import Application
    _HAS_PYWINAUTO = True
except ImportError:
    _HAS_PYWINAUTO = False
    Application = None  # ✅ Không crash, chỉ disable automation features
```

**File đã fix:**
- ✅ `core/downloadTool/get_link.py`
- ✅ `core/downloadTool/down_by_yt.py`
- ✅ `core/downloadTool/init_sub_app.py`
- ✅ `core/premierCore/control.py`

## 📋 Tóm Tắt

| Mode | Dependencies | Use Case |
|------|--------------|----------|
| **Gemini Only** | Minimal (3 packages) | Chỉ tìm link video/ảnh |
| **Full Automation** | All (75 packages) | Automation Premiere Pro |

**Khuyến nghị:** Dùng **Gemini Only** mode nếu không cần automation Premiere!

---

Commit: `1dc5b63` - fix: Make pywinauto imports optional to support Gemini-only mode
