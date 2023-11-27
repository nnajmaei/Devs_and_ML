import cv2
import multiprocessing
import numpy as np
import time
import os

from Broadcaster import VideoBroadcaster
from Processes import ConsumerProcess, VideoDisplayProcess, FaceDetectionProcess
from Processes import TextDetectionProcess, DownsampleProcess

class MultiProcessor:
    """
    A class responsible for managing video broadcasts and consumer processes.

    Attributes:
        video_broadcaster (VideoBroadcaster): The video broadcaster instance.
        video_source: The selected video source (Webcam or local video file).
        consumer_processes (list): A list of consumer process classes to run.
        consumer_processes_instances (list): A list to hold instances of running consumer processes.

    Methods:
        select_video_source(self):
            Selects the video source (Webcam or local video file).
        select_consumer_processes(self):
            Selects the consumer processes to run.
        initialize_consumer(self, consumer_class, index, broadcaster):
            Initializes and starts a consumer process instance.
        run(self):
            Runs the video broadcaster and consumer processes.
    """

    def __init__(self):
        """
        Initializes a MultiProcessor instance.
        """
        self.video_broadcaster = None
        self.video_source = None
        self.consumer_processes = []
        self.consumer_processes_instances = []

    def select_video_source(self):
        """
        Selects the video source (Webcam or local video file).
        """
        while True:
            print("Select video source: 1. Webcam, 2. Local saved video file (MLB.mp4)")
            choice = input("Enter 1 or 2: ")
            if choice == '1':
                webcam_choice = input("Enter 0. for Webcam, 2. iPhone: ")
                self.video_source = int(webcam_choice)
                break
            elif choice == '2':
                video_file = "/Users/niman/Desktop/MLB.mp4"
                if os.path.isfile(video_file):
                    self.video_source = video_file
                    break
                else:
                    print(f"File '{video_file}' does not exist. Please provide a valid file path.")
            else:
                print("Invalid choice. Please enter 1 or 2.")

    def select_consumer_processes(self):
        """
        Selects the consumer processes to run.
        """
        while True:
            try:
                count = int(input("\nEnter the number of consumers: "))
                if count >= 1:
                    break
                else:
                    print("Please enter a valid number (at least 1).")
            except ValueError:
                print("Invalid input. Please enter a valid number.")
        print("\n")
        for i in range(count):
            print(f"==========\nConsumer {i + 1}:")
            print("Select process type: 1. Video Display, 2. Face Detection, 3. Text Detection, 4. Downsampler")
            while True:
                choice = input(f"Enter 1, 2, 3, or 4 for Consumer {i + 1}: ")
                if choice == '1':
                    self.consumer_processes.append(VideoDisplayProcess)
                    break
                elif choice == '2':
                    self.consumer_processes.append(FaceDetectionProcess)
                    break
                elif choice == '3':
                    self.consumer_processes.append(TextDetectionProcess)
                    break
                elif choice == '4':
                    self.consumer_processes.append(DownsampleProcess)
                    break
                else:
                    print("Invalid choice. Please enter 1, 2, 3, or 4.")
        print("==========\nBroadcast and Processes Initiating\n==========")

    def initialize_consumer(self, consumer_class, index, broadcaster):
        """
        Initializes and starts a consumer process instance.

        Args:
            consumer_class: The consumer process class to initialize.
            index (int): The index of the consumer process.
            broadcaster (VideoBroadcaster): The video broadcaster instance.

        Returns:
            ConsumerProcess: The initialized consumer process instance.
        """
        consumer = consumer_class(index, broadcaster)
        consumer.start()
        return consumer

    def run(self):
        """
        Runs the video broadcaster and consumer processes.
        """
        try:
            self.select_video_source()
            self.select_consumer_processes()
            self.video_broadcaster = VideoBroadcaster(self.video_source)
            broadcaster_process = multiprocessing.Process(target=self.video_broadcaster.start)
            broadcaster_process.start()
            consumer_processes = [
                self.initialize_consumer(consumer_class, i + 1, self.video_broadcaster)
                for i, consumer_class in enumerate(self.consumer_processes)
            ]
            for consumer_process in consumer_processes:
                consumer_process.join()
            self.video_broadcaster.stop()
            broadcaster_process.join(timeout=1)
            if broadcaster_process.is_alive():
                broadcaster_process.terminate()
                broadcaster_process.join()
        except KeyboardInterrupt:
            print("Program terminated by the user.")
        except Exception as e:
            print(f"An error occurred in the main process: {e}")
        finally:
            for consumer_process in consumer_processes:
                consumer_process.join()
            print("All processes have been terminated correctly and gracefully.")
            cv2.destroyAllWindows()
