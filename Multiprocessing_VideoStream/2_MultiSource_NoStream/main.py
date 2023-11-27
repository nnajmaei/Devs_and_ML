import cv2
import multiprocessing
import numpy as np
import time
import os

from Broadcaster import VideoBroadcaster
from Processors import ConsumerProcess, FaceDetectionProcess, TextDetectionProcess
from Processors import VideoDisplayProcess, DownsampleProcess, Client
from ConnectionManager import ConnectionManager

if __name__ == "__main__":

    manager = ConnectionManager()
    manager.run()
