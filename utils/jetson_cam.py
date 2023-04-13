# MIT License
# Copyright (c) 2019 JetsonHacks
# See license
# Using a CSI camera (such as the Raspberry Pi Version 2) connected to a
# NVIDIA Jetson Nano Developer Kit using OpenCV
# Drivers for the camera and OpenCV are included in the base image

import cv2
import time

try:
    from Queue import Queue
except ModuleNotFoundError:
    from queue import Queue

import threading
import signal
import sys


# def signal_handler(sig, frame):
#     print('You pressed Ctrl+C!')
#     sys.exit(0)
# signal.signal(signal.SIGINT, signal_handler)


def gstreamer_pipeline(
        sensor_id=0,
        capture_width=1280,
        capture_height=720,
        display_width=640,
        display_height=360,
        framerate=60,
        flip_method=0,
):
    """
    Return a GStreamer pipeline for capturing from the CSI camera
    Args:
        sensor_id: The CSI sensor ID (0 or 1)
        capture_width: The capture width of the camera stream
        capture_height: The capture height of the camera stream
        display_width:  The display width of the camera stream
        display_height: The display height of the camera stream
        framerate: The framerate of the camera stream
        flip_method: The flip method of the camera stream

    Returns: A GStreamer pipeline for capturing from the CSI camera

    """
    return (
            "nvarguscamerasrc sensor_id=%d ! "
            "video/x-raw(memory:NVMM), "
            "width=(int)%d, height=(int)%d, "
            "format=(string)NV12, framerate=(fraction)%d/1 ! "
            "nvvidconv flip-method=%d ! "
            "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=(string)BGR ! appsink"
            % (
                sensor_id,
                capture_width,
                capture_height,
                framerate,
                flip_method,
                display_width,
                display_height,
            )
    )


class FrameReader(threading.Thread):
    """
    A class to read frames from a camera in a separate thread and store them in a queue for later use.
    """
    queues = []
    _running = True
    camera = None

    def __init__(self, camera, name):
        threading.Thread.__init__(self)
        self.name = name
        self.camera = camera

    def run(self):
        while self._running:
            _, frame = self.camera.read()
            while self.queues:
                queue = self.queues.pop()
                queue.put(frame)

    def addQueue(self, queue):
        self.queues.append(queue)

    def getFrame(self, timeout=None):
        queue = Queue(1)
        self.addQueue(queue)
        return queue.get(timeout=timeout)

    def stop(self):
        self._running = False


class Previewer(threading.Thread):
    """
    A class to preview frames from a camera in a separate thread.
    """
    window_name = "Arducam"
    _running = True
    camera = None

    def __init__(self, camera, name):
        threading.Thread.__init__(self)
        self.name = name
        self.camera = camera

    def run(self):
        self._running = True
        while self._running:
            cv2.imshow(self.window_name, self.camera.getFrame(2000))
            keyCode = cv2.waitKey(16) & 0xFF
        cv2.destroyWindow(self.window_name)

    def start_preview(self):
        self.start()

    def stop_preview(self):
        self._running = False


class Camera(object):
    """
    A class to manage a camera. It uses a FrameReader to read frames from the camera in a separate thread and store
    them in a queue for later use.
    """
    frame_reader = None
    cap = None
    previewer = None

    def __init__(self, sensor_id=0):
        self.open_camera(sensor_id)

    def open_camera(self, sensor_id=0):
        """
        Open the camera and start the frame reader.
        Args:
            sensor_id:  The CSI sensor ID (0 or 1)
        """
        self.cap = cv2.VideoCapture(gstreamer_pipeline(sensor_id), cv2.CAP_GSTREAMER)
        if not self.cap.isOpened():
            raise RuntimeError("Failed to open camera!")
        if self.frame_reader == None:
            self.frame_reader = FrameReader(self.cap, "")
            self.frame_reader.daemon = True
            self.frame_reader.start()
        self.previewer = Previewer(self.frame_reader, "")

    def getFrame(self):
        """
        Get a frame from the camera. This method blocks until a frame is available.
        Returns: A frame from the camera.

        """
        return self.frame_reader.getFrame()

    def start_preview(self):
        """
        Start the previewer thread.
        """
        self.previewer.daemon = True
        self.previewer.start_preview()

    def stop_preview(self):
        """
        Stop the previewer thread.
        """
        self.previewer.stop_preview()
        self.previewer.join()

    def close(self):
        """
        Close the camera and stop the frame reader.
        """
        self.frame_reader.stop()
        self.cap.release()


if __name__ == "__main__":
    camera_0 = Camera(sensor_id=0)
    # camera_1 = Camera(sensor_id=1)
    camera_0.start_preview()
    # camera_1.start_preview()
    time.sleep(20)
    camera_0.stop_preview()
    # camera_1.stop_preview()
    camera_0.close()
    # camera_1.close()
