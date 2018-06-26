import os
import sys
import json
import random
import socket

# Code largely copied from https://stackoverflow.com/a/27893987

# Create a UDP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(('', 12000))

if os.name != "nt":
    import fcntl
    import struct

    def get_interface_ip(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s',
                                ifname[:15]))[20:24])

def get_lan_ip():
    ip = socket.gethostbyname(socket.gethostname())
    if ip.startswith("127.") and os.name != "nt":
        interfaces = [
            "eth0",
            "eth1",
            "eth2",
            "wlan0",
            "wlan1",
            "wifi0",
            "ath0",
            "ath1",
            "ppp0",
            ]
        for ifname in interfaces:
            try:
                ip = get_interface_ip(ifname)
                break
            except IOError:
                pass
    return ip

def main():
    os.system('cls')

    server_ip = get_lan_ip()

    try:
        print("Starting server...")
        running = True
        times = 0
        current_player_set = dict()
        # while running:
        while times < 5:
            rec_message, address = server_socket.recvfrom(1024)
            message_dict = json.loads(rec_message.decode('utf-8'))
            print(f"Received data from {message_dict['username']} at {address}")
            # print(f"\t{message_dict.get('check_server', None)}")
            if message_dict.get('check_server', False):
                ret_message = json.dumps({'server_address': server_ip}).encode('utf-8')
                server_socket.sendto(ret_message, address)
            elif message_dict.get('sending_update', False):
                # print(f"{message_dict['username']} is sending me info!")
                current_player_set[message_dict['username']] = message_dict
            elif message_dict.get('get_update', False):
                # print(f"{message_dict['username']} wants an update!")
                ret_message = json.dumps(current_player_set).encode('utf-8')
                server_socket.sendto(ret_message, address)
            else:
                current_player_set[message_dict['username']] = message_dict
                ret_message = json.dumps(current_player_set).encode('utf-8')
                server_socket.sendto(ret_message, address)
            # print(f'returning message "{ret_message}"...')

            # times += 1
    except KeyboardInterrupt:
        print("Quitting server...")
        sys.exit()


if __name__ == '__main__':
    main()
