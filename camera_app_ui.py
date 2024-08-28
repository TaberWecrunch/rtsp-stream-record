import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import threading
from datetime import datetime
import queue
import cv2
import time

class CameraAppUI:
    def __init__(self, root, camera_manager):
        self.root = root
        self.root.title("Hikvision Camera Stream")
        self.camera_manager = camera_manager
        self.logger = camera_manager.logger
        self.recording = False
        self.video_label_width = 640
        self.video_label_height = 480
        self.frame_buffers = [queue.Queue(maxsize=5) for _ in range(len(camera_manager.captures))]
        self.video_labels = []
        self.status_labels = []

        self.create_widgets()
        self.start_stream_threads()
        self.start_recording()

    def create_widgets(self):
        video_frames = []
        for i in range(len(self.camera_manager.captures)):
            # Status label
            status_label = tk.Label(self.root, text="Status: Disconnected", bg="red", fg="white")
            status_label.grid(row=0, column=i, padx=5, pady=5)
            self.status_labels.append(status_label)

            # Video frame
            video_frame = tk.Frame(self.root, width=self.video_label_width, height=self.video_label_height, bg="black")
            video_frame.grid(row=1, column=i, padx=5, pady=5)
            video_frames.append(video_frame)

            # Video label
            video_label = tk.Label(video_frame, width=self.video_label_width, height=self.video_label_height)
            video_label.pack()
            self.video_labels.append(video_label)

        self.toggle_button = tk.Button(self.root, text="Stop Recording", command=self.toggle_recording)
        self.toggle_button.grid(row=2, column=0, columnspan=len(self.camera_manager.captures), padx=5, pady=5)

        self.update_video_stream()

    def update_video_stream(self):
        for i in range(len(self.frame_buffers)):
            if not self.frame_buffers[i].empty():
                frame = self.frame_buffers[i].get()
                self.camera_manager.frames[i] = frame
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (self.video_label_width, self.video_label_height))
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_labels[i].imgtk = imgtk
                self.video_labels[i].configure(image=imgtk)
        self.root.after(10, self.update_video_stream)

    def start_recording(self):
        if not self.recording:
            self.recording = True
            for video_frame in self.video_labels:
                video_frame.master.config(highlightbackground="red", highlightcolor="red", highlightthickness=2)
            self.toggle_button.config(text="Stop Recording")
            self.camera_manager.recording = True
            self.camera_manager.chunk_indices = [0] * len(self.camera_manager.captures)
            self.camera_manager.chunk_start_times = [datetime.now()] * len(self.camera_manager.captures)

            for i in range(len(self.camera_manager.captures)):
                self.camera_manager.start_new_chunk(i)

            self.recording_thread = threading.Thread(target=self.camera_manager.record_video)
            self.recording_thread.start()

    def stop_recording(self):
        if self.recording:
            self.camera_manager.stop_recording()
            self.recording = False
            self.recording_thread.join()

            for video_frame in self.video_labels:
                video_frame.master.config(highlightbackground="black", highlightcolor="black", highlightthickness=0)
            self.toggle_button.config(text="Start Recording")
            messagebox.showinfo("Recording", "Recording stopped and saved.")

    def toggle_recording(self):
        if self.recording:
            self.stop_recording()
        else:
            self.start_recording()

    def stream_camera(self, i):
        last_frame_time = time.time()
        reconnect_delay = 5  # Delay between reconnection attempts in seconds
        camera_name = f"Camera {i+1}"

        while True:
            try:
                if not self.camera_manager.camera_connected[i]:
                    if self.camera_manager.attempt_reconnection(i):
                        last_frame_time = time.time()
                    else:
                        time.sleep(reconnect_delay)
                        continue

                ret, frame = self.camera_manager.captures[i].read()
                if ret:
                    last_frame_time = time.time()
                    if self.frame_buffers[i].full():
                        self.frame_buffers[i].get()
                    self.frame_buffers[i].put(frame)
                    if self.status_labels[i].cget("text") != "Status: Connected":
                        self.status_labels[i].config(text="Status: Connected", bg="green", fg="white")
                else:
                    if time.time() - last_frame_time > reconnect_delay:
                        self.camera_manager.handle_disconnection(i)
                        self.status_labels[i].config(text=f"Status: Reconnecting Camera {i+1}", bg="orange", fg="black")
                        time.sleep(reconnect_delay)
            except Exception as e:
                self.camera_manager.log_error(str(e), camera_name)
                print(e)
                time.sleep(1)

    def start_stream_threads(self):
        for i in range(len(self.camera_manager.captures)):
            threading.Thread(target=self.stream_camera, args=(i,), daemon=True).start()