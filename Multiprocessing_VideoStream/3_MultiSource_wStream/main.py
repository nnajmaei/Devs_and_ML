import cv2
import multiprocessing
import numpy as np
import time
import os

from Broadcaster import VideoBroadcaster, ProcessBroadcaster
from Processes import (Client, ConsumerProcess, VideoDisplayProcess, FaceDetectionProcess,
                       TextDetectionProcess, DownsampleProcess)
from ConnectionManager import ConnectionManager


if __name__ == "__main__":

    manager = ConnectionManager()
    manager.run()
