import io
import os
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
import requests

class PiScannerGUI(tk.Tk):
    # connecting to the Pi
    PI_HOST = "192.168.137.32" # Pi's IP
    STREAM_INTERVAL_MS = 50

    def __init__(self):
        super().__init__()
        self.title("Raspberry Pi Document Scanner")
        self.geometry("400x640")
        self.last_image = None
        self.pages = [] # collected pages for PDF
        self.streaming = False

        # show Pi connection status
        self.hello_var = tk.StringVar(value="Connecting to Pi...")
        tk.Label(self, textvariable=self.hello_var, font=(None, 12, 'bold')).pack(pady=(10, 0))

        self._build_widgets()
        self.ping_pi() # check Pi connection
        self.start_stream() # start preview stream

    def _build_widgets(self):
        # main preview area
        preview_container = tk.Frame(
            self, width=360, height=480, relief="groove", bd=2, bg="black"
        )
        preview_container.pack(pady=10)
        preview_container.pack_propagate(False)

        self.preview = tk.Label(preview_container, bg="black")
        self.preview.pack(fill="both", expand=True)

        # button container
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=5)

        # action buttons
        self.btn_capture = tk.Button(btn_frame, text="📸 Capture", command=self.capture)
        self.btn_download = tk.Button(btn_frame, text="💾 Download", command=self.download)
        self.btn_save_pdf = tk.Button(btn_frame, text="📄 Save PDF", command=self.save_pdf)

        for btn in [self.btn_capture, self.btn_download, self.btn_save_pdf]:
            btn.pack(side="left", padx=4)

        # lower status bar
        self.status = tk.StringVar(value="Ready")
        tk.Label(self, textvariable=self.status).pack(pady=6)

    def start_stream(self):
        # start preview stream if not already running
        if not self.streaming:
            self.streaming = True
            self.stream_preview()

    def stop_stream(self):
        # stop preview stream
        self.streaming = False

    def stream_preview(self):
        # continuously fetch and display preview frames
        if not self.streaming:
            return
        try:
            # get latest preview frame from Pi
            r = requests.get(f"http://{self.PI_HOST}:5000/preview", timeout=1)
            r.raise_for_status()
            img = Image.open(io.BytesIO(r.content))
            # scale image to fit preview area
            container = self.preview.master
            container.update_idletasks()
            max_w, max_h = container.winfo_width(), container.winfo_height()
            img.thumbnail((max_w, max_h), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.preview.config(image=photo)
            self.preview.image = photo
        except Exception:
            pass
        finally:
            # schedule next frame
            self.after(self.STREAM_INTERVAL_MS, self.stream_preview)

    def ping_pi(self):
        # check if Pi is online and responding
        try:
            r = requests.get(f"http://{self.PI_HOST}:5000/", timeout=3)
            r.raise_for_status()
            msg = r.json().get("message", "")
            self.hello_var.set(f"Pi: {msg}")
        except Exception:
            self.hello_var.set("Pi unreachable")

    def capture(self):
        # take a high-quality photo
        self.stop_stream()
        try:
            # request full resolution capture from Pi
            r = requests.get(f"http://{self.PI_HOST}:5000/capture", timeout=5)
            r.raise_for_status()
            orig = Image.open(io.BytesIO(r.content))
            self.last_image = orig.copy()
            # add to PDF pages
            self.pages.append(self.last_image.copy())
            self.status.set(f"Captured page {len(self.pages)}")

            # show thumbnail preview
            container = self.preview.master
            container.update_idletasks()
            max_w, max_h = container.winfo_width(), container.winfo_height()
            thumb = orig.copy()
            thumb.thumbnail((max_w, max_h), Image.LANCZOS)
            photo = ImageTk.PhotoImage(thumb)
            self.preview.config(image=photo)
            self.preview.image = photo
        except Exception as e:
            self.status.set("Capture failed")
            messagebox.showerror("Capture", str(e))
        finally:
            self.start_stream()

    def download(self):
        # save last captured image to a file
        if not self.last_image:
            messagebox.showerror("Download", "No image to save. Capture first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".jpg",
            filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png"), ("All", "*.*")],
            initialdir=os.path.expanduser("~/Desktop"),
            title="Save Image As"
        )
        if path:
            try:
                self.last_image.save(path)
                self.status.set(f"Saved to {path}")
            except Exception as e:
                messagebox.showerror("Save Error", str(e))

    def save_pdf(self):
        # combine all captured pages into PDF
        if not self.pages:
            messagebox.showerror("Save PDF", "No pages captured.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialdir=os.path.expanduser("~/Desktop"),
            title="Save PDF"
        )
        if path:
            try:
                # save first page and append the rest
                first, rest = self.pages[0], self.pages[1:]
                first.save(path, "PDF", save_all=True, append_images=rest, resolution=100.0)
                self.status.set(f"PDF saved to {path}")
                # clear pages after successful save
                self.pages.clear()
            except Exception as e:
                messagebox.showerror("PDF Error", str(e))

if __name__ == "__main__":
    PiScannerGUI().mainloop()
