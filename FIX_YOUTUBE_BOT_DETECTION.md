# 🍪 Hướng Dẫn Fix YouTube Bot Detection

## ❌ Lỗi Gặp Phải

```
ERROR: Sign in to confirm you're not a bot
```

YouTube đã bật biện pháp chống bot mạnh hơn, yêu cầu cookies từ browser để chứng minh bạn không phải bot.

## ✅ GIẢI PHÁP: Export YouTube Cookies

### Phương Pháp 1: Dùng Browser Extension (DỄ NHẤT)

#### Bước 1: Cài Extension

**Chrome/Edge:**
- Vào: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
- Click "Add to Chrome"

**Firefox:**
- Vào: https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/
- Click "Add to Firefox"

#### Bước 2: Export Cookies

1. Mở YouTube trong browser: https://www.youtube.com
2. **Đăng nhập** tài khoản YouTube (quan trọng!)
3. Click vào extension icon (biểu tượng cookie)
4. Click **"Export"** hoặc **"Get cookies.txt"**
5. Lưu file với tên: `youtube_cookies.txt`

#### Bước 3: Đặt File Cookies

**Copy file vào folder tool (TỰ ĐỘNG TÌM):**

Tool sẽ **TỰ ĐỘNG** tìm file `youtube_cookies.txt` ở các vị trí sau:
1. ✅ Folder chứa file .exe: `autotool_win64\youtube_cookies.txt`
2. ✅ Thư mục gốc project: `D:\your-project-folder\youtube_cookies.txt`
3. ✅ Thư mục hiện tại khi chạy tool

**Không cần set biến môi trường!** Chỉ cần đặt file vào một trong những vị trí trên.

### Phương Pháp 2: Dùng yt-dlp Built-in (TỰ ĐỘNG)

**Không cần export file, yt-dlp tự lấy cookies từ browser!**

#### Bước 1: Cài Extension Browser

**Chrome/Edge:**
```bash
pip install yt-dlp[default]
```

**Firefox:**
```bash
pip install yt-dlp[default]
```

#### Bước 2: Đăng Nhập YouTube

1. Mở Chrome/Firefox
2. Đăng nhập YouTube: https://www.youtube.com
3. Đóng browser

#### Bước 3: Tool Sẽ Tự Động Dùng Cookies

Tool đã được config để tự động lấy cookies từ Chrome!

---

## 🔧 Cấu Hình Cho Tool

### Option A: Dùng File Cookies (youtube_cookies.txt)

**CÁCH DỄ NHẤT - TỰ ĐỘNG TÌM FILE:**

1. **Đặt file `youtube_cookies.txt` vào folder tool:**
   - Cùng folder với `autotool.exe`
   - Hoặc thư mục gốc project (nếu chạy Python)

2. **Chạy tool** - Tool sẽ tự động tìm và sử dụng file!

**KHÔNG CẦN** set biến môi trường nữa!

### Option B: Dùng Browser Cookies (Tự động)

Tool đã được config để **TỰ ĐỘNG** lấy cookies từ Chrome.

**Chỉ cần:**
1. Đăng nhập YouTube trong Chrome
2. Chạy tool

**Không cần làm gì thêm!**

---

## ⚙️ Technical Details (Đã Config Trong Code)

File `down_by_yt.py` đã được config:

```python
# Auto-detect cookies
if os.path.isfile(COOKIES_FILE):
    ydl_opts["cookiefile"] = COOKIES_FILE
    print(f"[down_by_yt] Using cookies from: {COOKIES_FILE}")
else:
    # Fallback: Use Chrome cookies automatically
    ydl_opts["cookiesfro mbrowser"] = ("chrome", )
    print("[down_by_yt] Using cookies from Chrome browser")
```

---

## 📊 Kết Quả Mong Đợi

**Trước (không cookies):**
```
ERROR: Sign in to confirm you're not a bot
Videos downloaded: 0/38 ❌
```

**Sau (có cookies):**
```
[youtube] Downloading webpage
[download] Destination: video.mp4
[download] 100% of 15.3MiB in 00:05
Videos downloaded: 38/38 ✅
```

---

## ⚠️ Lưu Ý Quan Trọng

### 1. Cookies Hết Hạn

Cookies YouTube thường **hết hạn sau 1-2 tuần**. Nếu gặp lỗi bot detection trở lại:

1. Export cookies mới
2. Hoặc đăng nhập lại YouTube trong Chrome
3. Chạy lại tool

### 2. Bảo Mật

**QUAN TRỌNG:** File `youtube_cookies.txt` chứa session login của bạn!

- ❌ **ĐỪNG CHIA SẺ** file này với ai
- ❌ **ĐỪNG COMMIT** vào Git
- ✅ Thêm vào `.gitignore`:
  ```
  youtube_cookies.txt
  *.txt
  ```

### 3. Multiple Accounts

Nếu có nhiều tài khoản YouTube:
- Đăng nhập tài khoản muốn dùng
- Export cookies từ tài khoản đó
- Tool sẽ download như tài khoản đó

---

## 🔍 Debug

### Kiểm Tra Cookies Hoạt Động

```bash
yt-dlp --cookies youtube_cookies.txt "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

Nếu download được → Cookies OK ✅

### Kiểm Tra Chrome Cookies

```bash
yt-dlp --cookies-from-browser chrome "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

Nếu download được → Chrome cookies OK ✅

---

## 🚀 Quick Start

**Cách nhanh nhất (30 giây):**

1. Đăng nhập YouTube trong Chrome
2. Chạy tool (tool tự động dùng Chrome cookies)
3. Done! ✅

**Nếu vẫn lỗi:**
1. Cài extension cookies.txt
2. Export cookies
3. Đặt file `youtube_cookies.txt` vào folder tool
4. Chạy lại

---

Made with ❤️ to bypass YouTube bot detection
