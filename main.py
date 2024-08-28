import tkinter as tk
from camera_manager import CameraManager
from camera_app_ui import CameraAppUI

def main():
    # Replace with your camera URLs
    camera_urls = [
        'rtsp://admin:WeCrunch1@192.168.0.36/',
        'rtsp://admin:WeCrunch1@192.168.0.36/'
    ]
    root = tk.Tk()
    camera_manager = CameraManager(camera_urls)
    app = CameraAppUI(root, camera_manager)
    root.mainloop()

if __name__ == "__main__":
    main()