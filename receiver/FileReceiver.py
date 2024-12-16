import os
import socket
import json


def post_process():

    pass


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
                    # open the received file
                    post_process()
                    connection.close()
                    # Stop the server after receiving the file
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
            # Accept incoming connection from sender
            connection, address = self.receiver_socket.accept()
            # Handle the connection and file transfer
            self.handle_request(connection, address)
            # Stop the server after handling the first request
            if self.receiver_socket.fileno() == -1:  # Check if the socket is closed
                break


def main():
    receiver = NetworkFileReceiver()
    receiver.start_server()
    receiver.listen_for_requests()


if __name__ == "__main__":
    main()
