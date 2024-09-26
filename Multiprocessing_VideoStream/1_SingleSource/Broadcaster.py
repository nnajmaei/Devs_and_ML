import cv2
import multiprocessing
import time

class VideoBroadcaster:
    """
    A class for broadcasting video frames from a source using multiple processes.

    Attributes:
        video_source (str): The source of the video stream (e.g., file path or camera index).
        frame_queue (multiprocessing.Queue): A queue for storing video frames.
        stopped (multiprocessing.Event): An event to signal when the video broadcasting should stop.
        stop_flag (multiprocessing.Event): An event to signal that the broadcasting process has stopped.
        consumers_finished_flag (multiprocessing.Event): An event to signal that consumers have finished processing frames.
        capture (cv2.VideoCapture): A VideoCapture object for capturing frames from the video source.
        frame_rate (multiprocessing.Value): A shared value to store the frame rate.
        start_time (multiprocessing.Value): A shared value to store the start time.
        frame_count (multiprocessing.Value): A shared value to store the frame count.

    Methods:
        start(self):
            Starts the video broadcasting process. Captures frames from the source and puts them in the frame queue.

        stop(self):
            Stops the video broadcasting process and releases the video capture object.
    """

    def __init__(self, source):
        """
        Initializes a VideoBroadcaster instance.

        Args:
            source (str): The source of the video stream (e.g., file path or camera index).
        """
        self.video_source = source
        self.frame_queue = multiprocessing.Queue()
        self.stopped = multiprocessing.Event()
        self.stop_flag = multiprocessing.Event()
        self.consumers_finished_flag = multiprocessing.Event()
        self.capture = None
        self.frame_rate = multiprocessing.Value('d', 0.0)
        self.start_time = multiprocessing.Value('d', 0.0)
        self.frame_count = multiprocessing.Value('i', 0)

    def start(self):
        """
        Starts the video broadcasting process.

        Captures frames from the source, calculates frame rate, and puts frames into the frame queue.
        """
        self.capture = cv2.VideoCapture(self.video_source)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        while not self.stopped.is_set():
            ret, frame = self.capture.read()
            if not ret:
                break
            self.frame_queue.put(frame)
            with self.frame_count.get_lock():
                self.frame_count.value += 1
                elapsed_time = time.time() - self.start_time.value
                if elapsed_time > 1.0:
                    with self.frame_rate.get_lock():
                        self.frame_rate.value = self.frame_count.value / elapsed_time
                    self.start_time.value = time.time()
                    self.frame_count.value = 0
        if self.capture is not None:
            self.capture.release()
        self.stop_flag.set()
        self.consumers_finished_flag.wait()

    def stop(self):
        """
        Stops the video broadcasting process and releases the video capture object.
        """
        self.stopped.set()
        if self.capture is not None:
            self.capture.release()
