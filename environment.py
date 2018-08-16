import os
import pdb
import sys
import json
import time
import pygame
import logging
import threading
import traceback
import more_itertools as mit

import MMX_Combat.constants as CN

import MMX_Combat.enemies as enemies
import MMX_Combat.weapons as weapons
from MMX_Combat.player import BasePlayerObj, RemotePlayerObj
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
        self.weapon_ids = set()
        self.weapons = pygame.sprite.Group()
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
            self.data_cache = {'player': {}, 'npc': {}, 'weapon': {}}


    def print_data_cache(self):
        logging.debug('--------------------------PRINTING LEVEL CACHE---------------------------------')
        logging.debug(json.dumps(self.data_cache, indent=4, sort_keys=True))
        logging.debug('-------------------------------------------------------------------------------')

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
                    # self.npc_enemies.add(wall)
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
        if not network:
            for i, point in enumerate(self.enemy_spawn_points):
                _ = enemies.BaseEnemy(i, *point, 40, 40, self, 3)
                self.all_sprite_list.add(_)
                self.npc_enemies.add(_)
                self.npc_ids.add(_.id)

        else:
            pass

    def update_player_data(self):
        for player_name, player_data in self.data_cache['player'].items():
            try:
                if player_name not in self.player_names:
                    # Newly connected player! Do things!
                    self.player_names.add(player_name)
                    logging.info(f'{self.level_id} - {player_name} connected')
                    player_color = player_data.get('color', None)
                    if player_color == None:
                        raise KeyError(f"Full player data for {player_name} hasn't been set yet, try again next frame")
                    remote_player = RemotePlayerObj(player_name, self, player_color)
                    self.players.add(remote_player)
                    self.all_sprite_list.add(remote_player)
            except KeyError as e:
                # Didn't have full data, clean up and move on.
                # This is expected on initial connection once or twice.
                logging.warning('Stuff broke, yo.')
                logging.debug(f'{json.dumps(player_data, indent=4, sort_keys=True)}')
                try:
                    self.players.remove(remote_player)
                    self.all_sprite_list.remove(remote_player)
                except UnboundLocalError:
                    pass
                self.player_names.remove(player_name)
                logging.warning(traceback.format_exc())
            except:
                logging.warning(traceback.format_exc())

    def update_npc_data(self):
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
                        new_npc = enemies.BaseEnemy(npc_id, npc_data['x'], npc_data['y'], npc_data['width'], npc_data['height'], self, npc_data['health'], from_network=True)
                        self.all_sprite_list.add(new_npc)
                except KeyError as e:
                    logging.debug(f'{json.dumps(self.data_cache, indent=4, sort_keys=True)}')
                    logging.warning(traceback.format_exc())
                    sys.exit(9)
                except:
                    logging.warning(traceback.format_exc())

            for npc in self.npc_enemies:
                if npc.health <= 0:
                    npc.destroy()

        except RuntimeError:
            # logging.info(f"Data!\n{json.dumps(self.data_cache['npc'], indent=4)}")
            sys.exit(8)

    def update_weapon_data(self):
        try:
            # pdb.set_trace()
            weapon_cache = self.data_cache['weapon'].items()
            for weapon_id, weapon_data in weapon_cache:
                if weapon_data == {}:
                    # Haven't populated the data yet. Ignore.
                    continue
                try:
                    logging.debug(f"Current weapon ids: {self.weapon_ids}")
                    logging.debug(f"this id: {weapon_id}")
                    if weapon_id not in self.weapon_ids:
                        # We aren't tracking this weapon yet, add it, pls.
                        # Get data from the recently ingested data cache
                        logging.debug(f'Found new weapon.... {weapon_id}')
                        self.weapon_ids.add(weapon_id)
                        weapon_type_name, weapon_parent_name, _ = weapon_id.split("_")
                        weapon_type = getattr(weapons, weapon_type_name)
                        # Find the weapon's parent. If this fails we have a problem. Recently disconnected user, possibly?
                        weapon_parent = [player for player in self.players if player.id == weapon_parent_name][0]
                        new_weapon_dict = {}
                        new_weapon_dict['parent'] = weapon_parent
                        new_weapon_dict['id'] = weapon_data.get('id', None)
                        new_weapon_dict['energy'] = weapon_data.get('energy', None)
                        new_weapon_dict['size']   = (weapon_data.get('width', None), weapon_data.get('height', None))
                        new_weapon_dict['color']  = weapon_data.get('color', None)
                        new_weapon_dict['destroyed_by_enemies'] = weapon_data.get('destroyed_by_enemies', None)
                        new_weapon_dict['rem_frames'] = weapon_data.get('rem_frames', None)
                        new_weapon_dict['velocity_magnitudes']   = (weapon_data.get('x_velocity', None), weapon_data.get('y_velocity', None))
                        new_weapon_dict['position_override']   = (weapon_data.get('x', None), weapon_data.get('y', None))

                        new_weapon = weapon_type(**new_weapon_dict)
                        self.all_sprite_list.add(new_weapon)
                        self.weapons.add(new_weapon)

                except:
                    logging.warning(traceback.format_exc())


            if len(weapon_cache) != len(self.weapon_ids):
                # We've just added all the weapons the cache has, so we must
                # need to kill some weapons that are no longer in the level
                # Create sets for what weapons are in the cache and what weapons
                # we'll want to destroy (can't destroy during iteration, causes
                # RuntimeError)
                weapon_cache_ids = {x[0] for x in weapon_cache}
                weapons_to_destroy = set()
                for obsolete_weapon_id in self.weapon_ids:
                    if obsolete_weapon_id not in weapon_cache_ids:
                        # Found a weapon id that should die. Kill it.
                        for weapon in self.weapons:
                            if weapon.id == obsolete_weapon_id:
                                if weapon.waiting_for_server < 1:
                                    # Destroy the weapon, we haven't gotten
                                    # an update in too long
                                    weapons_to_destroy.add(weapon)
                                else:
                                    # Decrement the weapon's update waiter
                                    weapon.waiting_for_server -= 1
                    else:
                        for weapon in self.weapons:
                            # Reset update counter to 3 in case of bad connection
                            if weapon.id == obsolete_weapon_id:
                                weapon.waiting_for_server = 3
                # Finally destroy the weapons
                for dead_weapon in weapons_to_destroy:
                    dead_weapon.destroy()

        except RuntimeError:
            # Not sure what happened here
            logging.error("I am so broken...")
            logging.error(traceback.format_exc())
            sys.exit(8)

    def update_data(self):
        self.update_player_data()
        self.update_npc_data()
        self.update_weapon_data()
        keylist = list(self.data_cache.keys())
        for key in keylist:
            if key not in ('player', 'npc', 'weapon'):
                logging.warning(f"Popping {key}")
                self.data_cache.pop(key)


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
