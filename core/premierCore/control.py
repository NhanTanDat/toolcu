# core/premierCore/control.py
from __future__ import annotations

import os
import sys
import subprocess
from time import sleep
from pathlib import Path
from typing import Optional, List

# =========================
# OPTIONAL IMPORTS
# =========================
try:
    from pywinauto import Application, Desktop
    from pywinauto.keyboard import send_keys
    _HAS_PYWINAUTO = True
except ImportError:
    Application = None
    Desktop = None
    _HAS_PYWINAUTO = False

    def send_keys(keys, **kwargs):  # type: ignore
        pass


try:
    import pyperclip
    _HAS_PYPERCLIP = True
except ImportError:
    _HAS_PYPERCLIP = False

    class pyperclip:  # type: ignore
        @staticmethod
        def copy(text: str):
            pass


# =========================
# CONFIG
# =========================
APP_NAME = "autotool"
PREMIERE_WINDOW_KEYWORD = "Adobe Premiere Pro"
VSCODE_WINDOW_KEYWORD = "Visual Studio Code"

FORCE_PREMIERE_EXE = r"C:\Program Files\Adobe\Adobe Premiere Pro 2022\Adobe Premiere Pro.exe"

DEFAULT_STARTUP_WAIT_SEC = 10
PROJECT_LOAD_WAIT_SEC = 10
VSCODE_START_WAIT_SEC = 3


# =========================
# PRINT / DEBUG
# =========================
def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _print_header(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def dump_runtime_info() -> None:
    _print_header("RUNTIME INFO")
    print("frozen:", getattr(sys, "frozen", False))
    print("sys.executable:", sys.executable)
    print("cwd:", os.getcwd())
    print("__file__:", __file__)
    print("_MEIPASS:", getattr(sys, "_MEIPASS", None))
    print("PROGRAMFILES:", os.environ.get("PROGRAMFILES"))
    print("PROGRAMFILES(X86):", os.environ.get("PROGRAMFILES(X86)"))
    print("LOCALAPPDATA:", os.environ.get("LOCALAPPDATA"))
    print("APPDATA:", os.environ.get("APPDATA"))


# =========================
# PATH HELPERS
# =========================
def clean_path_input(p: str) -> str:
    s = str(p).strip()
    s = s.strip("“”")
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        s = s[1:-1].strip()
    s = os.path.expandvars(os.path.expanduser(s))
    s = s.replace("/", "\\")
    return s


def abs_path(p: str) -> str:
    s = clean_path_input(p)
    pp = Path(s)
    if not pp.is_absolute():
        pp = (Path.cwd() / pp).resolve(strict=False)
    else:
        pp = pp.resolve(strict=False)
    return str(pp)


def exe_dir() -> Path:
    return Path(sys.executable).resolve().parent


def internal_dir_if_any() -> Path:
    # onedir: dist/app/_internal
    return exe_dir() / "_internal"


def bundled_meipass_if_any() -> Optional[Path]:
    p = getattr(sys, "_MEIPASS", None)
    return Path(p) if p else None


def project_root_from_source() -> Path:
    # core/premierCore/control.py -> parents[2] = project root
    return Path(__file__).resolve().parents[2]


# =========================
# RESOLVE PREMIERE
# =========================
def resolve_premiere_exe(premier_path: Optional[str]) -> str:
    _print_header("RESOLVE PREMIERE EXE (FORCE 2022)")

    forced = Path(FORCE_PREMIERE_EXE)
    print("[forced] ", forced, "=>", "EXISTS" if forced.exists() else "MISSING")
    if forced.exists():
        print("=> CHOSEN (forced):", forced.resolve())
        return str(forced.resolve())

    if premier_path:
        p0 = Path(clean_path_input(premier_path))
        print("[given]  ", p0, "=>", "EXISTS" if p0.exists() else "MISSING")
        if p0.exists():
            print("=> CHOSEN (given):", p0.resolve())
            return str(p0.resolve())

    raise FileNotFoundError("Không tìm thấy Premiere 2022. Hãy cài hoặc sửa FORCE_PREMIERE_EXE.")


# =========================
# RESOLVE JSX PATH (runAll.jsx)
# =========================
def resolve_premiercore_dir() -> Path:
    _print_header("RESOLVE premierCore DIR")
    candidates: List[Path] = []

    if _is_frozen():
        # khi chạy exe: ưu tiên _internal
        candidates.append(exe_dir() / "core" / "premierCore")
        candidates.append(internal_dir_if_any() / "core" / "premierCore")
        mp = bundled_meipass_if_any()
        if mp:
            candidates.append(mp / "core" / "premierCore")

    # khi chạy source:
    candidates.append(project_root_from_source() / "core" / "premierCore")

    print("\n[premierCore] Candidates:")
    for p in candidates:
        print("  -", p, "=>", "EXISTS" if p.exists() else "MISSING")

    for p in candidates:
        if p.exists():
            print("=> CHOSEN:", p.resolve())
            return p.resolve()

    raise FileNotFoundError("Không tìm thấy thư mục core/premierCore.")


def resolve_jsx_path(name: str = "runAll.jsx") -> str:
    _print_header(f"RESOLVE JSX: {name}")
    premiercore = resolve_premiercore_dir()
    jsx = (premiercore / name).resolve()
    print("JSX PATH =", jsx, "=>", "EXISTS" if jsx.exists() else "MISSING")

    print("\n[JSX LIST] Found .jsx files:")
    try:
        for f in sorted(premiercore.glob("*.jsx")):
            print("  -", f.name, "=>", "EXISTS" if f.exists() else "MISSING")
    except Exception as e:
        print("  (list jsx error)", e)

    if not jsx.exists():
        raise FileNotFoundError(f"Không thấy JSX file: {jsx}")
    return str(jsx)


# =========================
# RESOLVE DATA ROOT + path.txt
# =========================
def resolve_data_root() -> Path:
    _print_header("RESOLVE DATA ROOT")
    la = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or str(Path.home())
    preferred = Path(la) / APP_NAME / "data"
    preferred.mkdir(parents=True, exist_ok=True)
    print("=> CHOSEN (writable):", preferred.resolve())
    return preferred.resolve()


def resolve_path_txt() -> Path:
    path_txt = (resolve_data_root() / "path.txt").resolve()
    print("[path.txt] =", path_txt)
    return path_txt


def update_path_txt_for_data_folder(data_folder_abs: str) -> None:
    _print_header("UPDATE path.txt")
    path_txt = resolve_path_txt()
    content = f"data_folder={data_folder_abs}\n"
    print("Write content:", content.strip())
    with open(path_txt, "w", encoding="utf-8") as f:
        f.write(content)
    print("=> WROTE:", path_txt, "size=", path_txt.stat().st_size)


# =========================
# CLIPBOARD / INPUT
# =========================
def _copy_to_clipboard(text: str) -> bool:
    if not _HAS_PYPERCLIP:
        return False
    try:
        pyperclip.copy(text)
        return True
    except Exception:
        return False


def paste_text(text: str) -> None:
    ok = _copy_to_clipboard(text)
    if ok:
        send_keys("^v")
    else:
        # fallback gõ từng ký tự
        for ch in text:
            if ch == " ":
                send_keys("{SPACE}")
            else:
                send_keys(ch)
            sleep(0.01)


# =========================
# WINDOW HELPERS
# =========================
def focus_window_contains(keyword: str) -> bool:
    for w in Desktop(backend="uia").windows():
        t = (w.window_text() or "").lower()
        if keyword.lower() in t:
            try:
                w.set_focus()
                return True
            except Exception:
                pass
    return False


def connect_or_start_premiere(premiere_exe: str):
    for w in Desktop(backend="uia").windows():
        if PREMIERE_WINDOW_KEYWORD.lower() in (w.window_text() or "").lower():
            app = Application(backend="uia").connect(title_re=r".*Adobe Premiere Pro.*")
            try:
                w.set_focus()
            except Exception:
                pass
            return app

    return Application(backend="uia").start(f'"{premiere_exe}"')


# =========================
# RESOLVE VS CODE
# =========================
def resolve_vscode_exe() -> str:
    _print_header("RESOLVE VS CODE EXE")

    candidates: List[Path] = []

    la = os.environ.get("LOCALAPPDATA")
    if la:
        candidates.append(Path(la) / "Programs" / "Microsoft VS Code" / "Code.exe")
        candidates.append(Path(la) / "Programs" / "Microsoft VS Code Insiders" / "Code - Insiders.exe")

    pf = os.environ.get("PROGRAMFILES")
    if pf:
        candidates.append(Path(pf) / "Microsoft VS Code" / "Code.exe")

    pfx86 = os.environ.get("PROGRAMFILES(X86)")
    if pfx86:
        candidates.append(Path(pfx86) / "Microsoft VS Code" / "Code.exe")

    # fallback: người dùng add vào PATH (code.cmd)
    print("[VSCode] Candidates:")
    for p in candidates:
        print("  -", p, "=>", "EXISTS" if p.exists() else "MISSING")

    for p in candidates:
        if p.exists():
            print("=> CHOSEN:", p.resolve())
            return str(p.resolve())

    # thử PATH
    for name in ["code.cmd", "code.exe", "code"]:
        if shutil_which(name):
            print("=> CHOSEN (PATH):", name)
            return name

    raise FileNotFoundError(
        "Không tìm thấy VS Code.\n"
        "=> Cần cài Visual Studio Code + ExtendScript Debugger extension."
    )


def shutil_which(cmd: str) -> Optional[str]:
    # tránh import shutil (để hạn chế), implement nhanh
    exts = os.environ.get("PATHEXT", "").split(";")
    paths = os.environ.get("PATH", "").split(";")
    for d in paths:
        d = d.strip()
        if not d:
            continue
        c = Path(d) / cmd
        if c.exists():
            return str(c)
        for e in exts:
            e = e.strip()
            if not e:
                continue
            c2 = Path(d) / (cmd + e)
            if c2.exists():
                return str(c2)
    return None


# =========================
# RUN JSX VIA VS CODE (EXTENDSCRIPT DEBUGGER)
# =========================
def open_vscode_to_file(vscode_exe: str, file_path: str) -> None:
    _print_header("OPEN VS CODE TO JSX FILE")
    print("VSCode exe:", vscode_exe)
    print("Open file :", file_path)

    # mở VSCode (reuse-window) và mở file luôn
    try:
        subprocess.Popen([vscode_exe, "--reuse-window", file_path], shell=False)
    except Exception:
        # fallback string command
        subprocess.Popen(f'"{vscode_exe}" --reuse-window "{file_path}"', shell=True)

    sleep(VSCODE_START_WAIT_SEC)

    # focus VS Code
    if not focus_window_contains(VSCODE_WINDOW_KEYWORD):
        # đôi khi title không chứa đúng keyword, thử focus nhiều lần
        for _ in range(10):
            sleep(0.5)
            if focus_window_contains(VSCODE_WINDOW_KEYWORD):
                break


def vscode_run_extendscript_evaluate(host_name: str = "Adobe Premiere Pro 2022") -> None:
    """
    VS Code:
      Ctrl+Shift+P
      gõ: ExtendScript: Evaluate Script in Attached Host
      Enter
      chọn host: Adobe Premiere Pro 2022
      Enter
    """
    _print_header("VS CODE: EVALUATE EXTENDSCRIPT")
    if not focus_window_contains(VSCODE_WINDOW_KEYWORD):
        print("[warn] Không focus được VS Code, vẫn thử send_keys...")

    # Command Palette
    send_keys("^+p")
    sleep(0.8)

    paste_text("ExtendScript: Evaluate Script in Attached Host")
    sleep(0.3)
    send_keys("{ENTER}")
    sleep(0.8)

    paste_text(host_name)
    sleep(0.3)
    send_keys("{ENTER}")
    sleep(0.5)

    print("=> Sent Evaluate command to VS Code.")


# =========================
# MAIN
# =========================
def run_premier_script(premier_path: Optional[str], project_path: str, idx: int) -> None:
    if not _HAS_PYWINAUTO:
        raise RuntimeError("Thiếu pywinauto trong build. Hãy đảm bảo pywinauto nằm trong requirements/spec.")

    dump_runtime_info()

    # nếu chạy exe, set cwd về exe_dir để relative path không bị lệch
    if _is_frozen():
        try:
            os.chdir(str(exe_dir()))
        except Exception:
            pass

    premiere_exe = resolve_premiere_exe(premier_path)
    jsx_path = resolve_jsx_path("runAll.jsx")

    _print_header("PROJECT PATH INFO")
    project_abs = abs_path(project_path)
    print("project_path input:", project_path)
    print("project_path abs  :", project_abs)
    print("project exists   :", os.path.exists(project_abs))

    if not os.path.exists(project_abs):
        raise FileNotFoundError("Project .prproj không tồn tại (đang sai path hoặc dính quotes).")

    data_folder_abs = str(Path(project_abs).parent.resolve())
    update_path_txt_for_data_folder(data_folder_abs)

    _print_header("START PREMIERE AUTOMATION")
    print("Premiere exe:", premiere_exe)
    print("JSX path    :", jsx_path)
    print("Data folder :", data_folder_abs)

    # kill premiere cũ
    os.system('taskkill /IM "Adobe Premiere Pro.exe" /F 2>nul')
    sleep(2)

    # start premiere
    app = connect_or_start_premiere(premiere_exe)
    sleep(DEFAULT_STARTUP_WAIT_SEC)

    if not focus_window_contains(PREMIERE_WINDOW_KEYWORD):
        raise RuntimeError("Không focus được cửa sổ Premiere.")

    # open project
    print("[action] Ctrl+O open project")
    send_keys("^o")
    sleep(2)
    paste_text(project_abs)
    send_keys("{ENTER}")
    sleep(PROJECT_LOAD_WAIT_SEC)

    # dọn popup
    for _ in range(12):
        send_keys("{ESC}")
        sleep(0.15)
    sleep(1)

    # RUN JSX via VS Code (vì Premiere 2022 KHÔNG có File > Scripts)
    vscode_exe = resolve_vscode_exe()
    open_vscode_to_file(vscode_exe, jsx_path)
    vscode_run_extendscript_evaluate("Adobe Premiere Pro 2022")

    _print_header("WAITING...")
    max_wait_sec = 60 * 30
    waited = 0
    while waited < max_wait_sec:
        if not app.is_process_running():
            print("[control.py] Premiere đã tắt.")
            break
        sleep(5)
        waited += 5

    print("[control.py] === DONE ===")


if __name__ == "__main__":
    premier_path = None
    project_path = r"C:\Users\Tam\Desktop\YourProject\your.prproj"
    run_premier_script(premier_path, project_path, 1)
