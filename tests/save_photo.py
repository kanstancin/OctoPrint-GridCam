import cv2
import os

cam = cv2.VideoCapture(0)


ret, img = cam.read()
if not ret:
    print("failed to grab frame")

dir_out = "data/"
img_name = f"saved_img2.png"
cv2.imwrite(os.path.join(dir_out, img_name), img)
print(f"saved image: `{img_name}`")

cam.release()
