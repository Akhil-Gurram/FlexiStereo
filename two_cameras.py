import cv2
import time
import os

def createFolder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print('Error: Creating directory. ' + directory)

def gstreamer_pipeline(
    capture_width=720,
    capture_height=720,
    display_width=720,
    display_height=720,
    framerate=120,
    flip_method=0,
    camera=0
):
    return (
        "nvarguscamerasrc sensor-id=%d ! "
        "video/x-raw(memory:NVMM), "
        "width=(int)%d, height=(int)%d, "
        "format=(string)NV12, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (
            camera,
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )

def show_camera():
    cap = cv2.VideoCapture(gstreamer_pipeline(camera=0), cv2.CAP_GSTREAMER)
    cap2 = cv2.VideoCapture(gstreamer_pipeline(camera=1), cv2.CAP_GSTREAMER)

    prevTime = 0

    if cap.isOpened() and cap2.isOpened():
        cv2.namedWindow("Right Camera", cv2.WINDOW_AUTOSIZE)
        cv2.namedWindow("Left Camera", cv2.WINDOW_AUTOSIZE)

        start_time = time.time()

        while (cv2.getWindowProperty("Right Camera", 0) >= 0 
               and cv2.getWindowProperty("Left Camera", 0) >= 0):
            ret_val, imgR = cap.read()
            ret_val2, imgL = cap2.read()

            imgR = cv2.rotate(imgR, cv2.ROTATE_180)
            imgL = cv2.rotate(imgL, cv2.ROTATE_180)

            cv2.imshow("Right Camera", imgR)
            cv2.imshow("Left Camera", imgL)

            keyCode = cv2.waitKey(30) & 0xFF # ESC
            if keyCode == 27:
                break

            if time.time() - start_time >= 5:
                now = time.localtime()

                img_date = "%04d-%02d-%02d" % (now.tm_year, now.tm_mon, now.tm_mday)
                img_time = "%02d:%02d:%02d" % (now.tm_hour, now.tm_min, now.tm_sec)

                img_dir1 = './images/Right/'+img_date
                createFolder(img_dir1)

                img_dir2 = './images/Left/'+img_date
                createFolder(img_dir2)

                img_name = "/" + img_time +".png"

                cv2.imwrite(img_dir1 + img_name, imgR)
                print(img_name + " written to " + img_dir1)

                cv2.imwrite(img_dir2 + img_name, imgL)
                print(img_name + " written to " + img_dir2)

                start_time = time.time()

        cap.release()
        cap2.release()
        cv2.destroyAllWindows()
    else:
        print("Unable to open camera")

if __name__ == "__main__":
    show_camera()
