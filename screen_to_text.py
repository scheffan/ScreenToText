import tkinter as tk
import pyautogui
import easyocr
import pyperclip
from PIL import Image
import threading


class RegionSelector:
    def __init__(self):
        # Init main window
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-alpha", 0.3)
        self.root.configure(bg="gray")
        self.root.title("ScreenToText - Select Area")

        self.canvas = tk.Canvas(self.root, cursor="cross", bg="gray")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Mouse events
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        self.rect = None
        self.start_x = self.start_y = 0

        # EasyOCR reader
        self.reader = easyocr.Reader(["en", "es"])

    def on_press(self, event):
        self.start_x, self.start_y = event.x, event.y
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, event.x, event.y,
            outline="red", width=2
        )

    def on_drag(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_release(self, event):
        end_x, end_y = event.x, event.y
        self.root.withdraw()  # hide overlay

        # Run OCR in background thread
        threading.Thread(
            target=self.process_selection,
            args=(self.start_x, self.start_y, end_x, end_y),
            daemon=True
        ).start()

    def process_selection(self, x1, y1, x2, y2):
        # Fix negative coordinates if dragging left/up
        left = min(x1, x2)
        top = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)

        # Capture screenshot
        screenshot = pyautogui.screenshot(region=(left, top, width, height))
        screenshot = screenshot.convert("RGB")

        # OCR with EasyOCR
        results = self.reader.readtext(
            pil_to_cv2(screenshot),
            detail=0
        )
        text = "\n".join(results)

        # Copy to clipboard
        pyperclip.copy(text)

        print("\n===== Extracted Text =====\n")
        print(text)
        print("\nCopied to clipboard ✔")

        self.root.quit()

    def run(self):
        self.root.mainloop()


def pil_to_cv2(img):
    """EasyOCR expects numpy array BGR (OpenCV format)."""
    import numpy as np
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


# Import cv2 inside function to avoid Windows startup issues
import cv2

if __name__ == "__main__":
    selector = RegionSelector()
    selector.run()
