"""YouTube/Google Images link gathering using ONLY Gemini API.

Tính năng:
 - CHỈ CẦN 1 GEMINI API KEY DUY NHẤT - không cần YouTube API hay Google Custom Search API
 - Sử dụng Gemini với Google Search grounding để tìm video và image links
 - Không cần Selenium - chạy hoàn toàn trong terminal
 - Logging rõ ràng, bắt lỗi từng keyword
 - Giới hạn số video/ảnh mỗi keyword
 - Lọc theo thời lượng video (min/max minutes)
 - Đơn giản, dễ setup, chỉ cần 1 API key
"""

import os
import re
import json
from typing import List, Optional, Dict, Any
from time import sleep
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Khởi tạo Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Try import yt_dlp for faster search (optional)
try:
    from yt_dlp import YoutubeDL
    _HAS_YT_DLP = True
except ImportError:
    _HAS_YT_DLP = False
    YoutubeDL = None


def get_youtube_links_with_ytdlp(
    keyword: str,
    max_results: int = 10,
    max_minutes: Optional[int] = None,
    min_minutes: Optional[int] = None,
    use_ai_filter: bool = True,
) -> List[str]:
    """Sử dụng yt_dlp để tìm YouTube videos (NHANH NHẤT, KHÔNG CẦN GEMINI API cho search).

    Args:
        keyword: Search keyword
        max_results: Số video tối đa
        max_minutes: Thời lượng tối đa (phút)
        min_minutes: Thời lượng tối thiểu (phút)
        use_ai_filter: Dùng Gemini AI để filter kết quả (optional)

    Returns:
        List of YouTube video URLs
    """
    if not _HAS_YT_DLP:
        print("[get_link_gemini] yt_dlp not installed, falling back to Gemini search")
        return get_youtube_links_with_gemini(keyword, max_results, max_minutes, min_minutes)

    try:
        # Search nhiều hơn để filter bằng AI
        search_count = max_results * 3 if use_ai_filter and GEMINI_API_KEY else max_results + 5

        query = f"ytsearch{search_count}:{keyword}"
        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "default_search": "ytsearch",
            "noplaylist": True,
            "extract_flat": True,  # Fast mode - không download metadata đầy đủ
            "ignoreerrors": True,
        }

        videos = []
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False) or {}
            for entry in (info.get("entries") or []):
                if not isinstance(entry, dict):
                    continue

                url = entry.get("url") or entry.get("webpage_url") or entry.get("id")
                if not url:
                    continue

                if not url.startswith("http"):
                    url = f"https://www.youtube.com/watch?v={url}"

                title = entry.get("title") or ""
                duration = entry.get("duration")  # seconds
                channel = entry.get("channel") or entry.get("uploader") or ""

                # Filter by duration
                if duration:
                    if max_minutes and duration > max_minutes * 60:
                        continue
                    if min_minutes and duration < min_minutes * 60:
                        continue

                videos.append({
                    "url": url,
                    "title": title,
                    "duration_seconds": duration,
                    "channel": channel
                })

        print(f"[get_link_gemini] yt_dlp found {len(videos)} videos for '{keyword}'")

        # AI filtering với Gemini
        if use_ai_filter and GEMINI_API_KEY and len(videos) > max_results:
            print(f"[get_link_gemini] Using Gemini AI to filter top {max_results} videos...")
            filtered = filter_videos_with_gemini_ai(keyword, videos, max_results)
            return [v["url"] for v in filtered]

        # Return URLs
        return [v["url"] for v in videos[:max_results]]

    except Exception as e:
        print(f"[get_link_gemini] ERROR with yt_dlp: {e}")
        import traceback
        traceback.print_exc()
        return []


def filter_videos_with_gemini_ai(
    keyword: str,
    candidates: List[Dict[str, Any]],
    max_keep: int = 10,
) -> List[Dict[str, Any]]:
    """Dùng Gemini AI để filter videos phù hợp nhất.

    Args:
        keyword: Search keyword
        candidates: List of video dicts with url, title, duration_seconds, channel
        max_keep: Số video giữ lại

    Returns:
        Filtered list of videos
    """
    if not GEMINI_API_KEY:
        return candidates[:max_keep]

    if len(candidates) <= max_keep:
        return candidates

    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')

        # Build video list text
        items_text = []
        for idx, video in enumerate(candidates):
            title = video.get("title", "")
            duration = video.get("duration_seconds")
            channel = video.get("channel", "")
            url = video.get("url", "")

            dur_str = f"{int(duration)}s" if duration else "unknown"
            items_text.append(f"{idx}. title='{title}', duration={dur_str}, channel='{channel}', url={url}")

        items_str = "\n".join(items_text)

        prompt = f"""Keyword: {keyword}

Below is a list of candidate YouTube videos from a search.
Each line shows: index, title, duration (seconds), channel, url

{items_str}

Task:
- Pick at most {max_keep} videos that best match the keyword "{keyword}"
- Prefer videos that are:
  * Clearly about the keyword
  * Not 'live', 'premiere', 'upcoming', or spam compilation
  * Reasonable length (not several hours unless keyword implies that)
  * High quality content

Return STRICT JSON with this structure ONLY:
{{
  "keep_indices": [0, 3, 5, ...]
}}

If none are good, return: {{ "keep_indices": [] }}"""

        response = model.generate_content(prompt)
        text = response.text.strip()

        # Extract JSON
        json_match = re.search(r'\{.*?\}', text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            indices = data.get("keep_indices", [])

            if isinstance(indices, list):
                # Filter valid indices
                valid_indices = []
                seen = set()
                for idx in indices:
                    try:
                        i = int(idx)
                        if 0 <= i < len(candidates) and i not in seen:
                            valid_indices.append(i)
                            seen.add(i)
                    except:
                        pass

                if valid_indices:
                    result = [candidates[i] for i in valid_indices]
                    print(f"[get_link_gemini] AI filtered {len(candidates)} -> {len(result)} videos")
                    return result

        print(f"[get_link_gemini] AI filtering failed, using top {max_keep}")
        return candidates[:max_keep]

    except Exception as e:
        print(f"[get_link_gemini] ERROR in AI filtering: {e}")
        return candidates[:max_keep]


def get_youtube_links_with_gemini(
    keyword: str,
    max_results: int = 10,
    max_minutes: Optional[int] = None,
    min_minutes: Optional[int] = None,
) -> List[str]:
    """Sử dụng Gemini API để tìm YouTube video links.

    Args:
        keyword: Search keyword
        max_results: Số video tối đa
        max_minutes: Thời lượng tối đa (phút)
        min_minutes: Thời lượng tối thiểu (phút)

    Returns:
        List of YouTube video URLs
    """
    if not GEMINI_API_KEY:
        print("[get_link_gemini] ERROR: No GEMINI_API_KEY found!")
        return []

    try:
        # Sử dụng Gemini với Google Search grounding
        model = genai.GenerativeModel(
            'gemini-2.0-flash-exp',
            tools='google_search_retrieval'
        )

        # Tạo prompt để tìm YouTube videos
        duration_filter = ""
        if min_minutes and max_minutes:
            duration_filter = f" between {min_minutes}-{max_minutes} minutes long"
        elif max_minutes:
            duration_filter = f" under {max_minutes} minutes long"
        elif min_minutes:
            duration_filter = f" at least {min_minutes} minutes long"

        prompt = f"""Search YouTube for "{keyword}" and find {max_results} relevant video URLs{duration_filter}.

IMPORTANT: Return ONLY a JSON array of YouTube video URLs (direct watch links).
Format: ["https://www.youtube.com/watch?v=xxxxx", "https://www.youtube.com/watch?v=yyyyy", ...]

Requirements:
- Must be actual YouTube watch URLs (youtube.com/watch?v=...)
- No shorts, no playlists, no channels
- Focus on relevant, quality videos
- Return exactly {max_results} URLs if possible

Example format:
["https://www.youtube.com/watch?v=dQw4w9WgXcQ", "https://www.youtube.com/watch?v=jNQXAC9IVRw"]"""

        print(f"[get_link_gemini] Searching YouTube for '{keyword}'{duration_filter}...")
        response = model.generate_content(prompt)

        # Parse JSON response
        text = response.text.strip()

        # Extract JSON array
        json_match = re.search(r'\[.*?\]', text, re.DOTALL)
        if json_match:
            try:
                urls = json.loads(json_match.group())
                if isinstance(urls, list):
                    # Filter valid YouTube URLs
                    valid_urls = []
                    for url in urls:
                        if isinstance(url, str) and 'youtube.com/watch?v=' in url:
                            valid_urls.append(url)

                    print(f"[get_link_gemini] Found {len(valid_urls)} YouTube videos for '{keyword}'")
                    return valid_urls[:max_results]
            except json.JSONDecodeError as e:
                print(f"[get_link_gemini] JSON parse error: {e}")

        # Fallback: extract any YouTube links from response
        youtube_pattern = r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+'
        fallback_urls = re.findall(youtube_pattern, text)
        if fallback_urls:
            print(f"[get_link_gemini] Found {len(fallback_urls)} YouTube videos (fallback extraction)")
            return list(set(fallback_urls))[:max_results]

        print(f"[get_link_gemini] No YouTube URLs found for '{keyword}'")
        return []

    except Exception as e:
        print(f"[get_link_gemini] ERROR getting YouTube videos: {e}")
        import traceback
        traceback.print_exc()
        return []




def get_image_links_with_gemini(
    keyword: str,
    num_images: int = 10,
) -> List[str]:
    """Sử dụng Gemini API để tìm Google Image links.

    Args:
        keyword: Search keyword
        num_images: Số ảnh cần lấy

    Returns:
        List of image URLs
    """
    if not GEMINI_API_KEY:
        print("[get_link_gemini] ERROR: No GEMINI_API_KEY found!")
        return []

    try:
        # Sử dụng Gemini với Google Search grounding
        model = genai.GenerativeModel(
            'gemini-2.0-flash-exp',
            tools='google_search_retrieval'
        )

        prompt = f"""Search Google Images for "{keyword}" and find {num_images} direct image URLs.

IMPORTANT: Return ONLY a JSON array of direct image URLs (actual image files, not webpage links).
Format: ["https://example.com/image1.jpg", "https://example.com/image2.png", ...]

Requirements:
- Must be direct links to image files (.jpg, .jpeg, .png, .webp, .gif)
- High quality images (preferably > 500px width)
- No thumbnails, no data: URIs, no encrypted links
- Actual downloadable image URLs

Example format:
["https://example.com/photo.jpg", "https://site.com/pic.png"]"""

        print(f"[get_link_gemini] Searching Google Images for '{keyword}'...")
        response = model.generate_content(prompt)

        # Parse JSON response
        text = response.text.strip()

        # Extract JSON array
        json_match = re.search(r'\[.*?\]', text, re.DOTALL)
        if json_match:
            try:
                urls = json.loads(json_match.group())
                if isinstance(urls, list):
                    # Filter valid image URLs
                    valid_urls = []
                    for url in urls:
                        if isinstance(url, str) and url.startswith('http'):
                            # Check if it's likely an image URL
                            if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
                                valid_urls.append(url)
                            # Also accept URLs without extension (might be dynamic)
                            elif '/image' in url.lower() or '/photo' in url.lower():
                                valid_urls.append(url)

                    print(f"[get_link_gemini] Found {len(valid_urls)} image URLs for '{keyword}'")
                    return valid_urls[:num_images]
            except json.JSONDecodeError as e:
                print(f"[get_link_gemini] JSON parse error: {e}")

        # Fallback: extract any image URLs from response
        image_pattern = r'https?://[^\s"\'<>]+\.(?:jpg|jpeg|png|webp|gif)'
        fallback_urls = re.findall(image_pattern, text, re.IGNORECASE)
        if fallback_urls:
            print(f"[get_link_gemini] Found {len(fallback_urls)} image URLs (fallback extraction)")
            return list(set(fallback_urls))[:num_images]

        print(f"[get_link_gemini] No image URLs found for '{keyword}'")
        return []

    except Exception as e:
        print(f"[get_link_gemini] ERROR getting images: {e}")
        import traceback
        traceback.print_exc()
        return []




def read_keywords_from_file(file_path: str) -> List[str]:
    """Đọc keywords từ file."""
    if not os.path.isfile(file_path):
        print(f"[get_link_gemini] Keywords file not found: {file_path}")
        return []

    ordered = []
    seen = set()

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue

            # Format: "<index> <keyword>"
            parts = line.split(maxsplit=1)
            if len(parts) == 2 and parts[0].isdigit():
                keyword = parts[1].strip()
            else:
                keyword = line

            if keyword and keyword not in seen:
                seen.add(keyword)
                ordered.append(keyword)

    print(f"[get_link_gemini] Loaded {len(ordered)} unique keywords")
    return ordered


def get_links_main_video(
    keywords_file: str,
    output_txt: str,
    project_name: Optional[str] = None,
    max_per_keyword: int = 2,
    max_minutes: Optional[int] = None,
    min_minutes: Optional[int] = None,
    use_gemini_optimize: bool = True,
):
    """Thu link video và ghi ra file (CHỈ DÙNG GEMINI API).

    Args:
        keywords_file: File chứa keywords
        output_txt: File output
        project_name: Tên project (optional)
        max_per_keyword: Số video tối đa mỗi keyword
        max_minutes: Thời lượng tối đa (phút)
        min_minutes: Thời lượng tối thiểu (phút)
        use_gemini_optimize: Deprecated - luôn dùng Gemini
    """
    print("[get_link_gemini] === START get_links_main_video (GEMINI API ONLY) ===")
    print(f"[get_link_gemini] keywords_file = {keywords_file}")
    print(f"[get_link_gemini] output_txt    = {output_txt}")
    if project_name:
        print(f"[get_link_gemini] project_name  = {project_name}")

    if not GEMINI_API_KEY:
        print("[get_link_gemini] ERROR: GEMINI_API_KEY not found in .env!")
        print("[get_link_gemini] Please add GEMINI_API_KEY to your .env file")
        return

    keywords = read_keywords_from_file(keywords_file)
    if not keywords:
        print("[get_link_gemini] No keywords found -> abort")
        return

    # Clear output file
    try:
        with open(output_txt, 'w', encoding='utf-8') as f:
            f.write('')
    except Exception as e:
        print(f"[get_link_gemini] ERROR: cannot clear output file: {e}")
        return

    stt = 0
    num_vd = 0

    for idx, keyword in enumerate(keywords, start=1):
        print(f"[get_link_gemini] --- ({idx}/{len(keywords)}) '{keyword}' ---")

        try:
            # Ưu tiên dùng yt_dlp (nhanh nhất, không cần Gemini API cho search)
            if _HAS_YT_DLP:
                video_links = get_youtube_links_with_ytdlp(
                    keyword,
                    max_results=max_per_keyword,
                    max_minutes=max_minutes,
                    min_minutes=min_minutes,
                    use_ai_filter=bool(GEMINI_API_KEY),  # Dùng AI filter nếu có Gemini API
                )
            else:
                # Fallback: dùng Gemini search
                video_links = get_youtube_links_with_gemini(
                    keyword,
                    max_results=max_per_keyword,
                    max_minutes=max_minutes,
                    min_minutes=min_minutes,
                )
        except Exception as e:
            print(f"[get_link_gemini] ERROR collecting video links: {e}")
            video_links = []

        stt += 1
        try:
            with open(output_txt, 'a', encoding='utf-8') as f:
                f.write(f"{stt} {keyword}\n")
                for link in video_links:
                    num_vd += 1
                    f.write(f"{link}\n")
        except Exception as e:
            print(f"[get_link_gemini] ERROR writing video links: {e}")

        sleep(1.0)  # Rate limiting for Gemini API

    print(f"[get_link_gemini] TOTAL video links written: {num_vd}")
    print("[get_link_gemini] === END get_links_main_video ===")


def get_links_main_image(
    keywords_file: str,
    output_txt: str,
    project_name: Optional[str] = None,
    images_per_keyword: int = 10,
    use_gemini_optimize: bool = True,
):
    """Thu link ảnh và ghi ra file (CHỈ DÙNG GEMINI API).

    Args:
        keywords_file: File chứa keywords
        output_txt: File output
        project_name: Tên project (optional)
        images_per_keyword: Số ảnh mỗi keyword
        use_gemini_optimize: Deprecated - luôn dùng Gemini
    """
    print("[get_link_gemini] === START get_links_main_image (GEMINI API ONLY) ===")
    print(f"[get_link_gemini] keywords_file = {keywords_file}")
    print(f"[get_link_gemini] output_txt    = {output_txt}")
    if project_name:
        print(f"[get_link_gemini] project_name  = {project_name}")

    if not GEMINI_API_KEY:
        print("[get_link_gemini] ERROR: GEMINI_API_KEY not found in .env!")
        print("[get_link_gemini] Please add GEMINI_API_KEY to your .env file")
        return

    keywords = read_keywords_from_file(keywords_file)
    if not keywords:
        print("[get_link_gemini] No keywords found -> abort")
        return

    # Clear output file
    try:
        with open(output_txt, 'w', encoding='utf-8') as f:
            f.write('')
    except Exception as e:
        print(f"[get_link_gemini] ERROR: cannot clear output file: {e}")
        return

    stt = 0
    num_img = 0

    for idx, keyword in enumerate(keywords, start=1):
        print(f"[get_link_gemini] --- ({idx}/{len(keywords)}) '{keyword}' ---")

        try:
            image_links = get_image_links_with_gemini(
                keyword,
                num_images=images_per_keyword,
            )
        except Exception as e:
            print(f"[get_link_gemini] ERROR collecting image links: {e}")
            image_links = []

        stt += 1
        try:
            with open(output_txt, 'a', encoding='utf-8') as f:
                f.write(f"{stt} {keyword}\n")
                for link in image_links:
                    num_img += 1
                    f.write(f"{link}\n")
        except Exception as e:
            print(f"[get_link_gemini] ERROR writing image links: {e}")

        sleep(1.0)  # Rate limiting for Gemini API

    print(f"[get_link_gemini] TOTAL image links written: {num_img}")
    print("[get_link_gemini] === END get_links_main_image ===")


def get_links_main(
    keywords_file: str,
    output_txt: str,
    project_name: Optional[str] = None,
    max_per_keyword: int = 2,
    max_minutes: Optional[int] = None,
    min_minutes: Optional[int] = None,
    images_per_keyword: int = 10,
    use_gemini_optimize: bool = True,
):
    """Compatibility function - chạy cả video và ảnh."""
    print("[get_link_gemini] === START get_links_main (compat) ===")

    # Video
    get_links_main_video(
        keywords_file=keywords_file,
        output_txt=output_txt,
        project_name=project_name,
        max_per_keyword=max_per_keyword,
        max_minutes=max_minutes,
        min_minutes=min_minutes,
        use_gemini_optimize=use_gemini_optimize,
    )

    # Image
    if isinstance(output_txt, str) and output_txt.lower().endswith('.txt'):
        img_output = output_txt[:-4] + '_image.txt'
    else:
        img_output = output_txt + '_image'

    get_links_main_image(
        keywords_file=keywords_file,
        output_txt=img_output,
        project_name=project_name,
        images_per_keyword=images_per_keyword,
        use_gemini_optimize=use_gemini_optimize,
    )

    print("[get_link_gemini] === END get_links_main (compat) ===")


if __name__ == "__main__":
    import sys
    THIS_DIR = os.path.abspath(os.path.dirname(__file__))
    ROOT_DIR = os.path.abspath(os.path.join(THIS_DIR, '..', '..'))
    DATA_DIR = os.path.join(ROOT_DIR, 'data')

    if not os.path.isdir(DATA_DIR):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
        except Exception:
            pass

    keywords_file = os.path.join(DATA_DIR, 'list_name.txt')
    output_txt = os.path.join(DATA_DIR, 'dl_links.txt')

    get_links_main(keywords_file, output_txt)
