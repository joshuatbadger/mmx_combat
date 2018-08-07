import os
import sys
import json
import time
import pygame
import logging
import traceback
import more_itertools as mit

import MMX_Combat.constants as CN

from MMX_Combat.enemies import BaseEnemy
from MMX_Combat.player import RemotePlayerObj
from MMX_Combat.network.client import MMXClient

from abc import ABCMeta, abstractmethod

logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')

def find_ranges(iterable):
    """Yield range of consecutive numbers."""
    for group in mit.consecutive_groups(iterable):
        group = list(group)
        if len(group) == 1:
            yield group[0]
        else:
            yield group[0], group[-1]

class BaseEnvironmentObj(pygame.sprite.Sprite):
    def __init__(self,x,y,width, height):
        # call parent's constructor
        super().__init__()

        # Make a grey wall, of the size specified in the parameters
        self.image = pygame.Surface([width, height])
        self.image.fill((128,128,128))

        # Make our top-left corner the passed-in location.
        self.rect = self.image.get_rect()
        self.rect.y = y
        self.rect.x = x

    def damage(self, amount):
        pass

class SpikeWall(BaseEnvironmentObj):
    def __init__(self,x,y,width,height):
        super().__init__(x,y,width,height)
        self.image.fill(CN.RED)
        self.collide_damage = 9000

class Level(object):
    """Generic Base Level class"""
    def __init__(self, server_ip, server_port, id, network=True, server_instance=None):
        self.level_id = f'{"server_" if server_instance else ""}{time.time_ns()}'
        logging.info(f"LEVEL_ID: {self.level_id}")
        self.wall_list = pygame.sprite.Group()
        self.misc_objs = pygame.sprite.Group()
        self.npc_enemies = pygame.sprite.Group()
        self.npc_ids = set()
        self.all_sprite_list = pygame.sprite.Group()
        self.players = pygame.sprite.Group()
        self.player_names = set()
        self.spawn_points = []
        self.enemy_spawn_points = []
        if network:
            self.server_addr = server_ip, server_port
            self.chat_client = MMXClient(*self.server_addr, id, self )
        else:
            self.server_addr = None
            self.chat_client = None

        if server_instance:
            self.server = server_instance
            logging.debug(f"Server instance: {self.server}")
            self.data_cache = self.server.data_cache

        else:
            self.server = None
            self.data_cache = {'player': dict(), 'npc': dict(), 'weap': dict()}


    def print_data_cache(self):
        logging.debug(json.dumps(self.data_cache, indent=4))

    def update(self):
        self.wall_list.update()
        self.misc_objs.update()
        self.all_sprite_list.update()

    def draw(self, screen):
        screen.fill(BLACK)
        self.wall_list.draw(screen)
        self.misc_objs.draw(screen)
        self.all_sprite_list.draw(screen)

    def build_level(self, level_path, network=True):
        with open(level_path) as level:
            l = level.readlines()
        self.build_level_objs(l)

    def build_level_objs(self, level_lines):
        wall_locations_v_lines = []
        wall_locations_y_lines = []
        for y, line in enumerate(level_lines):
            for x, char in enumerate(line):
                if char in ("X","Y"):
                    wall_locations_v_lines.append((x,y))
                elif char in ("<", ">", "^", "V"):
                    wall = SpikeWall(x*CN.LEVEL_TILE_SIZE, y*CN.LEVEL_TILE_SIZE, CN.LEVEL_TILE_SIZE, CN.LEVEL_TILE_SIZE)
                    self.npc_enemies.add(wall)
                    self.all_sprite_list.add(wall)
                elif char in ("E"):
                    self.enemy_spawn_points.append([x*CN.LEVEL_TILE_SIZE, y*CN.LEVEL_TILE_SIZE])
                # Find spawn points (max 10 for now)
                elif char in [str(c) for c in range(0,10)]:
                    # logging.debug(f"Found spawn point {char}!")
                    self.spawn_points.append([x*CN.LEVEL_TILE_SIZE, y*CN.LEVEL_TILE_SIZE])

        self._parse_walls(wall_locations_v_lines)

        self.block_width = len(line)
        self.width = self.block_width*CN.LEVEL_TILE_SIZE
        self.block_height = len(level_lines)
        self.height = self.block_height*CN.LEVEL_TILE_SIZE
        # self.build_enemies()

    def _parse_walls(self, wall_block_list):
        wall_groups = dict()
        for block in wall_block_list:
            # wall_groups.get(block[1], []).append(block[0])
            # logging.debug(block)
            if wall_groups.get(block[0], None) == None:
                wall_groups[block[0]] = []
            wall_groups[block[0]].append(block[1])
        # logging.debug(wall_groups)
        wall_objs = dict()
        for k,v in sorted(wall_groups.items()):
            # logging.debug(k)
            wall_objs[k] = list(find_ranges(v))
            for b in wall_objs[k]:
                # logging.debug(f"\t{b}")
                if isinstance(b, int):
                    wall = BaseEnvironmentObj(k*CN.LEVEL_TILE_SIZE,b*CN.LEVEL_TILE_SIZE,CN.LEVEL_TILE_SIZE,CN.LEVEL_TILE_SIZE)
                else:
                    wall = BaseEnvironmentObj(k*CN.LEVEL_TILE_SIZE,(b[0])*CN.LEVEL_TILE_SIZE,CN.LEVEL_TILE_SIZE,((b[1]-b[0]+1)*CN.LEVEL_TILE_SIZE))
                self.all_sprite_list.add(wall)
                self.wall_list.add(wall)

        # logging.debug(wall_objs)

    def build_enemies(self, network=False):
        # logging.debug("I'm building my enemies now, yo.")
        if not network:
            for i, point in enumerate(self.enemy_spawn_points):
                _ = BaseEnemy(i, *point, 40, 40, self, 3)
                self.all_sprite_list.add(_)
                self.npc_enemies.add(_)
                self.npc_ids.add(_.id)

        else:
            pass

    def update_player_data(self):
        # logging.debug(self.data_cache.keys())
        for player_name, player_data in self.data_cache['player'].items():
            # logging.debug(player_name)
            try:
                if player_name not in self.player_names:
                    self.player_names.add(player_name)
                    logging.info(f'{self.level_id} - {player_name} connected')
                    # logging.debug(f'{json.dumps(player_data, indent=4, sort_keys=True)}')
                    remote_player = RemotePlayerObj(player_data.get('id'), self, player_data.get('color', 'MAGENTA'))
                    self.players.add(remote_player)
                    self.all_sprite_list.add(remote_player)
            except KeyError as e:
                logging.warning('Stuff broke, yo.')
                self.players.remove(remote_player)
                self.all_sprite_list.remove(remote_player)
                pass
            except:
                logging.warning(traceback.format_exc())

    def update_npc_data(self):
        # logging.debug(self.level_id)
        # logging.debug(self.data_cache)
        # return
        # logging.info(f"Data!\n{json.dumps(self.data_cache['npc'], indent=4)}")
        try:
            for npc_id, npc_data in self.data_cache['npc'].items():
                if npc_data == {}:
                    continue
                # logging.debug(f'{npc_id}: {npc_data}')
                try:
                    if npc_id not in self.npc_ids:
                        self.npc_ids.add(npc_id)
                        # logging.debug(f'Got new NPC "{npc_id}"')
                        # logging.debug(f'{json.dumps(npc_data, indent=4)}"')
                        new_npc = BaseEnemy(npc_id, npc_data['x'], npc_data['y'], npc_data['width'], npc_data['height'], self, npc_data['health'], from_network=True)
                        self.all_sprite_list.add(new_npc)
                except KeyError as e:
                    logging.debug(f'{json.dumps(self.data_cache, indent=4, sort_keys=True)}')
                    logging.warning(traceback.format_exc())
                    sys.exit(9)
                except:
                    logging.warning(traceback.format_exc())

        except RuntimeError:
            # logging.info(f"Data!\n{json.dumps(self.data_cache['npc'], indent=4)}")
            sys.exit(8)


class RemoteLevel(Level):
    def __init__(self, server_ip, server_port, id):
        super().__init__('127.0.0.1', 12000, 'Server')


class TestLevel(Level):
    def __init__(self, server_ip, server_port, id, network=True, server_instance=False):
        super().__init__(server_ip, server_port, id, network, server_instance=server_instance)
        level_path = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "levels", "level_02.txt"))
        self.build_level(level_path)
        self.build_enemies()

class ServerTestLevel(Level):
    def __init__(self, server_ip, server_port, id, network=True, server_instance=None):
        super().__init__(server_ip, server_port, id, network, server_instance=server_instance)
        level_path = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "levels", "level_02.txt"))
        self.build_level(level_path)
        # self.build_enemies()

    # def build_level(level_path):
        # self.server.

    # def build_enemies(self):
    #     # logging.debug("I'm building my enemies now, yo.")
    #     for i, point in enumerate(self.enemy_spawn_points):
    #         _ = BaseEnemy(i, *point, 40, 40, self, 3, from_network=True)
    #         self.all_sprite_list.add(_)
    #         self.npc_enemies.add(_)
