from flask import Flask, send_file, current_app, make_response
import os
from capture import capture_still, quick_capture

app = Flask(__name__)

@app.route("/")
def root():
    # simple health check endpoint to verify Pi is online
    return {"message": "Pi is connected"}, 200

@app.route("/capture", methods=["GET"])
def capture():
    # take a high-quality photo and send it back
    dst = "/tmp/preview.jpg"
    try:
        capture_still(dst)
    except Exception as e:
        current_app.logger.error(f"Capture failed: {e}", exc_info=True)
        return {"error": "Capture failed"}, 500

    if not os.path.exists(dst):
        return {"error": "File missing"}, 500

    # send the image file with cache headers disabled to ensure fresh images
    response = send_file(dst, mimetype="image/jpeg", conditional=False)
    # disable all caching to prevent stale images
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route("/preview", methods=["GET"])
def preview():
    """
    fast, low-latency JPEG for the viewfinder,
    used for the live preview stream
    """
    try:
        jpg_bytes = quick_capture()
    except Exception as e:
        current_app.logger.error(f"Preview failed: {e}", exc_info=True)
        return {"error": "Preview failed"}, 500

    # Send raw JPEG bytes with cache disabled
    resp = make_response(jpg_bytes)
    resp.headers["Content-Type"] = "image/jpeg"
    resp.headers.update({
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0"
    })
    return resp

if __name__ == "__main__":
    # run in single-threaded mode to avoid camera access conflicts
    app.run(host="0.0.0.0", port=5000, debug=False)