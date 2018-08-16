import os
os.environ["PYTHONDONTWRITEBYTECODE"] = 'stobbit'
import pdb
import sys
import copy
import json
import pygame
import socket
import logging
import threading
import traceback

from time import sleep
from weakref import WeakKeyDictionary

from PodSixNet.Channel import Channel
from PodSixNet.Server import Server

import MMX_Combat.constants as CN

logging.basicConfig(level=logging.DEBUG, format=CN.LOG_FMT)

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

DEFAULT_PLAYER_DICT = {
                        "B_H": 16,
                        "C_A_D": False,
                        "DELAY_JUMP_PERIOD": 4,
                        "D_M": 2,
                        "D_T": 10,
                        "G": 2,
                        "J_S": 22,
                        "M_S": 3,
                        "R_S": 10,
                        "S_V": 5,
                        "W_D_S": 6,
                        "W_J_V": 3,
                        "c_d": False,
                        "c_j": True,
                        "c_l": 0,
                        "color": "BLUE",
                        "cur_alt_weapon": 0,
                        "d_w": 0,
                        "dashing": -1,
                        "delay_jump": 4,
                        "dir": "right",
                        "ducking": False,
                        "fire_wait": 0,
                        "firing": False,
                        "height": 42,
                        "hp": 16,
                        "inv": 0,
                        "o_g": True,
                        "run": False,
                        "t_d": -1,
                        "v_h": 0,
                        "w_c": False,
                        "w_h": False,
                        "w_m_f_w": False,
                        "width": 20,
                        "x": -100,
                        "x_v": 0,
                        "y": -100,
                        "y_v": 0
                      }

class MMXClientChannel(Channel):

    def Close(self):
        self._server.DelPlayer(self)

    def Network(self, data):
        # logging.debug(f"I think I got some data:\n{data}\n")
        pass

    def Network_updateserver(self, data):
        self._server.UpdateData(data)
        self._server.SendToAll()

    def Network_newconnection(self, data):
        # logging.debug(f"I have a new connection! (channel level)\n{data}")
        self.id = data['id']
        self.Network_updateserver(data)

class MMXServer(Server):

    channelClass = MMXClientChannel

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_cache = {'player': {}, 'npc': {}, 'weapon': {}}
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
        # logging.debug(json.dumps(self.data_cache, indent=4, sort_keys=True))

    def DelPlayer(self, player):
        logging.info("Deleting Player" + str(player.addr))
        del self.data_cache['player'][player.id]
        del self.players[player]

    def UpdateData(self, data):
        try:
            # pdb.set_trace()
            type = data['type']
            id = data['id']
            self.data_cache[type][id] = data.get('data', {})
        except:
            logging.warning("Something broke in update data!")
            logging.warning(traceback.format_exc())
            logging.warning(data)


    def SendToAll(self):
        # confirm all player keys are in data cache before sending?
        try:
            temp_dict = copy.deepcopy(self.data_cache)
            # logging.debug('Checking player cache')
            for k, v in temp_dict['player'].items():
                if v.get('x', None) == None:
                    logging.debug(f'{k} is not ready for sending yet, pop it out')
                    temp_dict['player'].pop(k)

            keylist = list(temp_dict.keys())
            for key in keylist:
                if key not in ('player', 'npc', 'weapon'):
                    temp_dict.pop(key)
                    self.data_cache.pop(key)
            [p.Send({'action': 'updatefromserver', 'data': temp_dict}) for p in self.players]
        except (AttributeError, RuntimeError) as e:
            logging.warning(traceback.format_exc())
            logging.warning("Skipping update this frame")
        except:
            logging.error(traceback.format_exc())

    def CalcAndPump(self):
        self.level.update_data()
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
