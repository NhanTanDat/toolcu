"""YouTube/Google Images link gathering using Gemini API.

Tính năng:
 - Sử dụng Gemini API để tối ưu search queries
 - Sử dụng YouTube Data API hoặc youtubesearchpython để lấy video links
 - Sử dụng Gemini với Google Search để lấy image links
 - Không cần Selenium - chạy hoàn toàn trong terminal
 - Logging rõ ràng, bắt lỗi từng keyword
 - Giới hạn số video/ảnh mỗi keyword
 - Lọc theo thời lượng video (min/max minutes)
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


def optimize_search_query_with_gemini(keyword: str, search_type: str = 'video') -> str:
    """Sử dụng Gemini để tối ưu search query.

    Args:
        keyword: Từ khóa gốc
        search_type: 'video' hoặc 'image'

    Returns:
        Query đã được tối ưu
    """
    if not GEMINI_API_KEY:
        print("[get_link_gemini] WARNING: No GEMINI_API_KEY found, using original keyword")
        return keyword

    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')

        if search_type == 'video':
            prompt = f"""Given the keyword "{keyword}", generate an optimized YouTube search query to find relevant videos.
Return ONLY the search query text, nothing else. Keep it concise and effective for YouTube search.
If the keyword is already good, return it as-is."""
        else:  # image
            prompt = f"""Given the keyword "{keyword}", generate an optimized Google Images search query to find relevant images.
Return ONLY the search query text, nothing else. Keep it concise and effective for image search.
If the keyword is already good, return it as-is."""

        response = model.generate_content(prompt)
        optimized = response.text.strip()

        # Remove quotes if Gemini added them
        optimized = optimized.strip('"\'')

        print(f"[get_link_gemini] Optimized '{keyword}' -> '{optimized}'")
        return optimized

    except Exception as e:
        print(f"[get_link_gemini] ERROR optimizing query with Gemini: {e}")
        return keyword


def parse_duration_to_seconds(duration_str: str) -> Optional[int]:
    """Parse ISO 8601 duration (PT1H2M3S) to seconds."""
    if not duration_str:
        return None

    # ISO 8601 duration format: PT1H2M3S
    pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
    match = re.match(pattern, duration_str)

    if not match:
        return None

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)

    return hours * 3600 + minutes * 60 + seconds


def get_youtube_videos_with_api(
    keyword: str,
    max_results: int = 10,
    max_minutes: Optional[int] = None,
    min_minutes: Optional[int] = None,
) -> List[str]:
    """Lấy video links từ YouTube Data API v3.

    Args:
        keyword: Search keyword
        max_results: Số video tối đa
        max_minutes: Thời lượng tối đa (phút)
        min_minutes: Thời lượng tối thiểu (phút)

    Returns:
        List of YouTube video URLs
    """
    api_key = os.getenv('YOUTUBE_API_KEY', '')

    if not api_key:
        print("[get_link_gemini] WARNING: No YOUTUBE_API_KEY found, using fallback method")
        return get_youtube_videos_fallback(keyword, max_results, max_minutes, min_minutes)

    try:
        from googleapiclient.discovery import build

        youtube = build('youtube', 'v3', developerKey=api_key)

        # Search for videos
        search_response = youtube.search().list(
            q=keyword,
            part='id',
            type='video',
            maxResults=min(max_results * 2, 50),  # Get more to filter
            order='relevance',
            videoDuration='medium' if max_minutes and max_minutes <= 20 else 'any'
        ).execute()

        video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]

        if not video_ids:
            print(f"[get_link_gemini] No videos found for '{keyword}'")
            return []

        # Get video details including duration
        videos_response = youtube.videos().list(
            part='contentDetails',
            id=','.join(video_ids)
        ).execute()

        links = []
        max_seconds = max_minutes * 60 if max_minutes else None
        min_seconds = min_minutes * 60 if min_minutes else None

        for item in videos_response.get('items', []):
            if len(links) >= max_results:
                break

            video_id = item['id']
            duration_str = item['contentDetails']['duration']
            duration_seconds = parse_duration_to_seconds(duration_str)

            # Filter by duration
            if duration_seconds is None:
                continue

            if max_seconds and duration_seconds > max_seconds:
                continue

            if min_seconds and duration_seconds < min_seconds:
                continue

            links.append(f"https://www.youtube.com/watch?v={video_id}")

        print(f"[get_link_gemini] Found {len(links)} videos for '{keyword}' (filtered by duration)")
        return links

    except Exception as e:
        print(f"[get_link_gemini] ERROR using YouTube API: {e}")
        return get_youtube_videos_fallback(keyword, max_results, max_minutes, min_minutes)


def get_youtube_videos_fallback(
    keyword: str,
    max_results: int = 10,
    max_minutes: Optional[int] = None,
    min_minutes: Optional[int] = None,
) -> List[str]:
    """Fallback method using youtubesearchpython library.

    Args:
        keyword: Search keyword
        max_results: Số video tối đa
        max_minutes: Thời lượng tối đa (phút)
        min_minutes: Thời lượng tối thiểu (phút)

    Returns:
        List of YouTube video URLs
    """
    try:
        from youtubesearchpython import VideosSearch

        # Search with more results to allow for filtering
        search = VideosSearch(keyword, limit=min(max_results * 3, 50))
        results = search.result()

        links = []
        max_seconds = max_minutes * 60 if max_minutes else None
        min_seconds = min_minutes * 60 if min_minutes else None

        for video in results.get('result', []):
            if len(links) >= max_results:
                break

            # Parse duration
            duration_str = video.get('duration', '')
            duration_seconds = None

            if duration_str:
                # Duration format: "1:23:45" or "12:34" or "1:23"
                parts = duration_str.split(':')
                try:
                    if len(parts) == 3:
                        h, m, s = map(int, parts)
                        duration_seconds = h * 3600 + m * 60 + s
                    elif len(parts) == 2:
                        m, s = map(int, parts)
                        duration_seconds = m * 60 + s
                    elif len(parts) == 1:
                        duration_seconds = int(parts[0])
                except:
                    pass

            # Filter by duration
            if duration_seconds is None:
                continue

            if max_seconds and duration_seconds > max_seconds:
                continue

            if min_seconds and duration_seconds < min_seconds:
                continue

            link = video.get('link', '')
            if link:
                links.append(link)

        print(f"[get_link_gemini] Found {len(links)} videos for '{keyword}' (fallback method)")

        if not links:
            # Add fallback link
            links.append("https://www.youtube.com/watch?v=WqQUvfsavO4")

        return links

    except Exception as e:
        print(f"[get_link_gemini] ERROR in fallback method: {e}")
        return ["https://www.youtube.com/watch?v=WqQUvfsavO4"]


def get_image_links_with_gemini(
    keyword: str,
    num_images: int = 10,
) -> List[str]:
    """Lấy image links sử dụng Gemini API với Google Search grounding.

    Args:
        keyword: Search keyword
        num_images: Số ảnh cần lấy

    Returns:
        List of image URLs
    """
    if not GEMINI_API_KEY:
        print("[get_link_gemini] WARNING: No GEMINI_API_KEY, cannot search images")
        return []

    try:
        # Sử dụng Gemini với Google Search grounding
        model = genai.GenerativeModel(
            'gemini-2.0-flash-exp',
            tools='google_search_retrieval'
        )

        prompt = f"""Search Google Images for "{keyword}" and provide {num_images} direct image URLs.
Return ONLY a JSON array of image URLs (direct links to actual image files, not webpage links).
Format: ["url1", "url2", "url3", ...]
Only include high-quality images (preferably > 500px width)."""

        response = model.generate_content(prompt)

        # Try to parse JSON from response
        text = response.text.strip()

        # Extract JSON array
        json_match = re.search(r'\[.*\]', text, re.DOTALL)
        if json_match:
            urls = json.loads(json_match.group())
            if isinstance(urls, list):
                # Filter valid URLs
                valid_urls = [url for url in urls if isinstance(url, str) and url.startswith('http')]
                print(f"[get_link_gemini] Found {len(valid_urls)} image URLs for '{keyword}'")
                return valid_urls[:num_images]

        print(f"[get_link_gemini] Could not parse image URLs from Gemini response")
        return []

    except Exception as e:
        print(f"[get_link_gemini] ERROR getting images with Gemini: {e}")
        return get_image_links_fallback(keyword, num_images)


def get_image_links_fallback(keyword: str, num_images: int = 10) -> List[str]:
    """Fallback for image search using Custom Search API.

    Args:
        keyword: Search keyword
        num_images: Số ảnh cần lấy

    Returns:
        List of image URLs
    """
    api_key = os.getenv('GOOGLE_SEARCH_API_KEY', '')
    engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID', '')

    if not api_key or not engine_id:
        print("[get_link_gemini] WARNING: No Google Custom Search API credentials")
        return []

    try:
        from googleapiclient.discovery import build

        service = build('customsearch', 'v1', developerKey=api_key)

        links = []
        start_index = 1

        while len(links) < num_images and start_index <= 91:  # Max 100 results
            result = service.cse().list(
                q=keyword,
                cx=engine_id,
                searchType='image',
                num=min(10, num_images - len(links)),
                start=start_index,
                imgSize='large',
                safe='off'
            ).execute()

            items = result.get('items', [])
            if not items:
                break

            for item in items:
                link = item.get('link', '')
                if link and link.startswith('http'):
                    links.append(link)

            start_index += 10

        print(f"[get_link_gemini] Found {len(links)} images for '{keyword}' (Custom Search API)")
        return links[:num_images]

    except Exception as e:
        print(f"[get_link_gemini] ERROR in Custom Search API: {e}")
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
    """Thu link video và ghi ra file.

    Args:
        keywords_file: File chứa keywords
        output_txt: File output
        project_name: Tên project (optional)
        max_per_keyword: Số video tối đa mỗi keyword
        max_minutes: Thời lượng tối đa (phút)
        min_minutes: Thời lượng tối thiểu (phút)
        use_gemini_optimize: Có sử dụng Gemini để optimize query không
    """
    print("[get_link_gemini] === START get_links_main_video ===")
    print(f"[get_link_gemini] keywords_file = {keywords_file}")
    print(f"[get_link_gemini] output_txt    = {output_txt}")
    if project_name:
        print(f"[get_link_gemini] project_name  = {project_name}")

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

        # Optimize query with Gemini if enabled
        search_query = keyword
        if use_gemini_optimize and GEMINI_API_KEY:
            search_query = optimize_search_query_with_gemini(keyword, 'video')

        try:
            video_links = get_youtube_videos_with_api(
                search_query,
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

        sleep(0.5)  # Rate limiting

    print(f"[get_link_gemini] TOTAL video links written: {num_vd}")
    print("[get_link_gemini] === END get_links_main_video ===")


def get_links_main_image(
    keywords_file: str,
    output_txt: str,
    project_name: Optional[str] = None,
    images_per_keyword: int = 10,
    use_gemini_optimize: bool = True,
):
    """Thu link ảnh và ghi ra file.

    Args:
        keywords_file: File chứa keywords
        output_txt: File output
        project_name: Tên project (optional)
        images_per_keyword: Số ảnh mỗi keyword
        use_gemini_optimize: Có sử dụng Gemini để optimize query không
    """
    print("[get_link_gemini] === START get_links_main_image ===")
    print(f"[get_link_gemini] keywords_file = {keywords_file}")
    print(f"[get_link_gemini] output_txt    = {output_txt}")
    if project_name:
        print(f"[get_link_gemini] project_name  = {project_name}")

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

        # Optimize query with Gemini if enabled
        search_query = keyword
        if use_gemini_optimize and GEMINI_API_KEY:
            search_query = optimize_search_query_with_gemini(keyword, 'image')

        try:
            image_links = get_image_links_with_gemini(
                search_query,
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

        sleep(0.5)  # Rate limiting

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
