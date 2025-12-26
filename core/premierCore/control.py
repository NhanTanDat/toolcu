# Try import pywinauto (required for Premiere automation)
try:
    from pywinauto import Application, Desktop
    from pywinauto.keyboard import send_keys
    _HAS_PYWINAUTO = True
except ImportError:
    _HAS_PYWINAUTO = False
    Application = None
    Desktop = None
    def send_keys(keys):
        pass

from time import sleep
import os
import sys

# Try import pyperclip (optional, only needed for clipboard operations)
try:
    import pyperclip
    _HAS_PYPERCLIP = True
except ImportError:
    _HAS_PYPERCLIP = False
    # Dummy pyperclip module when not installed
    class pyperclip:
        @staticmethod
        def copy(text):
            """Dummy copy when pyperclip not installed."""
            pass


def get_jsx_path():
    """Get the path to runAll.jsx based on whether we're running from .exe or source."""
    if getattr(sys, 'frozen', False):
        # Running as .exe - JSX files are in the same folder as .exe
        base_dir = os.path.dirname(sys.executable)
    else:
        # Running from source - JSX files are relative to this file
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

    jsx_path = os.path.join(base_dir, 'core', 'premierCore', 'runAll.jsx')
    return jsx_path.replace('/', '\\')


def copy_paste(path):
    '''function that change the download path of YT Downloader'''
    #giả lập thay tác ctrl + c bằng các lưu
    pyperclip.copy(path)
    send_keys('^v')


def focus_premiere():
    """Focus on Premiere Pro window."""
    for w in Desktop(backend="uia").windows():
        if "Adobe Premiere Pro" in w.window_text():
            w.set_focus()
            return True
    return False


#hàm này thực hiện mở Premiere và chạy file runAll.jsx tự động (KHÔNG CẦN VSCODE)
def run_premier_script(premier_path, project_path, idx):
    print("[control.py] Đang khởi động Premiere Pro...")
    os.system('taskkill /IM "Adobe Premiere Pro.exe" /F 2>nul')
    sleep(2)

    app = None
    # Kiểm tra xem Premiere đã chạy chưa
    for w in Desktop(backend="uia").windows():
        if "Adobe Premiere Pro" in w.window_text():
            app = Application(backend="uia").connect(title_re=".*Adobe Premiere Pro.*")
            w.set_focus()
            send_keys('^s')
            break

    if not app:
        print("[control.py] Premiere Pro chưa chạy, đang khởi động...")
        app = Application(backend="uia").start(
            r'"C:\Program Files\Adobe\Adobe Premiere Pro 2022\Adobe Premiere Pro.exe"',
        )

    sleep(10)  # Chờ Premiere Pro khởi động

    # Mở project
    print(f"[control.py] Đang mở project: {project_path}")
    send_keys('^o')
    sleep(2)
    copy_paste(project_path)
    send_keys('{ENTER}')
    sleep(8)  # Chờ project load

    # Đóng các popup
    for _ in range(5):
        send_keys('{ESC}')
        sleep(0.3)
    sleep(2)

    # Lấy đường dẫn JSX
    jsx_path = get_jsx_path()
    print(f"[control.py] Đường dẫn JSX: {jsx_path}")

    # Focus vào Premiere
    focus_premiere()
    sleep(1)

    # Chạy JSX qua menu File > Scripts > Run Script (KHÔNG CẦN VSCODE!)
    # Premiere Pro: File menu -> Scripts -> Run Script...
    print("[control.py] Đang chạy JSX script qua Premiere menu...")

    # Mở File menu
    send_keys('%f')  # Alt+F
    sleep(0.5)

    # Di chuyển đến Scripts (thường là mục thứ mấy trong menu, dùng phím tắt 's')
    # Hoặc dùng mũi tên xuống nhiều lần
    for _ in range(15):  # Di chuyển xuống để tìm Scripts
        send_keys('{DOWN}')
        sleep(0.1)

    # Nhấn Enter hoặc Right để vào submenu Scripts
    send_keys('{RIGHT}')
    sleep(0.3)

    # Chọn "Run Script..." (thường là mục đầu tiên trong submenu)
    send_keys('{ENTER}')
    sleep(1)

    # Paste đường dẫn JSX vào dialog
    copy_paste(jsx_path)
    sleep(0.5)
    send_keys('{ENTER}')
    sleep(2)

    print("[control.py] Đã gửi lệnh chạy script. Đang chờ hoàn thành...")

    # Chờ script chạy xong
    while True:
        if not app.is_process_running():
            print("[control.py] Premiere Pro đã đóng.")
            break
        try:
            send_keys('{ENTER}')
            sleep(5)
        except Exception as e:
            print("[control.py] Script đã hoàn thành.")
            break

    print("[control.py] === HOÀN THÀNH ===")

#test
if __name__ == "__main__":
    premier_path = r"C:\Program Files\Adobe\Adobe Premiere Pro 2022\Adobe Premiere Pro.exe"
    project_path = r"C:\Users\phamp\Downloads\Copied_3638\Copied_3638\3638.prproj"
    run_premier_script(premier_path, project_path, 1)