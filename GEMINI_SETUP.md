# Hướng dẫn sử dụng Gemini API cho Auto Download

## Giới thiệu

Tool đã được nâng cấp để sử dụng **Gemini API** thay vì Selenium scraping. Điều này mang lại nhiều lợi ích:

✅ **Chạy hoàn toàn trong terminal** - không cần mở Chrome browser
✅ **Nhanh hơn** - sử dụng API trực tiếp thay vì scraping
✅ **Ổn định hơn** - không bị ảnh hưởng bởi thay đổi HTML của YouTube/Google
✅ **Thông minh hơn** - Gemini AI tối ưu search queries để tìm kết quả chính xác hơn
✅ **Lọc chính xác** - Sử dụng YouTube Data API để filter theo thời lượng video

---

## Cài đặt

### 1. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 2. Lấy API Keys

#### **Gemini API Key** (Bắt buộc)

1. Truy cập: https://makersuite.google.com/app/apikey
2. Đăng nhập bằng Google account
3. Click "Create API Key"
4. Copy API key

#### **YouTube Data API v3** (Tùy chọn - khuyến nghị)

1. Truy cập: https://console.cloud.google.com/
2. Tạo project mới hoặc chọn project hiện có
3. Enable "YouTube Data API v3":
   - Vào "APIs & Services" > "Enable APIs and Services"
   - Tìm "YouTube Data API v3" và enable
4. Tạo credentials:
   - Vào "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "API Key"
   - Copy API key

> **Lưu ý**: Nếu không có YouTube API key, tool sẽ tự động dùng fallback method với thư viện `youtubesearchpython`

#### **Google Custom Search API** (Tùy chọn - cho image search)

1. Truy cập: https://console.cloud.google.com/
2. Enable "Custom Search API"
3. Tạo API key tương tự YouTube API
4. Tạo Search Engine:
   - Truy cập: https://programmablesearchengine.google.com/
   - Click "Add" để tạo search engine mới
   - Cấu hình "Search entire web"
   - Copy Search Engine ID

### 3. Cấu hình .env file

Copy file `.env.example` thành `.env` và điền API keys:

```bash
cp .env.example .env
```

Sửa file `.env`:

```bash
# Gemini API (BẮT BUỘC)
GEMINI_API_KEY=AIzaSy...your_gemini_key_here

# YouTube Data API v3 (Tùy chọn - khuyến nghị)
YOUTUBE_API_KEY=AIzaSy...your_youtube_key_here

# Google Custom Search API (Tùy chọn)
GOOGLE_SEARCH_API_KEY=AIzaSy...your_search_key_here
GOOGLE_SEARCH_ENGINE_ID=your_engine_id_here
```

---

## Sử dụng

### Chế độ tự động

Tool sẽ **tự động phát hiện** nếu có `GEMINI_API_KEY` trong file `.env` và chuyển sang Gemini mode:

```python
from core.downloadTool import get_link

# Nếu có GEMINI_API_KEY -> dùng Gemini API
# Nếu không có -> dùng Selenium (cách cũ)
get_link.get_links_main_video(
    keywords_file='data/list_name.txt',
    output_txt='data/dl_links.txt',
    max_per_keyword=5,
    max_minutes=20,
    min_minutes=4
)
```

### Test trong terminal

Chạy script test để kiểm tra:

```bash
python test_gemini_search.py
```

Script này sẽ:
- Kiểm tra API keys
- Test query optimization với Gemini
- Test video search
- Test full workflow với file keywords

### Sử dụng trực tiếp Gemini module

```python
from core.downloadTool import get_link_gemini

# Search YouTube videos
videos = get_link_gemini.get_youtube_videos_with_api(
    keyword="python tutorial",
    max_results=10,
    max_minutes=20,
    min_minutes=4
)

# Search Google Images
images = get_link_gemini.get_image_links_with_gemini(
    keyword="beautiful landscape",
    num_images=10
)

# Optimize search query
optimized = get_link_gemini.optimize_search_query_with_gemini(
    keyword="cat",
    search_type='video'
)
```

---

## So sánh Selenium vs Gemini Mode

| Tính năng | Selenium Mode (Cũ) | Gemini Mode (Mới) |
|-----------|-------------------|-------------------|
| Browser | Cần Chrome | Không cần |
| Tốc độ | Chậm (scraping) | Nhanh (API) |
| Ổn định | Dễ bị lỗi khi HTML thay đổi | Ổn định |
| Query optimization | Không | Có (Gemini AI) |
| Duration filter | Approximate | Chính xác (API) |
| Rate limiting | Dễ bị block | Có quota API |
| Image search | Google Images scraping | Gemini Search + API |

---

## Troubleshooting

### Lỗi: "No GEMINI_API_KEY found"

**Nguyên nhân**: Không tìm thấy API key trong file `.env`

**Giải pháp**:
1. Kiểm tra file `.env` có tồn tại không
2. Kiểm tra đã điền `GEMINI_API_KEY` chưa
3. Restart terminal/IDE sau khi sửa `.env`

### Lỗi: "YouTube API quota exceeded"

**Nguyên nhân**: Vượt quá quota miễn phí của YouTube API (10,000 units/day)

**Giải pháp**:
- Tool sẽ tự động fallback sang `youtubesearchpython`
- Hoặc đợi 24h để quota reset
- Hoặc nâng cấp quota trong Google Cloud Console

### Lỗi: "Gemini API rate limit"

**Nguyên nhân**: Gọi API quá nhanh

**Giải pháp**:
- Tool đã có `sleep(0.5)` giữa các request
- Nếu vẫn lỗi, tăng delay trong code

### Video/Image không tìm thấy

**Nguyên nhân**:
- Keyword quá chung hoặc quá specific
- Filter quá strict (min/max duration)

**Giải pháp**:
- Thử keyword khác
- Giảm filter duration
- Kiểm tra logs để debug

---

## Ví dụ output

### Video search với Gemini

```
[get_link_gemini] === START get_links_main_video ===
[get_link_gemini] Loaded 2 unique keywords
[get_link_gemini] --- (1/2) 'python tutorial' ---
[get_link_gemini] Optimized 'python tutorial' -> 'python programming tutorial for beginners'
[get_link_gemini] Found 5 videos for 'python tutorial' (filtered by duration)
[get_link_gemini] --- (2/2) 'machine learning' ---
[get_link_gemini] Optimized 'machine learning' -> 'machine learning tutorial complete course'
[get_link_gemini] Found 5 videos for 'machine learning' (filtered by duration)
[get_link_gemini] TOTAL video links written: 10
```

### Keywords file format

**Input** (`data/list_name.txt`):
```
1 python tutorial
2 machine learning
3 web development
```

**Output Video** (`data/dl_links.txt`):
```
1 python tutorial
https://www.youtube.com/watch?v=abc123
https://www.youtube.com/watch?v=def456
2 machine learning
https://www.youtube.com/watch?v=ghi789
https://www.youtube.com/watch?v=jkl012
```

**Output Image** (`data/dl_links_image.txt`):
```
1 python tutorial
https://example.com/image1.jpg
https://example.com/image2.png
2 machine learning
https://example.com/image3.jpg
https://example.com/image4.png
```

---

## API Quotas & Pricing

### Gemini API
- **Free tier**: 60 requests/minute
- **Cost**: Free trong preview phase
- Docs: https://ai.google.dev/pricing

### YouTube Data API v3
- **Free tier**: 10,000 units/day
- **Cost per search**: ~100 units
- Quota: ~100 searches/day free
- Docs: https://developers.google.com/youtube/v3/getting-started#quota

### Google Custom Search API
- **Free tier**: 100 searches/day
- **Cost**: $5 per 1000 queries sau 100 searches
- Docs: https://developers.google.com/custom-search/v1/overview

---

## Liên hệ & Support

Nếu gặp vấn đề:
1. Kiểm tra logs trong terminal
2. Chạy `python test_gemini_search.py` để debug
3. Kiểm tra API keys còn valid không
4. Kiểm tra quota API

---

## Changelog

### Version 2.0 - Gemini Integration
- ✅ Thêm hỗ trợ Gemini API
- ✅ Auto-detect API key và switch mode
- ✅ YouTube Data API v3 integration
- ✅ Query optimization với Gemini AI
- ✅ Fallback methods cho mỗi API
- ✅ Terminal-only mode (no browser needed)
- ✅ Test suite đầy đủ

### Version 1.0 - Selenium Mode
- Selenium scraping cho YouTube & Google Images
- Duration filtering
- Multi-keyword support
