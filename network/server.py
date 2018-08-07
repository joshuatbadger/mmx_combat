import os
os.environ["PYTHONDONTWRITEBYTECODE"] = 'stobbit'
import sys
import json
import pygame
import socket
import logging
import traceback

from time import sleep
from weakref import WeakKeyDictionary

from PodSixNet.Channel import Channel
from PodSixNet.Server import Server

logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')

try:
    from ..environment import TestLevel
    logging.info("Server successfully imported stuff!")
except (ValueError, ImportError):
    logging.warning("Server couldn't import.... try importing explicitly")

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
        # logging.debug(f"I think I got some data:\n{data}\n")
        pass

    def Network_updateclient(self, data):
        # logging.debug(f"Client wants me send them stuff!\n{data}")
        self._server.SendToAll()

    def Network_updateserver(self, data):
        # logging.debug(f"Client wants me to do something!")
        self._server.UpdateData(data)
        self._server.SendToAll()

    def Network_newconnection(self, data):
        # logging.debug(f"I have a new connection! (channel level)\n{data}")
        self.id = data['id']
        self._server.UpdateData(data)
        self._server.SendToAll()

class MMXServer(Server):

    channelClass = MMXClientChannel

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_cache = {'player': dict(), 'npc': dict(), 'weap': dict()}
        self.players = WeakKeyDictionary()
        self.update_interval = 0
        self.level = TestLevel(None, None, 'serverman', False, server_instance=self)
        logging.info(f"IP address: {get_lan_ip()}")

    def Connected(self, channel, addr):
        # logging.debug(f"We have a new connection from {addr}! (server level)")
        self.AddPlayer(channel)

    def AddPlayer(self, player):
        logging.info(f"New Player{str(player.addr)}")
        self.players[player] = True

    def DelPlayer(self, player):
        logging.info("Deleting Player" + str(player.addr))
        del self.data_cache['player'][player.id]
        del self.players[player]

    def UpdateData(self, data):
        try:
            # if data['type'] == 'player':

            # logging.debug(data)
            self.data_cache[data['type']][data['id']] = data.get('data', dict())
            # elif data['type'] == 'npc':
            #     self.data_cache[data['npc']]
            # else:
            #     self.data_
            # logging.debug(self.data_cache)
        except:
            logging.warning("Something broke in update data!")
            logging.warning(traceback.format_exc())
            logging.warning(data)

    def SendToAll(self):
        # logging.debug("Current data_cache: ")
        # logging.debug(self.data_cache)
        [p.Send({'action': 'updatefromserver', 'data': self.data_cache}) for p in self.players]

    def CalcAndPump(self):
        self.level.update_player_data()
        self.level.update_npc_data()
        self.level.all_sprite_list.update()
        self.Pump()



if __name__ == '__main__':
    mmx_main_path = os.path.normpath(os.path.join(os.path.realpath(__file__), "..", "..", ".."))
    if mmx_main_path not in sys.path:
        sys.path.append(mmx_main_path)
    os.system("cls")
    # args = get_args()
    server = MMXServer(localaddr=('localhost', 12000))
    logging.info(server)
    while True:
        server.CalcAndPump()
        sleep(0.0001)
