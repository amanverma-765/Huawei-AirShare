import socket
import json
import os
import threading
import time
import psutil
import ipaddress

class NetworkFileSender:
    def __init__(self, file_path, port=65432):
        self.file_path = file_path
        self.port = port
        self.receivers = []

    def get_network_range(self):
        # Find local network range based on IP and subnet mask
        for interface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    ip = addr.address
                    netmask = addr.netmask
                    if ip.startswith('192.168.0') or ip.startswith('10.') or ip.startswith('172.'):
                        if netmask:
                            network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
                            return network
        return None

    def discover_receivers(self, timeout=2):
        # Continuously discover active receivers on the local network
        while True:
            print("[*] Discovering receivers...")
            network = self.get_network_range()
            if not network:
                print("[!] Could not determine network range")
                return []

            discovered_ips = []

            def check_host(ip):
                try:
                    test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    test_socket.settimeout(timeout)
                    result = test_socket.connect_ex((str(ip), self.port))
                    test_socket.close()

                    if result == 0:
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                            s.connect((str(ip), self.port))
                            s.send(json.dumps({'type': 'discovery'}).encode())
                            response = s.recv(1024).decode()
                            if response == 'RECEIVER_READY':
                                discovered_ips.append(str(ip))
                except Exception:
                    pass

            threads = []
            for ip in network.hosts():
                thread = threading.Thread(target=check_host, args=(ip,))
                thread.start()
                threads.append(thread)

            for thread in threads:
                thread.join()

            if discovered_ips:
                print("[*] Found receivers:")
                for receiver_ip in discovered_ips:
                    print(f" - {receiver_ip}")
                self.receivers = discovered_ips
                break  # Stop searching once a receiver is found
            else:
                print("[!] No receivers found, retrying...")

            time.sleep(5)  # Wait for 5 seconds before retrying discovery

    def send_file(self, receiver_ip):
        try:
            filename = os.path.basename(self.file_path)
            filesize = os.path.getsize(self.file_path)

            # Create file metadata object
            file_info = {
                'filename': filename,
                'filesize': filesize
            }

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((receiver_ip, self.port))
                # Send the discovery message
                s.send(json.dumps({'type': 'discovery'}).encode())

                # Wait for receiver to respond with READY
                response = s.recv(1024).decode()
                if response != 'RECEIVER_READY':
                    print(f"[!] Receiver {receiver_ip} not ready.")
                    return

                # Send the file metadata
                s.send(json.dumps(file_info).encode())

                # Wait for READY signal from the receiver
                response = s.recv(1024).decode()
                if response != 'RECEIVER_READY':
                    print(f"[!] Receiver {receiver_ip} did not confirm readiness.")
                    return

                # Now, send the file
                with open(self.file_path, 'rb') as file:
                    while chunk := file.read(4096):
                        s.send(chunk)
                print(f"[✓] File {filename} sent to {receiver_ip}.")

        except Exception as e:
            print(f"[!] Error sending file to {receiver_ip}: {e}")

    def start_sending(self):
        print("[*] Starting receiver discovery...")
        self.discover_receivers()  # Start discovery process
        if self.receivers:
            print("[*] Sending file transfer requests...")
            for receiver_ip in self.receivers:
                self.send_file(receiver_ip)  # Send file to the first found receiver
        else:
            print("[!] No receivers found after discovery.")




# Usage:
# file_path = '/home/ark/Pictures/Aman/photo_2024-12-05_16-33-09.jpg'
# sender = NetworkFileSender(file_path)
# sender.start_sending()
