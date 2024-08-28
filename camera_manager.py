import cv2
import os
from logger import Logger
from buffer_video_writer import BufferedVideoWriter
from datetime import datetime, timedelta

class CameraManager:
    def __init__(self, camera_urls):
        self.logger = Logger()
        self.logger.log_recording_start()

        os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;tcp'
        self.camera_urls = camera_urls
        self.output_dir = os.path.join(os.getcwd(), "recordings")
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.captures = [cv2.VideoCapture(url, cv2.CAP_FFMPEG) for url in camera_urls]
        self.video_writers = [None] * len(camera_urls)
        self.frames = [None] * len(camera_urls)
        self.chunk_start_times = [None] * len(camera_urls)
        self.chunk_duration = timedelta(minutes=1)
        current_date_str = datetime.now().strftime('%Y%m%d')
        self.chunk_indices = [self.get_last_index(f"front" if i == 0 else "rear", current_date_str) for i in range(len(camera_urls))]
        self.camera_connected = [True] * len(camera_urls)

        for capture in self.captures:
            if not capture.isOpened():
                raise ValueError('Cannot open RTSP stream. Possibly the URL/video is broken')

    def get_last_index(self, camera_name, date_str):
        max_index = -1
        date_dir = os.path.join(self.output_dir, date_str)

        if not os.path.exists(date_dir):
            return 0

        for filename in os.listdir(date_dir):
            if filename.startswith(camera_name) and date_str in filename:
                try:
                    index = int(filename.split('_')[-1].split('.')[0])
                    if index > max_index:
                        max_index = index
                except (ValueError, IndexError):
                    pass

        return max_index + 1

    def start_new_chunk(self, i):
        current_date_str = datetime.now().strftime('%Y%m%d')
        date_dir = os.path.join(self.output_dir, current_date_str)
        os.makedirs(date_dir, exist_ok=True)
        
        camera_name = "front" if i == 0 else "rear"
        self.chunk_indices[i] = self.get_last_index(camera_name, current_date_str)
        video_filename = f"{camera_name}_{self.chunk_start_times[i].strftime('%Y%m%d_%H%M%S')}_{self.chunk_indices[i]}.avi"
        video_path = os.path.join(date_dir, video_filename)
        frame_width = int(self.captures[i].get(3))
        frame_height = int(self.captures[i].get(4))
        fps = int(self.captures[i].get(cv2.CAP_PROP_FPS))
        video_codec = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
        self.video_writers[i] = BufferedVideoWriter(video_path, video_codec, fps, (frame_width, frame_height))
        self.video_writers[i].start()
        self.chunk_start_times[i] = datetime.now()
        self.logger.log_file_start(camera_name, video_filename)

    def record_video(self):
        self.recording = True
        while self.recording:
            current_time = datetime.now()
            for i, frame in enumerate(self.frames):
                if frame is not None and self.camera_connected[i]:
                    elapsed_time = current_time - self.chunk_start_times[i]
                    if elapsed_time >= self.chunk_duration:
                        self.video_writers[i].stop()
                        camera_name = "front" if i == 0 else "rear"
                        self.logger.log_file_save(camera_name, os.path.basename(self.video_writers[i].filename))
                        self.chunk_indices[i] += 1
                        self.start_new_chunk(i)
                    self.video_writers[i].write(frame)

            cv2.waitKey(1)

        for writer in self.video_writers:
            if writer is not None:
                writer.stop()
        self.logger.log_recording_stop()

    def stop_recording(self):
        self.recording = False

    def release(self):
        for capture in self.captures:
            capture.release()

    def log_error(self, error_message, camera_index=None):
        camera_name = f"Camera {camera_index + 1}" if camera_index is not None else "Unknown camera"
        self.logger.log_error(error_message, camera_name)

    def handle_disconnection(self, camera_index):
        camera_name = "front" if camera_index == 0 else "rear"
        self.logger.log_camera_disconnect(f"Camera {camera_index + 1}")

        self.camera_connected[camera_index] = False

        # Stop the current recording for this camera
        if self.video_writers[camera_index] is not None:
            self.video_writers[camera_index].stop()
            self.logger.log_file_save(camera_name, os.path.basename(self.video_writers[camera_index].filename))
            self.video_writers[camera_index] = None

    def handle_reconnection(self, camera_index):
        camera_name = "front" if camera_index == 0 else "rear"
        self.logger.log_camera_connect(f"Camera {camera_index + 1}")

        self.camera_connected[camera_index] = True

        # Start a new recording chunk for this camera
        self.chunk_start_times[camera_index] = datetime.now()
        self.start_new_chunk(camera_index)

    def attempt_reconnection(self, camera_index):
        self.logger.log_reconnection_attempt(f"Camera {camera_index + 1}")
        self.captures[camera_index].release()
        self.captures[camera_index] = cv2.VideoCapture(self.camera_urls[camera_index], cv2.CAP_FFMPEG)
        if self.captures[camera_index].isOpened():
            self.handle_reconnection(camera_index)
            return True
        return False