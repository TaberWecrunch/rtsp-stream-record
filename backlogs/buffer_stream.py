"""
Created on Sun Apr 06 2019

@author: Chayatorn Supataragul
"""
# OpenCV Python script to buffer the video stream

# import libraries of python OpenCV as cv2
import cv2
import sys
import threading
import queue

# == Start Initialization ==
frame_buffer_size = 5 # The queue size for keeping video frame for processing. Cannot less than 2

# Capture frames from the ip camera
fn = "rtsp://admin:WeCrunch1@192.168.0.36/"

# Set capture device from fn
cap = cv2.VideoCapture(fn)

# The queue for keeping video frame for processing
frame_buffer = queue.Queue(maxsize=frame_buffer_size)

# == End Initialization ==

# De-allocate any associated memory usage and exit the program
def deallocateAndExit():
    # De-allocate any associated memory usage
    cap.release()# release camera
    cv2.destroyAllWindows()# release screen
    sys.exit() # exit program

# This is a thread function to keep reading frames and put the frames into frame_buffer for preventing lag of frames reading.
def rtsp_read_buffer():
    # ret will be False when cap.read() timeout or error
    ret = True
    while (ret):
        # If frame_buffer queue is full, get the first queue element out of the queue
        if frame_buffer.full():
            frame_buffer.get()
        # Read frame-by-frame
        # capturing each frame
        ret, buffer_frame = cap.read()
        # Put the capturing frame to the queue
        frame_buffer.put(buffer_frame)
    # Exit program
    deallocateAndExit()


# Main function to start the program
def main():

    # Create a named window and resize it
    cv2.namedWindow('Frame out', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Frame out', 640, 480)

    # Start thread function to continue its task parallelly
    threading.Thread(target=rtsp_read_buffer, daemon=True).start()
    
    # Check if cv2.VideoCapture(fn) is open
    while cap.isOpened():

        # Check if frame_buffer queue has frames waiting to process
        if not frame_buffer.empty():

            # Get a frame from the frame_buffer queue
            frame = frame_buffer.get()

            # Resize the frame to 640x480
            frame_out = cv2.resize(frame, (640, 480))

            # Display the resized video frame
            cv2.imshow('Frame out', frame_out)

            # Terminate program if user presses 'q' or 'ESC'
            if cv2.waitKey(33) & 0xFF in (ord('q'), 27):
                break

    # Exit program
    deallocateAndExit()

# start process
if __name__ == '__main__':
    main()

# Main.py 
# import cv2
# import tkinter as tk
# from tkinter import messagebox
# import threading
# import os
# from datetime import datetime, timedelta
# from PIL import Image, ImageTk
# import queue
# import sys
# import time

# class CameraApp:
#     def __init__(self, root, camera_urls):
#         self.root = root
#         self.root.title("Hikvision Camera Stream")
#         self.camera_urls = camera_urls
#         os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;tcp'
#         self.captures = [cv2.VideoCapture(url, cv2.CAP_FFMPEG) for url in camera_urls]
#         self.recording = False
#         self.output_dir = os.path.join(os.getcwd(), "recordings")
#         os.makedirs(self.output_dir, exist_ok=True)
#         self.video_label_width = 640
#         self.video_label_height = 480
#         self.video_writers = [None, None]
#         self.frames = [None, None]
#         self.chunk_start_times = [None, None]
#         self.chunk_duration = timedelta(minutes=1)  # Chunk duration
#         self.chunk_indices = [0, 0]  # To keep track of chunk files
#         self.frame_buffers = [queue.Queue(maxsize=5) for _ in range(2)]  # Frame buffers

#         for capture in self.captures:
#             if not capture.isOpened():
#                 print('Cannot open RTSP stream. Possibly the URL/video is broken')
#                 exit(-1)

#         self.create_widgets()
#         self.start_stream_threads()
#         self.start_recording()  # Start recording automatically

#     def create_widgets(self):
#         self.video_frames = []
#         self.video_labels = []

#         for i in range(2):
#             video_frame = tk.Frame(self.root, width=self.video_label_width, height=self.video_label_height, bg="black")
#             video_frame.grid(row=0, column=i, padx=5, pady=5)
#             self.video_frames.append(video_frame)

#             video_label = tk.Label(video_frame, width=self.video_label_width, height=self.video_label_height)
#             video_label.pack()
#             self.video_labels.append(video_label)

#         self.toggle_button = tk.Button(self.root, text="Stop Recording", command=self.toggle_recording)
#         self.toggle_button.grid(row=1, column=0, columnspan=2, padx=5, pady=5)

#         self.update_video_stream()

#     def update_video_stream(self):
#         for i in range(2):
#             if not self.frame_buffers[i].empty():
#                 frame = self.frame_buffers[i].get()
#                 self.frames[i] = frame
#                 frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#                 frame = cv2.resize(frame, (self.video_label_width, self.video_label_height))
#                 img = Image.fromarray(frame)
#                 imgtk = ImageTk.PhotoImage(image=img)
#                 self.video_labels[i].imgtk = imgtk
#                 self.video_labels[i].configure(image=imgtk)

#         self.root.after(10, self.update_video_stream)

#     def toggle_recording(self):
#         if self.recording:
#             self.stop_recording()
#         else:
#             self.start_recording()

#     def start_recording(self):
#         if not self.recording:
#             self.recording = True
#             self.chunk_indices = [0, 0]  # Reset chunk indices
#             self.chunk_start_times = [datetime.now()] * 2  # Initialize chunk start times
#             for video_frame in self.video_frames:
#                 video_frame.config(highlightbackground="red", highlightcolor="red", highlightthickness=2)
#             self.toggle_button.config(text="Stop Recording")
#             self.start_time = self.chunk_start_times[0]  # Start time for naming chunks

#             for i, capture in enumerate(self.captures):
#                 self.start_new_chunk(i)

#             self.recording_thread = threading.Thread(target=self.record_video)
#             self.recording_thread.start()

#     def start_new_chunk(self, i):
#         camera_name = f"camera{i+1}"
#         video_filename = f"{camera_name}_{self.chunk_start_times[i].strftime('%Y%m%d_%H%M%S')}_{self.chunk_indices[i]}.mp4"
#         video_path = os.path.join(self.output_dir, video_filename)
#         frame_width = int(self.captures[i].get(3))
#         frame_height = int(self.captures[i].get(4))
#         fps = 20
#         video_codec = cv2.VideoWriter_fourcc(*'mp4v')
#         self.video_writers[i] = cv2.VideoWriter(video_path, video_codec, fps, (frame_width, frame_height))
#         self.chunk_start_times[i] = datetime.now()  # Reset chunk start time

#     def record_video(self):
#         while self.recording:
#             current_time = datetime.now()
#             for i, frame in enumerate(self.frames):
#                 if frame is not None:
#                     elapsed_time = current_time - self.chunk_start_times[i]

#                     if elapsed_time >= self.chunk_duration:
#                         self.video_writers[i].release()
#                         self.chunk_indices[i] += 1
#                         self.start_new_chunk(i)
#                         self.chunk_start_times[i] = datetime.now()  # Reset chunk start time after starting new chunk

#                     self.video_writers[i].write(frame)

#             # Sleep for a short duration to prevent high CPU usage
#             time.sleep(0.01)

#         for writer in self.video_writers:
#             writer.release()

#     def stop_recording(self):
#         if self.recording:
#             self.recording = False
#             self.recording_thread.join()

#             for video_frame in self.video_frames:
#                 video_frame.config(highlightbackground="black", highlightcolor="black", highlightthickness=0)
#             self.toggle_button.config(text="Start Recording")
#             messagebox.showinfo("Recording", "Recording stopped and saved.")

#     def stream_camera(self, i):
#         while True:
#             ret, frame = self.captures[i].read()
#             if ret:
#                 if self.frame_buffers[i].full():
#                     self.frame_buffers[i].get()
#                 self.frame_buffers[i].put(frame)
#             else:
#                 print(f"Failed to grab frame from camera {i+1}")
#                 break

#     def start_stream_threads(self):
#         for i in range(2):
#             threading.Thread(target=self.stream_camera, args=(i,), daemon=True).start()

# def main():
#     camera_urls = [
#         'rtsp://admin:WeCrunch1@192.168.0.36/',  # Replace with your camera URLs
#         'rtsp://admin:WeCrunch1@192.168.0.36/'
#     ]
#     root = tk.Tk()
#     app = CameraApp(root, camera_urls)
#     root.mainloop()

# if __name__ == "__main__":
#     main()