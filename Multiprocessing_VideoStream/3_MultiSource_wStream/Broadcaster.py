import cv2
import multiprocessing
import time

class VideoBroadcaster:
    """
    A class for capturing video frames from a source and broadcasting them to a queue.

    Attributes:
        video_source (str): The video source URL or file path.
        name (str): The name of the broadcaster.
        channel_index (int): The channel index for the broadcaster.
        frame_queue (multiprocessing.Queue): A queue for storing video frames.
        stopped (multiprocessing.Event): An event to signal when the broadcaster should stop.
        stop_flag (multiprocessing.Event): An event to indicate that the broadcaster has stopped.
        consumers_finished_flag (multiprocessing.Event): An event to indicate when consumers have finished processing frames.
        capture (cv2.VideoCapture): The video capture object.
        frame_rate (multiprocessing.Value): A shared value for storing the frame rate.
        start_time (multiprocessing.Value): A shared value for storing the start time.
        frame_count (multiprocessing.Value): A shared value for counting frames.

    Methods:
        start(self):
            Starts capturing video frames and putting them in the frame_queue until stopped.

        stop(self):
            Stops the video capture and sets the stopped flag.

        calculate_frame_rate(self):
            Calculates the frame rate and updates the frame_rate attribute.
    """

    def __init__(self, video_source, name, channel_index):
        """
        Initializes a VideoBroadcaster instance with the provided parameters.

        Args:
            video_source (str): The video source URL or file path.
            name (str): The name of the broadcaster.
            channel_index (int): The channel index for the broadcaster.
        """
        self.video_source = video_source
        self.name = name
        self.channel_index = channel_index
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
        Starts capturing video frames and putting them in the frame_queue until stopped.
        """
        self.capture = cv2.VideoCapture(self.video_source)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        while not self.stopped.is_set():
            ret, frame = self.capture.read()
            if not ret:
                break
            self.frame_queue.put(frame)
            self.calculate_frame_rate()
        if self.capture is not None:
            self.capture.release()
        self.stop_flag.set()
        self.consumers_finished_flag.wait()

    def stop(self):
        """
        Stops the video capture and sets the stopped flag.
        """
        self.stopped.set()
        if self.capture is not None:
            self.capture.release()

    def calculate_frame_rate(self):
        """
        Calculates the frame rate and updates the frame_rate attribute.
        """
        with self.frame_count.get_lock():
            self.frame_count.value += 1
            elapsed_time = time.time() - self.start_time.value
            if elapsed_time > 1.0:
                with self.frame_rate.get_lock():
                    self.frame_rate.value = self.frame_count.value / elapsed_time
                self.start_time.value = time.time()
                self.frame_count.value = 0

class ProcessBroadcaster:
    def __init__(self, video_source, name, channel_index):
        self.video_source = video_source
        self.name = name
        self.channel_index = channel_index
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
        Starts capturing video frames and putting them in the frame_queue until stopped.
        """
        while not self.stop_flag.is_set():
            frame = self.video_source.get()
            if frame is None:
                break
            self.frame_queue.put(frame)
            self.calculate_frame_rate()
        self.stop_flag.set()
        self.consumers_finished_flag.wait()

    def stop(self):
        """
        Stops the video capture and sets the stopped flag.
        """
        self.stopped.set()
        if self.capture is not None:
            self.capture.release()

    def calculate_frame_rate(self):
        """
        Calculates the frame rate and updates the frame_rate attribute.
        """
        with self.frame_count.get_lock():
            self.frame_count.value += 1
            elapsed_time = time.time() - self.start_time.value
            if elapsed_time > 1.0:
                with self.frame_rate.get_lock():
                    self.frame_rate.value = self.frame_count.value / elapsed_time
                self.start_time.value = time.time()
                self.frame_count.value = 0
