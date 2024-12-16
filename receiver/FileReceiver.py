import socket
import json
import os
import platform
import subprocess


def open_image(image_path):
    if platform.system() == 'Windows':
        os.startfile(image_path)
    elif platform.system() == 'Darwin':
        subprocess.run(['open', image_path])
    else:
        subprocess.run(['xdg-open', image_path])


class NetworkFileReceiver:
    def __init__(self, host_ip='0.0.0.0', port=65432):
        self.host_ip = host_ip
        self.port = port
        self.receiver_socket = None

    def start_server(self):
        self.receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.receiver_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.receiver_socket.bind((self.host_ip, self.port))
        self.receiver_socket.listen(5)
        print(f"[*] Receiver listening on {self.host_ip}:{self.port}")

    def handle_request(self, connection, address):
        try:
            print(f"[*] Connection from {address}")

            # Wait for file transfer request
            data = connection.recv(1024).decode()
            if not data:
                print("[!] No data received from sender. Waiting for next attempt.")
                connection.close()
                return

            try:
                request = json.loads(data)
                if request['type'] == 'discovery':
                    print(f"[+] Received discovery request from {address}")
                    # Respond with READY signal
                    connection.send(b'RECEIVER_READY')

                    # Wait for file metadata
                    metadata = connection.recv(1024).decode()
                    if not metadata:
                        print("[!] No file metadata received. Waiting for next attempt.")
                        connection.close()
                        return

                    try:
                        file_info = json.loads(metadata)
                        filename = file_info['filename']
                        filesize = file_info['filesize']
                    except json.JSONDecodeError:
                        print("[!] Failed to decode file metadata.")
                        connection.close()
                        return

                    print(f"[*] Receiving file: {filename} ({filesize} bytes)")

                    # Acknowledge to sender that receiver is ready
                    connection.send(b'RECEIVER_READY')
                    # Receive the file
                    receive_folder = 'files/received/'
                    if not os.path.exists(receive_folder):
                        os.makedirs(receive_folder)
                    with open(os.path.join(receive_folder, filename), 'wb') as f:
                        remaining_bytes = filesize
                        while remaining_bytes > 0:
                            data = connection.recv(min(4096, remaining_bytes))
                            if not data:
                                break
                            f.write(data)
                            remaining_bytes -= len(data)

                    print(f"[✓] File {filename} received successfully.")

                    image_path ='files/received/screenshot.png'
                    open_image(image_path)

                    connection.close()
                    self.receiver_socket.close()
                    print("[*] Server stopped after receiving the file.")
                    return

            except json.JSONDecodeError:
                print("[!] Error decoding JSON data.")
                connection.close()

        except Exception as e:
            print(f"[!] Error while handling request from {address}: {e}")
            connection.close()

    def listen_for_requests(self):
        while True:
            connection, address = self.receiver_socket.accept()
            self.handle_request(connection, address)
            if self.receiver_socket.fileno() == -1:
                break



# receiver = NetworkFileReceiver()
# receiver.start_server()
# receiver.listen_for_requests()
