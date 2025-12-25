# 🪟 Hướng Dẫn Cài Đặt Trên Windows

## 📦 Cài Đặt Dependencies

### Option 1: Chỉ Dùng Gemini API (Không Automation Premiere)

Nếu bạn chỉ muốn dùng tính năng tìm link với Gemini API (không cần automation Premiere Pro):

```bash
pip install google-generativeai python-dotenv yt-dlp
```

**Lưu ý:** Với option này, bạn sẽ KHÔNG thể dùng tính năng tự động hoá Premiere Pro.

### Option 2: Cài Đặt Đầy Đủ (Có Automation Premiere)

Để sử dụng đầy đủ tính năng automation Premiere Pro:

```bash
pip install -r requirements.txt
```

**Lưu ý trên Windows:**
- `pywin32` và `pywinauto` là bắt buộc cho automation Premiere Pro
- Nếu gặp lỗi cài `pywin32==311`, thử:
  ```bash
  pip install pywin32 pywinauto --upgrade
  ```

## 🔑 Setup Gemini API Key

```bash
# 1. Tạo file .env
copy .env.example .env

# 2. Edit .env và thêm API key
GEMINI_API_KEY=your_gemini_api_key_here
```

Lấy API key miễn phí tại: https://makersuite.google.com/app/apikey

## 🚀 Chạy Tool

```bash
python GUI/mainGUI.py
```

## ⚠️ Troubleshooting

### Lỗi: "No module named 'pywinauto'"

**Nguyên nhân:** Thiếu dependency cho automation Premiere.

**Giải pháp:**
1. Cài đặt đầy đủ dependencies:
   ```bash
   pip install pywin32 pywinauto
   ```

2. Hoặc chỉ dùng Gemini mode (không automation):
   ```bash
   pip install google-generativeai python-dotenv yt-dlp
   ```

### Lỗi: "Cannot install pywin32==311"

**Giải pháp:**
```bash
pip install pywin32 --upgrade
```

### Tool Không Tìm Được Video/Ảnh

**Kiểm tra:**
1. `.env` có chứa `GEMINI_API_KEY` chưa?
2. Đã cài `yt-dlp` chưa? → `pip install yt-dlp`
3. Check log trong GUI để xem lỗi cụ thể

## 📊 Dependencies Chi Tiết

### Core (Gemini Mode Only)
- `google-generativeai` - Gemini API
- `python-dotenv` - Load .env file
- `yt-dlp` - Fast YouTube search + thumbnails

### Full (Automation Mode)
- All Core dependencies +
- `pywin32` - Windows automation
- `pywinauto` - UI automation
- `selenium` - Web scraping fallback
- `pyperclip` - Clipboard operations

---

Made with ❤️ for Windows users
