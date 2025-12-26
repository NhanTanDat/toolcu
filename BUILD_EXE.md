# 🏗️ Hướng Dẫn Build File .EXE

## ⚠️ Vấn Đề Với File .EXE

**Hiện tượng:**
- ✅ Chạy Python script: Tải video **BÌNH THƯỜNG**
- ❌ Chạy file .exe: **KHÔNG tải được video**

**Nguyên nhân:**
- PyInstaller không tự động bundle `ffmpeg.exe`
- Thiếu một số hidden imports (google-generativeai, dotenv)
- yt-dlp không tìm thấy ffmpeg trong runtime

## ✅ GIẢI PHÁP (Đã Fix!)

### Bước 1: Cài Đặt Dependencies

```bash
pip install pyinstaller
```

### Bước 2: Download ffmpeg.exe

**Option A: Tự động (khuyến nghị)**
- File `autotool.spec` đã được cấu hình tự động tìm ffmpeg
- Nếu ffmpeg có trong PATH, sẽ tự động bundle vào .exe

**Option B: Thủ công**

1. Download ffmpeg từ: https://github.com/BtbN/FFmpeg-Builds/releases
2. Giải nén và copy `ffmpeg.exe` vào:
   - **Option 1:** Cùng folder với project (root)
   - **Option 2:** Folder `bin/ffmpeg.exe`
   - **Option 3:** Thêm vào PATH

### Bước 3: Build .EXE

```bash
pyinstaller autotool.spec
```

**Output:** File .exe sẽ nằm trong folder `dist/autotool/`

### Bước 4: Test

```bash
cd dist/autotool
autotool.exe
```

## 📋 Đã Sửa Gì Trong autotool.spec?

### 1. Thêm Hidden Imports Mới

```python
hiddenimports = [
    'selenium',
    'yt_dlp',
    'google.generativeai',        # ⭐ MỚI - Gemini API
    'google.ai.generativelanguage', # ⭐ MỚI
    'dotenv',                      # ⭐ MỚI - Load .env
    'pyperclip',                   # ⭐ MỚI - Optional
]
```

### 2. Tự Động Tìm & Bundle ffmpeg.exe

```python
# Check common locations
ffmpeg_locations = [
    shutil.which('ffmpeg'),         # From PATH
    'ffmpeg.exe',                    # Current directory
    'bin/ffmpeg.exe',               # bin folder
]

# Auto-include if found
if ffmpeg_path:
    binaries.append((ffmpeg_path, '.'))
```

### 3. Thu Thập Google Generative AI Modules

```python
hiddenimports += collect_submodules('google.generativeai')
```

## 🎯 Kết Quả

**Trước fix:**
- ❌ Video không tải được trong .exe
- ❌ Gemini API không hoạt động
- ❌ Thiếu ffmpeg

**Sau fix:**
- ✅ Video tải được (nếu có ffmpeg)
- ✅ Gemini API hoạt động
- ✅ Tự động bundle ffmpeg nếu tìm thấy
- ✅ Thông báo rõ ràng nếu thiếu ffmpeg

## 📦 Cấu Trúc Folder Sau Khi Build

```
dist/
└── autotool/
    ├── autotool.exe        # Main executable
    ├── ffmpeg.exe          # (Tự động nếu tìm thấy)
    ├── core/               # Python modules
    ├── GUI/                # GUI files
    ├── data/               # Data folder
    └── _internal/          # PyInstaller files
```

## ⚠️ Nếu Vẫn Không Tải Được Video

### Giải pháp nhanh:

**Copy ffmpeg.exe vào cùng folder với autotool.exe:**

```
dist/autotool/
├── autotool.exe
└── ffmpeg.exe    ← Đặt file này ở đây
```

**Download ffmpeg.exe:**
1. Vào: https://github.com/BtbN/FFmpeg-Builds/releases
2. Tải bản **ffmpeg-master-latest-win64-gpl.zip**
3. Giải nén → Copy `ffmpeg.exe` từ folder `bin/`
4. Paste vào `dist/autotool/`

## 🔍 Debug

**Kiểm tra xem ffmpeg có được bundle không:**

```bash
# Trong folder dist/autotool/
dir ffmpeg.exe

# Hoặc chạy
autotool.exe
# → Check log: "ffmpeg = ..." trong console
```

**Nếu thấy:**
- `ffmpeg = NOT FOUND` → Cần copy ffmpeg.exe thủ công
- `ffmpeg = C:\...` → ffmpeg đã được tìm thấy ✅

## 📝 Build Script Tự Động (Optional)

Tạo file `build.bat`:

```batch
@echo off
echo Building AutoTool.exe...
echo.

REM Clean old build
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Build with PyInstaller
pyinstaller autotool.spec

REM Check if ffmpeg exists in dist
if not exist "dist\autotool\ffmpeg.exe" (
    echo WARNING: ffmpeg.exe not found!
    echo Please copy ffmpeg.exe to dist\autotool\
)

echo.
echo Build complete! Check dist\autotool\
pause
```

Chạy:
```bash
build.bat
```

---

**Made with ❤️ for PyInstaller users**
