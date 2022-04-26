# import cv2
# url = "http://192.168.101.39/webcam/?action=stream"
# cap = cv2.VideoCapture(url)
#
# while True:
#   ret, frame = cap.read()
#   print(frame.shape)
#   cv2.imshow('Video', frame)
#
#   if cv2.waitKey(1) == 27:
#     exit(0)

import cv2
import urllib.request
import numpy as np

stream = urllib.request.urlopen("http://192.168.101.39/webcam/?action=stream")
bytes = b''
while True:
    bytes += stream.read(1024)
    a = bytes.find(b'\xff\xd8') #frame starting
    b = bytes.find(b'\xff\xd9') #frame ending
    if a != -1 and b != -1:
        jpg = bytes[a:b+2]
        bytes = bytes[b+2:]
        img = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), 1)
        cv2.imshow('image', img)
        if cv2.waitKey(1) == 27:
            cv2.destroyAllWindows()
            break
