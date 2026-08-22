import os
import threading
import tkinter as tk
import webview
from PIL import Image, ImageTk

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SPLASH_IMAGE = os.path.join(SCRIPT_DIR, "LoyalBear.png")


def main():
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

    model_ok = [False]

    def _status(msg):
        status_var.set(msg)
        root.update_idletasks()

    def _load():
        from src.gui import load_model_on_startup
        _status("Loading pipeline...")
        model_ok[0] = load_model_on_startup()
        root.after(0, root.destroy)

    threading.Thread(target=_load, daemon=True).start()
    root.mainloop()

    if not model_ok[0]:
        return

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
    main()
