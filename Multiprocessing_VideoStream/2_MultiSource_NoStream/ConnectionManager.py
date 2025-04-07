import multiprocessing
import os

import cv2
from Broadcaster import VideoBroadcaster
from Processors import Client


class ConnectionManager:
    """
    A class responsible for managing video broadcasts and consumer processes.

    Attributes:
        sources (list): A list of video sources (broadcasters).
        clients (list): A list of clients, each with its consumer processes.
        broadcasters_queue (list): A list to hold broadcaster processes.
        processes_queue (list): A list to hold consumer processes.

    Methods:
        setup_broadcasts(self):
            Configures and sets up video broadcasts.
        setup_consumers(self):
            Configures and sets up consumer processes.
        run(self):
            Starts and manages the broadcast and consumer processes.
    """

    def __init__(self):
        """
        Initializes a ConnectionManager instance.
        """
        self.sources = []
        self.clients = []
        self.broadcasters_queue = []
        self.processes_queue = []

    def setup_broadcasts(self):
        """
        Configures and sets up video broadcasts.
        """
        while True:
            print("\n--------------------\nBROADCASTS SETUP:")
            source_number = int(input("How many broadcasts do you want to have? "))
            if source_number > 0:
                break
            else:
                print("Invalid choice.")

        for si in range(source_number):
            while True:
                choice = input(
                    f"\n--- Broadcast {si+1}: Select video source for broadcast: 1. Webcam, 2. Local saved video file: "
                )
                if choice == "1":
                    webcam_choice = input("Enter 0. for Webcam, 2. iPhone: ")
                    video_source = int(webcam_choice)
                    name = "Webcam " + webcam_choice
                    self.sources.append(VideoBroadcaster(video_source, name, si))
                    break
                elif choice == "2":
                    video_file = input("Enter the file name you want to use: ")
                    video_file = "/Users/niman/Desktop/" + video_file
                    if os.path.isfile(video_file):
                        video_source = video_file
                        name = "File_" + os.path.basename(video_source)
                        self.sources.append(VideoBroadcaster(video_source, name, si))
                        break
                    else:
                        print(
                            f"File '{video_file}' does not exist. Please provide a valid file path."
                        )
                else:
                    print("Invalid choice. Please enter 1 or 2.")
        print("\n----- Result -----")
        print("Broadcasts created:")
        for source in self.sources:
            print(f"Broadcast {source.channel_index + 1}: {source.name}")

    def setup_consumers(self):
        """
        Configures and sets up consumer processes for clients.
        """
        while True:
            print("\n--------------------\nCONSUMERS SETUP:")
            client_number = int(input("How many consumers do you want to have? "))
            if client_number > 0:
                break
            else:
                print("Invalid choice.")

        for ci in range(client_number):
            self.clients.append(Client(ci, self.sources))
            self.clients[ci].setup()
        print("\n----- Result -----")
        print("Consumers created:")
        for client in self.clients:
            print(
                f"Consumer {client.client_index + 1} has {len(client.consumer_processes)} processes:"
            )
            for process in client.consumer_processes:
                source_index = client.process_registry[process.__class__]
                print(
                    f"    - {process.window_name.split(' - ')[-1]} connected to source {source_index + 1} {process.broadcaster.name}"
                )
        print("------------------")

    def run(self):
        """
        Starts and manages the broadcast and consumer processes.
        """
        self.setup_broadcasts()
        self.setup_consumers()

        print("--- Broadcast Started")
        for i, source in enumerate(self.sources):
            self.broadcasters_queue.append(multiprocessing.Process(target=source.start))
            self.broadcasters_queue[i].start()

        print("--- Processes Started")
        print("------------------")
        for client in self.clients:
            for process in client.consumer_processes:
                process.start()
                self.processes_queue.append(process)

        for process in self.processes_queue:
            process.join()

        for broadcaster in self.broadcasters_queue:
            broadcaster.join(timeout=1)
            if broadcaster.is_alive():
                broadcaster.terminate()
                broadcaster.join()

        for source in self.sources:
            source.stop()
        for broadcaster in self.broadcasters_queue:
            broadcaster.join()
        print("Processes Terminated")
        print("Broadcast Terminated\n--------------------")
        cv2.destroyAllWindows()
