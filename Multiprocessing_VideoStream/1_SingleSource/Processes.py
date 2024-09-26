import cv2
import multiprocessing
import numpy as np
import time
import os


class ConsumerProcess(multiprocessing.Process):
    """
    A base class for consumer processes that process frames from a queue.

    Attributes:
        frame_queue (multiprocessing.Queue): A queue for frames to be processed.
        task_function (callable): The function to process frames.
        index (int): The index of the consumer process.
        window_name (str): The window name for displaying frames.
        stop_flag (multiprocessing.Event): An event to signal the process to stop.
        consumers_finished_flag (multiprocessing.Event): An event to signal when all consumers are finished.
        broadcaster (Broadcaster): The broadcaster object for communication.
        frame_rate (float): The frame processing rate.
        start_time (float): The start time of frame processing.
        frame_count (int): The number of frames processed.
    """

    def __init__(self, task_function, index, broadcaster):
        super().__init__()
        self.frame_queue = broadcaster.frame_queue
        self.task_function = task_function
        self.index = index
        self.window_name = None
        self.stop_flag = broadcaster.stop_flag
        self.consumers_finished_flag = broadcaster.consumers_finished_flag
        self.broadcaster = broadcaster
        self.frame_rate = 0.0
        self.start_time = time.time()
        self.frame_count = 0

    def run(self):
        while not self.stop_flag.is_set():
            frame = self.frame_queue.get()
            if frame is None:
                break
            self.task_function(frame)
            self.frame_count += 1
            elapsed_time = time.time() - self.start_time
            if elapsed_time > 1.0:
                self.frame_rate = self.frame_count / elapsed_time
                self.start_time = time.time()
                self.frame_count = 0

        self.consumers_finished_flag.set()

    def get_broadcaster_frame_rate(self):
        """Get the frame rate from the broadcaster."""
        with self.broadcaster.frame_rate.get_lock():
            return self.broadcaster.frame_rate.value

    def set_window_name(self, process_name):
        """Set the window name for displaying frames."""
        self.window_name = f"Consumer {self.index} - {process_name}"

    def display_frame(self, frame):
        """
        Display a frame with information about frame rates.

        Args:
            frame (numpy.ndarray): The frame to be displayed.
        """
        frame = cv2.resize(frame, (640, 480))
        cv2.putText(
            frame,
            f"Broadcast Frame Rate: {self.get_broadcaster_frame_rate():6.2f} fps",
            (10, 30),
            cv2.FONT_HERSHEY_DUPLEX,
            0.5,
            (255, 255, 255),
            1,
        )
        cv2.putText(
            frame,
            f"Process Frame Rate:   {self.frame_rate:6.2f} fps",
            (10, 60),
            cv2.FONT_HERSHEY_DUPLEX,
            0.5,
            (255, 255, 255),
            1,
        )
        cv2.imshow(self.window_name, frame)
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        key = cv2.waitKey(1)
        if key == ord("q"):
            self.frame_queue.put(None)


class VideoDisplayProcess(ConsumerProcess):
    """
    A consumer process for displaying video frames.

    Attributes:
        index (int): The index of the consumer process.
        broadcaster (Broadcaster): The broadcaster object for communication.
    """

    def __init__(self, index, broadcaster):
        super().__init__(self.display_frame, index, broadcaster)
        self.set_window_name("Video Display")


class FaceDetectionProcess(ConsumerProcess):
    """
    A consumer process for detecting faces in video frames.

    Attributes:
        index (int): The index of the consumer process.
        broadcaster (Broadcaster): The broadcaster object for communication.
        confidence_threshold (float): The confidence threshold for face detection.
        net (cv2.dnn_Net): The face detection neural network.
    """

    def __init__(self, index, broadcaster):
        super().__init__(self.detect_faces, index, broadcaster)
        self.set_window_name("Face Detection")
        self.confidence_threshold = 0.2

    def load_face_detection_model(self):
        """Load the face detection model."""
        model_path = os.getcwd() + "/DNN_models/deploy.prototxt"
        weights_path = (
            os.getcwd() + "/DNN_models/res10_300x300_ssd_iter_140000.caffemodel"
        )
        try:
            self.net = cv2.dnn.readNetFromCaffe(model_path, weights_path)
        except cv2.error as e:
            print(f"Error loading the face detection model: {e}")

    def detect_faces(self, frame):
        """Detect faces in a video frame and display them."""
        if not hasattr(self, "net"):
            self.load_face_detection_model()
        blob = cv2.dnn.blobFromImage(
            cv2.resize(frame, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0)
        )
        self.net.setInput(blob)
        detections = self.net.forward()
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > self.confidence_threshold:
                box = detections[0, 0, i, 3:7] * np.array(
                    [frame.shape[1], frame.shape[0], frame.shape[1], frame.shape[0]]
                )
                (startX, startY, endX, endY) = box.astype(int)
                cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)
        self.display_frame(frame)


class TextDetectionProcess(ConsumerProcess):
    """
    A consumer process for detecting text in video frames.

    Attributes:
        index (int): The index of the consumer process.
        broadcaster (Broadcaster): The broadcaster object for communication.
        net (cv2.dnn_Net): The text detection neural network.
    """

    def __init__(self, index, broadcaster):
        super().__init__(self.detect_texts, index, broadcaster)
        self.set_window_name("Text Detection")

    def load_text_detection_model(self):
        """Load the text detection model."""
        model_path = os.getcwd() + "/DNN_models/frozen_east_text_detection.pb"
        try:
            self.net = cv2.dnn.readNet(model_path)
        except cv2.error as e:
            print(f"Error loading the text detection model: {e}")

    def detect_texts(self, frame):
        """Detect text in a video frame and display it."""
        if not hasattr(self, "net"):
            self.load_text_detection_model()
        if self.broadcaster.video_source != 0:
            confidence_threshold = 0.3
            max_rows = 1.0
        else:
            confidence_threshold = 0.1
            max_rows = 0.4
        small_frame = cv2.resize(frame, (320, 320))
        blob = cv2.dnn.blobFromImage(
            small_frame,
            1.0,
            (320, 320),
            (123.68, 116.78, 103.94),
            swapRB=True,
            crop=False,
        )
        self.net.setInput(blob)
        (scores, geometry) = self.net.forward(
            ["feature_fusion/Conv_7/Sigmoid", "feature_fusion/concat_3"]
        )
        (numRows, numCols) = scores.shape[2:4]
        rects = []
        confidences = []
        for y in range(0, int(numRows * max_rows)):
            scoresData = scores[0, 0, y]
            xData0 = geometry[0, 0, y]
            xData1 = geometry[0, 1, y]
            xData2 = geometry[0, 2, y]
            xData3 = geometry[0, 3, y]
            anglesData = geometry[0, 4, y]
            for x in range(0, numCols):
                if scoresData[x] < confidence_threshold:
                    continue
                (offsetX, offsetY) = (x * 4.0, y * 4.0)
                angle = anglesData[x]
                cos = np.cos(angle)
                sin = np.sin(angle)
                h = xData0[x] + xData2[x]
                w = xData1[x] + xData3[x]
                endX = int(offsetX + (cos * xData1[x]) + (sin * xData2[x]))
                endY = int(offsetY - (sin * xData1[x]) + (cos * xData2[x]))
                startX = int(endX - w)
                startY = int(endY - h)
                startX = int(startX * (frame.shape[1] / 320))
                startY = int(startY * (frame.shape[0] / 320))
                endX = int(endX * (frame.shape[1] / 320))
                endY = int(endY * (frame.shape[0] / 320))
                rects.append((startX, startY, endX, endY))
                confidences.append(scoresData[x])
        boxes = self.non_max_suppression(np.array(rects), probs=confidences)
        for startX, startY, endX, endY in boxes:
            cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)
        self.display_frame(frame)

    def non_max_suppression(self, boxes, probs=None, overlapThresh=0.3):
        """
        Apply non-maximum suppression to eliminate redundant boxes.

        Args:
            boxes (numpy.ndarray): An array of bounding boxes.
            probs (numpy.ndarray): An array of confidence scores.
            overlapThresh (float): Threshold for overlapping boxes.

        Returns:
            numpy.ndarray: An array of selected boxes after non-maximum suppression.
        """
        if len(boxes) == 0:
            return []
        if boxes.dtype.kind == "i":
            boxes = boxes.astype("float")
        pick = []
        x1 = boxes[:, 0]
        y1 = boxes[:, 1]
        x2 = boxes[:, 2]
        y2 = boxes[:, 3]
        area = (x2 - x1 + 1) * (y2 - y1 + 1)
        if probs is not None:
            idxs = np.argsort(probs)
        else:
            idxs = np.argsort(y2)
        while len(idxs) > 0:
            last = len(idxs) - 1
            i = idxs[last]
            pick.append(i)
            xx1 = np.maximum(x1[i], x1[idxs[:last]])
            yy1 = np.maximum(y1[i], y1[idxs[:last]])
            xx2 = np.minimum(x2[i], x2[idxs[:last]])
            yy2 = np.minimum(y2[i], y2[idxs[:last]])
            w = np.maximum(0, xx2 - xx1 + 1)
            h = np.maximum(0, yy2 - yy1 + 1)
            overlap = (w * h) / area[idxs[:last]]
            idxs = np.delete(
                idxs, np.concatenate(([last], np.where(overlap > overlapThresh)[0]))
            )
        return boxes[pick].astype("int")


class DownsampleProcess(ConsumerProcess):
    """
    A consumer process for downscaling video frames.

    Attributes:
        index (int): The index of the consumer process.
        broadcaster (Broadcaster): The broadcaster object for communication.
        downscale_factor (float): The factor by which frames are downscaled.
    """

    def __init__(self, index, broadcaster, downscale_factor=0.2):
        super().__init__(self.downsample_frame, index, broadcaster)
        self.set_window_name("Downsample")
        self.downscale_factor = downscale_factor

    def downsample_frame(self, frame):
        """Downscale a video frame and display it."""
        frame = cv2.resize(
            frame, None, fx=self.downscale_factor, fy=self.downscale_factor
        )
        self.display_frame(frame)
