from threading import Thread
import cv2
import time

class VideoWriterWidget(object):
    def __init__(self, video_file_name, src=0):
        # Create a VideoCapture object
        self.frame_name = str(src)
        self.video_file = video_file_name
        self.video_file_name = video_file_name + '.avi'
        self.capture = cv2.VideoCapture(src)

        # Default resolutions of the frame are obtained (system dependent)
        self.frame_width = int(self.capture.get(3))
        self.frame_height = int(self.capture.get(4))

        # Set up codec and output video settings
        self.codec = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
        self.output_video = cv2.VideoWriter(self.video_file_name, self.codec, 25, (self.frame_width, self.frame_height))

        # Track start time
        self.start_time = time.time()

        # Start the thread to read frames from the video stream
        self.thread = Thread(target=self.update, args=())
        self.thread.daemon = True
        self.thread.start()
        
        # Start recording
        self.start_recording()
        print('Initialized {}'.format(self.video_file))

    def update(self):
        # Read the next frame from the stream in a different thread
        while True:
            if self.capture.isOpened():
                (self.status, self.frame) = self.capture.read()
            if time.time() - self.start_time > 60:  # Stop recording after 60 seconds
                self.stop_recording()
                break

    def show_frame(self):
        # Display frames in main program
        if self.status:
            cv2.imshow(self.frame_name, self.frame)

        # Press Q on keyboard to stop recording
        key = cv2.waitKey(1)
        if key == ord('q'):
            self.stop_recording()
            cv2.destroyAllWindows()
            exit(1)

    def save_frame(self):
        # Save obtained frame into video output file
        if self.status:
            self.output_video.write(self.frame)
    
    def start_recording(self):
        # Create another thread to show/save frames
        def start_recording_thread():
            while True:
                try:
                    self.show_frame()
                    self.save_frame()
                    if time.time() - self.start_time > 60:  # Stop recording after 60 seconds
                        self.stop_recording()
                        break
                except AttributeError:
                    pass
        self.recording_thread = Thread(target=start_recording_thread, args=())
        self.recording_thread.daemon = True
        self.recording_thread.start()

    def stop_recording(self):
        # Release resources
        self.capture.release()
        self.output_video.release()
        print(f"Stopped recording and saved to {self.video_file_name}")

if __name__ == '__main__':
    src1 = 'rtsp://admin:WeCrunch1@192.168.0.36/stream'
    video_writer_widget1 = VideoWriterWidget('Camera 1', src1)

    # Since each video player is in its own thread, we need to keep the main thread alive.
    # Keep spinning using time.sleep() so the background threads keep running
    # Threads are set to daemon=True so they will automatically die 
    # when the main thread dies
    while True:
        time.sleep(5)