"""API configuration helper.

Cung cấp các hàm để đọc API keys từ config.json.
Các module khác có thể import và sử dụng:

    from core.api_config import get_api_key

    google_key = get_api_key('google')
    youtube_key = get_api_key('youtube')
    gemini_key = get_api_key('gemini')
"""

import os
import json

# Đường dẫn đến file config
_THIS_DIR = os.path.abspath(os.path.dirname(__file__))
_ROOT_DIR = os.path.abspath(os.path.join(_THIS_DIR, '..'))
DATA_DIR = os.path.join(_ROOT_DIR, 'data')
CONFIG_PATH = os.path.join(DATA_DIR, 'config.json')


def _load_config() -> dict:
    """Load config từ file JSON."""
    if not os.path.isfile(CONFIG_PATH):
        return {}
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def get_api_key(key_type: str) -> str:
    """Lấy API key theo loại.

    Args:
        key_type: Loại API key ('google', 'youtube', 'gemini')

    Returns:
        API key string hoặc rỗng nếu không tìm thấy.
    """
    cfg = _load_config()
    key_name = f'{key_type}_api_key'
    return str(cfg.get(key_name, ''))


def get_google_api_key() -> str:
    """Lấy Google API key."""
    return get_api_key('google')


def get_youtube_api_key() -> str:
    """Lấy YouTube API key."""
    return get_api_key('youtube')


def get_gemini_api_key() -> str:
    """Lấy Gemini API key."""
    return get_api_key('gemini')


def has_api_key(key_type: str) -> bool:
    """Kiểm tra xem API key đã được cấu hình chưa."""
    return bool(get_api_key(key_type))
