from picamera2 import Picamera2
import threading
import numpy as np
import io
from PIL import Image
import time

# lock to prevent multiple processes from accessing the camera simultaneously
_camera_lock = threading.Lock()

def capture_still(output_path: str, size=(2480, 3508), quality=80):
    """
    used for high-quality captures when the user clicks the capture button,
    grabs a JPEG and write it to output_path
    """
    with _camera_lock:
        # initialize camera with high-res settings
        picam2 = Picamera2()
        config = picam2.create_preview_configuration(
            main={"size": size, "format": "RGB888"}
        )
        picam2.configure(config)
        picam2.start()
        # give camera time to auto-adjust
        time.sleep(1)
        # grab the actual frame
        array = picam2.capture_array("main")
        picam2.stop()
        picam2.close()
    # make sure the image data is in the right format for PIL
    array = np.ascontiguousarray(array)
    img = Image.fromarray(array)
    # convert to grayscale to reduce file size while maintaining readability
    img = img.convert("L")
    img.save(output_path,format="JPEG", quality=85, optimize=True)
    print(f"[capture.py] Wrote preview to {output_path}")

def quick_capture(size=(620, 877), quality=60):
    """
    fast capture for live preview - uses lower resolution and quality
    to minimize latency for the viewfinder
    """
    with _camera_lock:
        picam2 = Picamera2()
        # low-res settings for faster capture
        config = picam2.create_preview_configuration(
            main={"size": size, "format": "RGB888"}
        )
        picam2.configure(config)    
        picam2.start()
        # minimal delay to let camera stabilize
        time.sleep(0.1)
        array = picam2.capture_array("main")
        picam2.stop()
        picam2.close()
    # process image for streaming
    array = np.ascontiguousarray(array)
    img = Image.fromarray(array)
    img = img.convert("L") # convert to grayscale for smaller size
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue()
