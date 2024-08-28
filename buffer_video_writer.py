import cv2
import threading, queue, time
import logging

class BufferedVideoWriter:
    def __init__(self, filename, fourcc, fps, frameSize, maxBufferSize=25):
        self.fourcc = fourcc
        self.thread = None
        self.queue = queue.Queue()
        self.fps = fps
        self.maxBufferSize = maxBufferSize
        self.frameSize = frameSize
        self.filename = filename
        self.logger = logging.getLogger(__name__)

    def start(self):
        if self.thread:
            return
        if self.fps <= 0:
            self.logger.error(f"Invalid FPS value: {self.fps}. Using default value of 30.")
            self.fps = 30  # Set a default FPS if the value is invalid
        dt = 1. / self.fps
        def loop():
            try:
                writer = cv2.VideoWriter(filename=self.filename, fourcc=self.fourcc, fps=self.fps, frameSize=self.frameSize)
                t = time.time()
                self.queue.put((cv2.rectangle(self.frameSize, (0, 0), self.frameSize, (0, 0, 0), -1), t))
                while self.thread or self.queue.qsize():
                    frame, ts = self.queue.get()
                    if frame is None:
                        break
                    while t < ts:
                        writer.write(frame)
                        t += dt
                writer.release()
            except Exception as e:
                self.logger.error(f"Error in BufferedVideoWriter loop: {str(e)}")

        self.thread = threading.Thread(target=loop)
        self.thread.start()

    def stop(self):
        if not self.thread:
            return
        self.write(None)
        t = self.thread
        self.thread = None
        t.join()
        
    def write(self, image):
        if self.thread and self.queue.qsize() < self.maxBufferSize:
            return self.queue.put((image, time.time()))