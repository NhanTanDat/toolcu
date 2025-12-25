#!/usr/bin/env python3
"""Script test để demo Gemini API search trong terminal.

Usage:
    python test_gemini_search.py
"""

import os
import sys

# Add project root to path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

from core.downloadTool import get_link_gemini
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_video_search():
    """Test search YouTube videos với Gemini API."""
    print("\n" + "="*60)
    print("TEST: YouTube Video Search với Gemini API")
    print("="*60 + "\n")

    keyword = "python programming tutorial"
    print(f"Keyword: {keyword}")
    print(f"Max results: 3")
    print(f"Duration: 4-20 minutes\n")

    try:
        links = get_link_gemini.get_youtube_videos_with_api(
            keyword=keyword,
            max_results=3,
            max_minutes=20,
            min_minutes=4,
        )

        print(f"\n✓ Tìm thấy {len(links)} video links:")
        for i, link in enumerate(links, 1):
            print(f"  {i}. {link}")

        return True

    except Exception as e:
        print(f"\n✗ Lỗi: {e}")
        return False


def test_image_search():
    """Test search Google Images với Gemini API."""
    print("\n" + "="*60)
    print("TEST: Google Image Search với Gemini API")
    print("="*60 + "\n")

    keyword = "beautiful landscape"
    print(f"Keyword: {keyword}")
    print(f"Max results: 5\n")

    try:
        links = get_link_gemini.get_image_links_with_gemini(
            keyword=keyword,
            num_images=5,
        )

        print(f"\n✓ Tìm thấy {len(links)} image links:")
        for i, link in enumerate(links, 1):
            print(f"  {i}. {link[:80]}...")

        return True

    except Exception as e:
        print(f"\n✗ Lỗi: {e}")
        return False


def test_query_optimization():
    """Test Gemini query optimization."""
    print("\n" + "="*60)
    print("TEST: Gemini Query Optimization")
    print("="*60 + "\n")

    keywords = [
        "cat",
        "beautiful sunset",
        "how to cook pasta"
    ]

    print("Testing query optimization:\n")

    for keyword in keywords:
        try:
            optimized = get_link_gemini.optimize_search_query_with_gemini(
                keyword=keyword,
                search_type='video'
            )
            print(f"  '{keyword}' -> '{optimized}'")
        except Exception as e:
            print(f"  '{keyword}' -> ERROR: {e}")

    return True


def test_full_workflow():
    """Test full workflow với file keywords."""
    print("\n" + "="*60)
    print("TEST: Full Workflow - Keywords File to Output")
    print("="*60 + "\n")

    # Tạo test keywords file
    data_dir = os.path.join(ROOT_DIR, 'data')
    os.makedirs(data_dir, exist_ok=True)

    keywords_file = os.path.join(data_dir, 'test_keywords.txt')
    output_video = os.path.join(data_dir, 'test_output_video.txt')
    output_image = os.path.join(data_dir, 'test_output_image.txt')

    # Write test keywords
    with open(keywords_file, 'w', encoding='utf-8') as f:
        f.write("1 python tutorial\n")
        f.write("2 beautiful landscape\n")

    print(f"Keywords file: {keywords_file}")
    print(f"Output video: {output_video}")
    print(f"Output image: {output_image}\n")

    try:
        # Test video search
        print("Testing video search...")
        get_link_gemini.get_links_main_video(
            keywords_file=keywords_file,
            output_txt=output_video,
            max_per_keyword=2,
            max_minutes=20,
            min_minutes=4,
        )

        # Test image search
        print("\nTesting image search...")
        get_link_gemini.get_links_main_image(
            keywords_file=keywords_file,
            output_txt=output_image,
            images_per_keyword=3,
        )

        # Show results
        print("\n" + "-"*60)
        print("Video results:")
        print("-"*60)
        with open(output_video, 'r', encoding='utf-8') as f:
            print(f.read())

        print("\n" + "-"*60)
        print("Image results:")
        print("-"*60)
        with open(output_image, 'r', encoding='utf-8') as f:
            print(f.read())

        return True

    except Exception as e:
        print(f"\n✗ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function."""
    print("\n" + "="*60)
    print("GEMINI API SEARCH - TEST SUITE")
    print("="*60)

    # Check API key
    gemini_key = os.getenv('GEMINI_API_KEY', '')
    youtube_key = os.getenv('YOUTUBE_API_KEY', '')

    print(f"\nGEMINI_API_KEY: {'✓ Found' if gemini_key else '✗ Not found'}")
    print(f"YOUTUBE_API_KEY: {'✓ Found' if youtube_key else '✗ Not found (will use fallback)'}")

    if not gemini_key:
        print("\n⚠️  WARNING: GEMINI_API_KEY not found in .env file!")
        print("Please add your Gemini API key to the .env file to test this feature.")
        print("\nTo get API key:")
        print("  1. Visit: https://makersuite.google.com/app/apikey")
        print("  2. Create a new API key")
        print("  3. Add to .env: GEMINI_API_KEY=your_key_here")
        return

    # Run tests
    tests = [
        ("Query Optimization", test_query_optimization),
        ("Video Search", test_video_search),
        # ("Image Search", test_image_search),  # Commented out - requires more setup
        ("Full Workflow", test_full_workflow),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except KeyboardInterrupt:
            print("\n\n⚠️  Test interrupted by user")
            break
        except Exception as e:
            print(f"\n✗ Test '{test_name}' failed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60 + "\n")

    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {status}: {test_name}")

    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")


if __name__ == "__main__":
    main()
