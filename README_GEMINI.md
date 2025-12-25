# 🚀 Auto Download với Gemini API - Siêu Đơn Giản!

## ✨ CHỈ CẦN 1 API KEY DUY NHẤT!

Không cần YouTube API, không cần Google Custom Search API, không cần Selenium!
**CHỈ CẦN GEMINI API KEY** - miễn phí và dễ lấy trong 2 phút!

---

## 📦 Cài đặt nhanh

### Bước 1: Cài dependencies

```bash
pip install -r requirements.txt
```

### Bước 2: Lấy Gemini API Key (MIỄN PHÍ)

1. **Truy cập**: https://makersuite.google.com/app/apikey
2. **Đăng nhập** Google account
3. **Click** "Create API Key"
4. **Copy** API key

⏱️ Mất 2 phút!

### Bước 3: Cấu hình

Copy file `.env.example` thành `.env`:

```bash
cp .env.example .env
```

Mở file `.env` và điền API key:

```bash
GEMINI_API_KEY=AIzaSy...paste_your_key_here
```

### Bước 4: Xong! Bắt đầu dùng 🎉

Tool sẽ **tự động** dùng Gemini API khi phát hiện có key trong `.env`

---

## 🎯 Sử dụng

### Cách 1: Dùng GUI (như cũ)

Mở GUI và dùng bình thường:

```bash
python GUI/mainGUI.py
```

Tool sẽ **tự động chuyển sang Gemini mode** - không cần setup gì thêm!

### Cách 2: Test trong terminal

```bash
python test_gemini_search.py
```

### Cách 3: Dùng trực tiếp trong code

```python
from core.downloadTool import get_link

# Tự động dùng Gemini nếu có API key trong .env
get_link.get_links_main_video(
    keywords_file='data/list_name.txt',
    output_txt='data/dl_links.txt',
    max_per_keyword=5,
    max_minutes=20,
    min_minutes=4
)
```

---

## 🔥 Tính năng

✅ **CHỈ 1 API KEY** - Gemini làm tất cả!
✅ **Miễn phí** - Gemini API free tier rất hào phóng (60 requests/phút)
✅ **Terminal-only** - Không cần Chrome browser
✅ **Nhanh hơn Selenium** - Direct API thay vì scraping
✅ **Thông minh** - Gemini AI tìm videos/images relevant nhất
✅ **Ổn định** - Không bị lỗi khi YouTube/Google thay đổi HTML
✅ **Auto-detect** - Tự động chuyển mode khi có API key

---

## 📝 Ví dụ Output

### Input: `data/list_name.txt`
```
1 python tutorial
2 beautiful sunset
```

### Chạy tool:

```bash
python test_gemini_search.py
```

### Output Videos: `data/dl_links.txt`
```
1 python tutorial
https://www.youtube.com/watch?v=abc123
https://www.youtube.com/watch?v=def456
2 beautiful sunset
https://www.youtube.com/watch?v=ghi789
https://www.youtube.com/watch?v=jkl012
```

### Output Images: `data/dl_links_image.txt`
```
1 python tutorial
https://example.com/python1.jpg
https://example.com/python2.png
2 beautiful sunset
https://example.com/sunset1.jpg
https://example.com/sunset2.jpg
```

---

## 💡 Cách hoạt động

1. **Gemini với Google Search Grounding** - Gemini tìm kiếm trên web real-time
2. **YouTube Videos** - Gemini search YouTube và trả về video links
3. **Google Images** - Gemini search Google Images và trả về image links
4. **Filter thông minh** - Lọc theo thời lượng video (min/max minutes)
5. **No browser needed** - Chạy hoàn toàn trong terminal

---

## ❓ FAQ

### Q: Tôi có cần YouTube API không?
**A: KHÔNG!** Chỉ cần Gemini API key duy nhất.

### Q: Gemini API có miễn phí không?
**A: CÓ!** Free tier: 60 requests/phút - đủ xài!

### Q: Có cần Google Custom Search API không?
**A: KHÔNG!** Gemini làm tất cả.

### Q: Tool cũ (Selenium) có còn hoạt động không?
**A: CÓ!** Nếu không có Gemini API key, tool tự động dùng Selenium mode (cách cũ).

### Q: Tôi phải làm gì nếu hết quota API?
**A: Đợi 1 phút!** Gemini free tier reset mỗi phút. Hoặc tạm thời comment out `GEMINI_API_KEY` trong `.env` để dùng Selenium mode.

### Q: Cách biết đang dùng Gemini mode hay Selenium mode?
**A:** Khi chạy, xem log:
- Gemini mode: `[get_link] GEMINI API DETECTED - Will use Gemini-powered search`
- Selenium mode: `[get_link] Gemini API not available, using Selenium mode`

---

## 🐛 Troubleshooting

### Lỗi: "No GEMINI_API_KEY found"

```
[get_link_gemini] ERROR: GEMINI_API_KEY not found in .env!
```

**Giải pháp:**
1. Kiểm tra file `.env` có tồn tại không
2. Kiểm tra đã điền `GEMINI_API_KEY=...` chưa
3. Restart terminal/IDE

### Lỗi: "Rate limit exceeded"

```
ERROR: Gemini API rate limit
```

**Giải pháp:**
- Đợi 1 phút (free tier = 60 requests/phút)
- Hoặc comment out `GEMINI_API_KEY` để dùng Selenium mode tạm thời

### Không tìm thấy video/image

**Nguyên nhân:**
- Keyword quá chung hoặc quá specific
- Gemini không tìm thấy kết quả phù hợp

**Giải pháp:**
- Thử keyword khác
- Kiểm tra logs để debug

---

## 📊 So sánh: Selenium vs Gemini

| Tính năng | Selenium (Cũ) | Gemini (Mới) |
|-----------|--------------|--------------|
| **API Keys** | 0 | 1 (chỉ Gemini) |
| **Browser** | Cần Chrome | KHÔNG cần |
| **Tốc độ** | Chậm | Nhanh |
| **Ổn định** | Dễ lỗi | Rất ổn định |
| **Setup** | Phức tạp | Siêu đơn giản |
| **Cost** | Free | Free (60 req/min) |
| **Smart search** | Không | Có (AI) |

---

## 🎁 Bonus: Test Script

File `test_gemini_search.py` giúp bạn test ngay:

```bash
python test_gemini_search.py
```

Output:
```
============================================================
GEMINI API SEARCH - TEST SUITE
============================================================

GEMINI_API_KEY: ✓ Found

============================================================
TEST: Query Optimization
============================================================
...

============================================================
TEST SUMMARY
============================================================
  ✓ PASSED: Query Optimization
  ✓ PASSED: Video Search
  ✓ PASSED: Full Workflow

Total: 3/3 tests passed
```

---

## 📞 Hỗ trợ

Nếu gặp vấn đề:
1. Kiểm tra API key còn valid không
2. Chạy `python test_gemini_search.py` để debug
3. Xem logs trong terminal
4. Check quota: https://makersuite.google.com/app/apikey

---

## 🎉 Kết luận

**Tool autodownload bây giờ siêu đơn giản:**

1. ✅ Lấy 1 Gemini API key (2 phút)
2. ✅ Paste vào `.env`
3. ✅ Xong! Bắt đầu dùng

Không cần YouTube API, không cần Google API, không cần Chrome, không cần setup phức tạp!

**CHỈ 1 API KEY DUY NHẤT = GEMINI** 🚀

---

Made with ❤️ using Gemini 2.0 Flash
