import os
import logging
from datetime import datetime

class Logger:
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        self.current_log_file = None
        self.logger = None
        self.current_date = None
        self.camera_connected = {}  # To track initial connection
        self.start_new_log()

    def start_new_log(self):
        current_date = datetime.now().date()
        if self.current_date != current_date:
            self.current_date = current_date
            date_str = current_date.strftime("%Y%m%d")
            self.current_log_file = os.path.join(self.log_dir, f"camera_log_{date_str}.log")
            
            if self.logger:
                for handler in self.logger.handlers[:]:
                    self.logger.removeHandler(handler)
            else:
                self.logger = logging.getLogger(__name__)
            
            self.logger.setLevel(logging.INFO)
            file_handler = logging.FileHandler(self.current_log_file)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def log(self, message, level=logging.INFO):
        self.start_new_log()
        self.logger.log(level, message)

    def log_recording_start(self):
        self.log("Recording started")

    def log_recording_stop(self):
        self.log("Recording stopped")

    def log_file_start(self, camera_name, file_name):
        self.log(f"Started recording file: {file_name} for camera {camera_name}")

    def log_file_save(self, camera_name, file_name):
        self.log(f"Saved recording file: {file_name} for camera {camera_name}")

    def log_camera_disconnect(self, camera_name):
        self.log(f"Camera {camera_name} disconnected", logging.WARNING)
        self.camera_connected[camera_name] = False

    def log_camera_connect(self, camera_name):
        if camera_name not in self.camera_connected or not self.camera_connected[camera_name]:
            self.log(f"Camera {camera_name} connected")
        else:
            self.log(f"Camera {camera_name} reconnected")
        self.camera_connected[camera_name] = True

    def log_error(self, error_message, camera_name=None):
        if camera_name:
            self.log(f"Error occurred for camera {camera_name}: {error_message}", logging.ERROR)
        else:
            self.log(f"Error occurred: {error_message}", logging.ERROR)

    def log_reconnection_attempt(self, camera_name):
        self.log(f"Attempting to reconnect camera {camera_name}")