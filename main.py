import os
import sys
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON = os.path.join(SCRIPT_DIR, ".venv", "Scripts", "python.exe")
SPLASH_IMAGE = os.path.join(SCRIPT_DIR, "LoyalBear.png")


def _bootstrap():
    """Create venv + install deps if needed, then relaunch under the venv Python."""
    if not os.path.isfile(VENV_PYTHON):
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", ".venv"], cwd=SCRIPT_DIR, check=True)
        print("Installing torch - CPU (this may take a few minutes)...")
        subprocess.run(
            [VENV_PYTHON, "-m", "pip", "install", "--isolated",
             "--index-url", "https://pypi.org/simple", "torch", "torchvision"],
            cwd=SCRIPT_DIR, check=True,
        )
        print("Installing dependencies...")
        subprocess.run(
            [VENV_PYTHON, "-m", "pip", "install", "--isolated",
             "--index-url", "https://pypi.org/simple",
             "-r", os.path.join(SCRIPT_DIR, "requirements.txt")],
            cwd=SCRIPT_DIR, check=True,
        )

    if sys.executable.lower() != VENV_PYTHON.lower():
        print("Relaunching with venv Python...")
        os.execv(VENV_PYTHON, [VENV_PYTHON, os.path.abspath(__file__)])


def _show_splash_and_wait():
    """Show the splash with status text; returns True if model loaded OK."""
    import threading
    import tkinter as tk
    from PIL import Image, ImageTk

    root = tk.Tk()
    root.overrideredirect(True)
    root.configure(bg="#0d0d1a")
    root.attributes("-topmost", True)

    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()

    try:
        pil_img = Image.open(SPLASH_IMAGE)
        ratio = min(screen_w * 0.5 / pil_img.width, screen_h * 0.5 / pil_img.height, 1.0)
        new_w = int(pil_img.width * ratio)
        new_h = int(pil_img.height * ratio)
        pil_img = pil_img.resize((new_w, new_h), Image.LANCZOS)
        tk_img = ImageTk.PhotoImage(pil_img)
    except Exception:
        tk_img = None
        new_w, new_h = 200, 200

    img_label = tk.Label(root, image=tk_img, bg="#0d0d1a")
    img_label.image = tk_img
    img_label.pack(pady=(40, 10))

    status_var = tk.StringVar(value="Loading Components")
    status_label = tk.Label(
        root, textvariable=status_var, fg="#a78bfa", bg="#0d0d1a",
        font=("Segoe UI", 11), justify="left",
    )
    status_label.pack(pady=(0, 30))

    win_w = max(new_w + 60, 350)
    win_h = new_h + 150
    x = (screen_w - win_w) // 2
    y = (screen_h - win_h) // 2
    root.geometry(f"{win_w}x{win_h}+{x}+{y}")

    result = {"ok": False, "error": ""}

    def _status(msg):
        status_var.set(msg)
        root.update_idletasks()

    def _load():
        try:
            from src.gui import load_model_on_startup
            _status("Loading pipeline...")
            result["ok"] = load_model_on_startup()
            if not result["ok"]:
                result["error"] = "Model failed to load"
        except Exception as e:
            result["ok"] = False
            result["error"] = str(e)
        root.after(0, root.destroy)

    threading.Thread(target=_load, daemon=True).start()
    root.mainloop()
    return result["ok"], result["error"]


def main():
    ok, error = _show_splash_and_wait()
    if not ok:
        print(f"Failed to load model: {error}")
        input("Press Enter to exit...")
        return

    import webview

    from src.gui import build_ui, THEME, CSS

    demo = build_ui()
    _, url, _ = demo.launch(
        server_name="127.0.0.1",
        share=False,
        inbrowser=False,
        prevent_thread_lock=True,
        theme=THEME,
        css=CSS,
    )

    webview.create_window("Loyal Bear – The SynthID Scrambler", url, width=1280, height=900)
    webview.start()


if __name__ == "__main__":
    _bootstrap()
    main()
