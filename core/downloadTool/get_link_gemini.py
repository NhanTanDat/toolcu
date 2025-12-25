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
