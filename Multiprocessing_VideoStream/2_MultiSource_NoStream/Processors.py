import cv2
import multiprocessing
import numpy as np
import time
import os

class ConsumerProcess(multiprocessing.Process):
    """
    A class for processing video frames from a frame queue.

    Attributes:
        frame_queue (multiprocessing.Queue): A queue containing video frames.
        task_function (function): The function to process each frame.
        index (int): The index of the consumer process.
        client_index (int): The index of the client associated with the process.
        window_name (str): The name of the display window.
        stop_flag (multiprocessing.Event): An event to indicate that the process should stop.
        consumers_finished_flag (multiprocessing.Event): An event to signal when consumers have finished processing frames.
        broadcaster (VideoBroadcaster): The video broadcaster object.
        frame_rate (float): The frame rate of the consumer process.
        start_time (float): The start time for calculating frame rate.
        frame_count (int): The count of processed frames.

    Methods:
        run(self):
            Runs the consumer process, processing frames and calculating the frame rate.

        get_broadcaster_frame_rate(self):
            Gets the frame rate from the video broadcaster.

        set_window_name(self, process_name):
            Sets the display window name.

        display_frame(self, frame):
            Displays the frame with frame rates.
    """

    def __init__(self, task_function, client_index, index, broadcaster):
        """
        Initializes a ConsumerProcess instance with the provided parameters.

        Args:
            task_function (function): The function to process each frame.
            client_index (int): The index of the client associated with the process.
            index (int): The index of the consumer process.
            broadcaster (VideoBroadcaster): The video broadcaster object.
        """
        super().__init__()
        self.frame_queue = broadcaster.frame_queue
        self.task_function = task_function
        self.index = index
        self.client_index = client_index
        self.window_name = None
        self.stop_flag = broadcaster.stop_flag
        self.consumers_finished_flag = broadcaster.consumers_finished_flag
        self.broadcaster = broadcaster
        self.frame_rate = 0.0
        self.start_time = time.time()
        self.frame_count = 0

    def run(self):
        """
        Runs the consumer process, processing frames and calculating the frame rate.
        """
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
        """
        Gets the frame rate from the video broadcaster.

        Returns:
            float: The frame rate of the video broadcaster.
        """
        with self.broadcaster.frame_rate.get_lock():
            return self.broadcaster.frame_rate.value

    def set_window_name(self, process_name):
        """
        Sets the display window name.

        Args:
            process_name (str): The name of the process associated with the window.
        """
        self.window_name = (
            f"Consumer {self.client_index + 1} - Process {self.index + 1} - {process_name}"
        )

    def display_frame(self, frame):
        """
        Displays the frame with frame rates.

        Args:
            frame: The video frame to display.
        """
        frame = cv2.resize(frame, (640, 480))
        cv2.putText(
            frame,
            f"Broadcast Frame Rate: {self.get_broadcaster_frame_rate():6.2f} fps",
            (10, 30),
            cv2.FONT_HERSHEY_DUPLEX,
            0.5,
            (255, 255, 255),
            1
        )
        cv2.putText(
            frame,
            f"Process Frame Rate:   {self.frame_rate:6.2f} fps",
            (10, 60),
            cv2.FONT_HERSHEY_DUPLEX,
            0.5,
            (255, 255, 255),
            1
        )
        cv2.imshow(self.window_name, frame)
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        key = cv2.waitKey(1)
        if key == ord('q'):
            self.frame_queue.put(None)

class VideoDisplayProcess(ConsumerProcess):
    """
    A class for displaying video frames in a separate process.

    Inherits from ConsumerProcess.

    Methods:
        __init__(self, client_index, index, broadcaster):
            Initializes a VideoDisplayProcess instance with the given parameters.

    Attributes:
        Inherits attributes from ConsumerProcess.
    """

    def __init__(self, client_index, index, broadcaster):
        """
        Initializes a VideoDisplayProcess instance.

        Args:
            client_index (int): The index of the client associated with the process.
            index (int): The index of the consumer process.
            broadcaster (VideoBroadcaster): The video broadcaster object.
        """
        super().__init__(self.display_frame, client_index, index, broadcaster)
        self.set_window_name("Video Display")

class FaceDetectionProcess(ConsumerProcess):
    """
    A class for performing face detection on video frames in a separate process.

    Inherits from ConsumerProcess.

    Methods:
        __init__(self, client_index, index, broadcaster):
            Initializes a FaceDetectionProcess instance with the given parameters.
        load_face_detection_model(self):
            Loads the face detection model.
        detect_faces(self, frame):
            Detects faces in the input frame and displays them.

    Attributes:
        Inherits attributes from ConsumerProcess.
        confidence_threshold (float): The confidence threshold for face detection.
        net: The face detection neural network model.
    """

    def __init__(self, client_index, index, broadcaster):
        """
        Initializes a FaceDetectionProcess instance.

        Args:
            client_index (int): The index of the client associated with the process.
            index (int): The index of the consumer process.
            broadcaster (VideoBroadcaster): The video broadcaster object.
        """
        super().__init__(self.detect_faces, client_index, index, broadcaster)
        self.set_window_name("Face Detection")
        self.confidence_threshold = 0.2

    def load_face_detection_model(self):
        """
        Loads the face detection model.
        """
        model_path = os.getcwd()+"/DNN_models/deploy.prototxt"
        weights_path = os.getcwd()+"/DNN_models/res10_300x300_ssd_iter_140000.caffemodel"
        try:
            self.net = cv2.dnn.readNetFromCaffe(model_path, weights_path)
        except cv2.error as e:
            print(f"Error loading the face detection model: {e}")

    def detect_faces(self, frame):
        """
        Detects faces in the input frame and displays them.

        Args:
            frame: The video frame to perform face detection on.
        """
        if not hasattr(self, 'net'):
            self.load_face_detection_model()
        blob = cv2.dnn.blobFromImage(
            cv2.resize(frame, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
        self.net.setInput(blob)
        detections = self.net.forward()
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > self.confidence_threshold:
                box = detections[0, 0, i, 3:7] * np.array(
                    [frame.shape[1], frame.shape[0], frame.shape[1], frame.shape[0]])
                (startX, startY, endX, endY) = box.astype(int)
                cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)
        self.display_frame(frame)

class TextDetectionProcess(ConsumerProcess):
    """
    A class for performing text detection on video frames in a separate process.

    Inherits from ConsumerProcess.

    Methods:
        __init__(self, client_index, index, broadcaster):
            Initializes a TextDetectionProcess instance with the given parameters.
        load_text_detection_model(self):
            Loads the text detection model.
        detect_texts(self, frame):
            Detects texts in the input frame and displays them.
        non_max_suppression(self, boxes, probs=None, overlapThresh=0.3):
            Performs non-maximum suppression on detected text boxes.

    Attributes:
        Inherits attributes from ConsumerProcess.
        confidence_threshold (float): The confidence threshold for text detection.
        net: The text detection neural network model.
    """

    def __init__(self, client_index, index, broadcaster):
        """
        Initializes a TextDetectionProcess instance.

        Args:
            client_index (int): The index of the client associated with the process.
            index (int): The index of the consumer process.
            broadcaster (VideoBroadcaster): The video broadcaster object.
        """
        super().__init__(self.detect_texts, client_index, index, broadcaster)
        self.set_window_name("Text Detection")
        self.confidence_threshold = 0.2

    def load_text_detection_model(self):
        """
        Loads the text detection model.
        """
        model_path = os.getcwd()+"/DNN_models/frozen_east_text_detection.pb"
        try:
            self.net = cv2.dnn.readNet(model_path)
        except cv2.error as e:
            print(f"Error loading the text detection model: {e}")

    def detect_texts(self, frame):
        if not hasattr(self, 'net'):
            self.load_text_detection_model()
        if self.broadcaster.video_source != 0:
            confidence_threshold = 0.3
            max_rows = 1.0
        else:
            confidence_threshold = 0.1
            max_rows = 0.4
        small_frame = cv2.resize(frame, (320, 320))
        blob = cv2.dnn.blobFromImage(
            small_frame, 1.0, (320, 320), (123.68, 116.78, 103.94), swapRB=True, crop=False)
        self.net.setInput(blob)
        (scores, geometry) = self.net.forward(["feature_fusion/Conv_7/Sigmoid", "feature_fusion/concat_3"])
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
        for (startX, startY, endX, endY) in boxes:
            cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)
        self.display_frame(frame)

    def non_max_suppression(self, boxes, probs=None, overlapThresh=0.3):
        """
        Performs non-maximum suppression on detected text boxes.

        Args:
            boxes (numpy.ndarray): Array of detected text boxes.
            probs (list): List of detection probabilities.
            overlapThresh (float): Overlap threshold for suppression.

        Returns:
            numpy.ndarray: Filtered list of text boxes after non-maximum suppression.
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
            idxs = np.delete(idxs, np.concatenate(([last], np.where(overlap > overlapThresh)[0])))
        return boxes[pick].astype("int")

class DownsampleProcess(ConsumerProcess):
    """
    A class for downscaling video frames in a separate process.

    Inherits from ConsumerProcess.

    Methods:
        __init__(self, client_index, index, broadcaster, downscale_factor=0.2):
            Initializes a DownsampleProcess instance with the given parameters.
        downsample_frame(self, frame):
            Downsamples the input frame and displays it.

    Attributes:
        Inherits attributes from ConsumerProcess.
        downscale_factor (float): The factor by which frames are downscaled.
    """

    def __init__(self, client_index, index, broadcaster, downscale_factor=0.2):
        """
        Initializes a DownsampleProcess instance.

        Args:
            client_index (int): The index of the client associated with the process.
            index (int): The index of the consumer process.
            broadcaster (VideoBroadcaster): The video broadcaster object.
            downscale_factor (float): The factor by which frames are downscaled.
        """
        super().__init__(self.downsample_frame, client_index, index, broadcaster)
        self.set_window_name("Downsample")
        self.downscale_factor = downscale_factor

    def downsample_frame(self, frame):
        """
        Downsamples the input frame and displays it.

        Args:
            frame: The video frame to be downsampled and displayed.
        """
        frame = cv2.resize(frame, None, fx=self.downscale_factor, fy=self.downscale_factor)
        self.display_frame(frame)

class Client:
    """
    A class representing a client with multiple consumer processes.

    Attributes:
        client_index (int): The index of the client.
        sources (list): A list of video sources.
        consumer_processes (list): A list to hold instances of ConsumerProcess.
        process_registry (dict): A dictionary mapping consumer process classes to their corresponding channels.

    Methods:
        setup(self):
            Sets up the client by configuring and initializing consumer processes.
        initialize_process(self, consumer_class, index, broadcaster):
            Initializes a consumer process instance.

    """
    def __init__(self, client_index, sources):
        """
        Initializes a Client instance with the given parameters.

        Args:
            client_index (int): The index of the client.
            sources (list): A list of video sources.
        """
        self.client_index = client_index
        self.sources = sources
        self.consumer_processes = []  # List to hold instances of ConsumerProcess
        self.process_registry = {}

    def setup(self):
        """
        Sets up the client by configuring and initializing consumer processes.
        """
        while True:
            try:
                print("\n----------")
                print(f"----- Consumer {self.client_index + 1}:")
                count = int(input(
                    f"Enter the number of processes you want to add to consumer {self.client_index + 1}: "))
                if count >= 1:
                    break
                else:
                    print("Please enter a valid number (at least 1).")
            except ValueError:
                print("Invalid input. Please enter a valid number.")

        for i in range(count):
            print(f"\n--- Consumer {self.client_index + 1} - Process {i + 1}:")
            while True:
                choice = input(
                    "Select process type: 1. Video Display, 2. Face Detection, 3. Text Detection, 4. Downsampler: ")
                print(
                    f"Select Broadcast for Consumer {self.client_index + 1} - Process {i + 1}:")
                for idx, source in enumerate(self.sources):
                    print(f"{idx + 1}. {source.name}")

                try:
                    channel_index = int(
                        input(f"Enter the broadcast for this process {i + 1}: ")) - 1
                    if channel_index < 0 or channel_index >= len(self.sources):
                        raise ValueError
                except ValueError:
                    print(
                        "Invalid channel choice. Please select from the provided options.")
                    continue

                if choice == '1':
                    self.process_registry[VideoDisplayProcess] = channel_index
                    break
                elif choice == '2':
                    self.process_registry[FaceDetectionProcess] = channel_index
                    break
                elif choice == '3':
                    self.process_registry[TextDetectionProcess] = channel_index
                    break
                elif choice == '4':
                    self.process_registry[DownsampleProcess] = channel_index
                    break
                else:
                    print("Invalid choice.")

        for i, (consumer_class, channel) in enumerate(self.process_registry.items()):
            self.consumer_processes.append(
                self.initialize_process(consumer_class, i, self.sources[channel]))

    def initialize_process(self, consumer_class, index, broadcaster):
        """
        Initializes a consumer process instance.

        Args:
            consumer_class: The class of the consumer process to initialize.
            index (int): The index of the consumer process.
            broadcaster: The video broadcaster object.

        Returns:
            ConsumerProcess: The initialized consumer process instance.
        """
        consumer = consumer_class(self.client_index, index, broadcaster)
        return consumer
