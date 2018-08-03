import os
os.environ["PYTHONDONTWRITEBYTECODE"] = 'stobbit'
import sys
import json
import pygame
import socket

from time import sleep
from weakref import WeakKeyDictionary

from PodSixNet.Channel import Channel
from PodSixNet.Server import Server

try:
    from .. import environment
    print("Server successfully imported stuff!")
except (ValueError, ImportError):
    print("Server couldn't import.... try importing explicitly")

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

class MMXClientChannel(Channel):

    def Close(self):
        self._server.DelPlayer(self)

    def Network(self, data):
        # print(f"I think I got some data:\n{data}\n")
        pass

    def Network_updateclient(self, data):
        # print(f"Client wants me send them stuff!\n{data}")
        self._server.SendToAll()

    def Network_updateserver(self, data):
        # print(f"Client wants me to do something!")
        self._server.UpdateData(data)
        self._server.SendToAll()

    def Network_newconnection(self, data):
        # print(f"I have a new connection! (channel level)\n{data}")
        self.username = data['un']

class MMXServer(Server):

    channelClass = MMXClientChannel

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_cache = dict()
        self.players = WeakKeyDictionary()
        # self.level =
        print(f"IP address: {get_lan_ip()}")

    def Connected(self, channel, addr):
        # print(f"We have a new connection from {addr}! (server level)")
        self.AddPlayer(channel)

    def AddPlayer(self, player):
        print("New Player" + str(player.addr))
        self.players[player] = True

    def DelPlayer(self, player):
        print("Deleting Player" + str(player.addr))
        del self.data_cache[player.username]
        del self.players[player]

    def UpdateData(self, data):
        try:
            self.data_cache[data['un']] = data['data']
            # print(self.data_cache)
        except:
            print("Something broke in update data!")

    def SendToAll(self):
        # print("Current data_cache: ")
        # print(self.data_cache)
        [p.Send({'action': 'updatefromserver', 'data': self.data_cache}) for p in self.players]

    def CalcAndPump(self,i):
        # Game loop goes here?
        # print(i)
        # if i%3 == 0:
        #     print("Run Game loop here!")
        self.Pump()



if __name__ == '__main__':
    mmx_main_path = os.path.normpath(os.path.join(os.path.realpath(__file__), "..", "..", ".."))
    if mmx_main_path not in sys.path:
        sys.path.append(mmx_main_path)
    os.system("cls")
    # args = get_args()
    server = MMXServer(localaddr=('localhost', 12000))
    print(server)
    while True:
        server.CalcAndPump(i)
        sleep(0.0001)
