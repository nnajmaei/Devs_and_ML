import cv2
import multiprocessing
import numpy as np
import time
import os

from Broadcaster import VideoBroadcaster
from Processes import ConsumerProcess, VideoDisplayProcess, FaceDetectionProcess
from Processes import TextDetectionProcess, DownsampleProcess
from ProcessManager import MultiProcessor

if __name__ == "__main__":
    multiprocessor = MultiProcessor()
    multiprocessor.run()
