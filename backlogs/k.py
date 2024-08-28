import cv2
import time

# open video stream
cap = cv2.VideoCapture('rtsp://admin:WeCrunch1@192.168.0.36/stream', cv2.CAP_FFMPEG)

# set video resolution
frame_width = int(cap.get(3))
frame_height = int(cap.get(4))
fps = int(cap.get(cv2.CAP_PROP_FPS))
print(fps)
# set video codec
fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
out = cv2.VideoWriter('output.avi', fourcc, fps, (frame_width, frame_height))

# start timer
start_time = time.time()

while (int(time.time() - start_time) < 60):
    ret, frame = cap.read()
    if ret == True:
        out.write(frame)
        cv2.imshow('frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    else:
        break

# release resources
cap.release()
out.release()
cv2.destroyAllWindows()
