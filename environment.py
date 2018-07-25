import os
import sys
import json
import pygame
import traceback
import more_itertools as mit

import MMX_Combat.constants as CN

from MMX_Combat.enemies import BaseEnemy
from MMX_Combat.player import RemotePlayerObj
from MMX_Combat.network.client import MMXClient

from abc import ABCMeta, abstractmethod

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
        self.collide_damage = 900

class Level(object):
    """Generic Base Level class"""
    def __init__(self, server_ip, server_port, username):
        self.wall_list = pygame.sprite.Group()
        self.misc_objs = pygame.sprite.Group()
        self.npc_enemies = pygame.sprite.Group()
        self.all_sprite_list = pygame.sprite.Group()
        self.players = pygame.sprite.Group()
        self.player_names = set()
        self.spawn_points = []
        self.enemy_spawn_points = []
        self.server_addr = server_ip, server_port
        self.player_data = dict()
        self.chat_client = MMXClient(*self.server_addr, username, self )

    def print_data_cache(self):
        print(json.dumps(self.player_data, indent=4))

    def update(self):
        self.wall_list.update()
        self.misc_objs.update()
        self.all_sprite_list.update()

    def draw(self, screen):
        screen.fill(BLACK)
        self.wall_list.draw(screen)
        self.misc_objs.draw(screen)
        self.all_sprite_list.draw(screen)

    def build_level_objs(self, level_path):
        wall_locations_v_lines = []
        wall_locations_y_lines = []
        with open(level_path) as level:
            l = level.readlines()
            for y, line in enumerate(l):
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
                        # print(f"Found spawn point {char}!")
                        self.spawn_points.append([x*CN.LEVEL_TILE_SIZE, y*CN.LEVEL_TILE_SIZE])

            self._parse_walls(wall_locations_v_lines)

            self.width = len(line)*CN.LEVEL_TILE_SIZE
            self.height = len(l)*CN.LEVEL_TILE_SIZE
        # self.build_enemies()

    def _parse_walls(self, wall_block_list):
        wall_groups = dict()
        for block in wall_block_list:
            # wall_groups.get(block[1], []).append(block[0])
            # print(block)
            if wall_groups.get(block[0], None) == None:
                wall_groups[block[0]] = []
            wall_groups[block[0]].append(block[1])
        # print(wall_groups)
        wall_objs = dict()
        for k,v in sorted(wall_groups.items()):
            # print(k)
            wall_objs[k] = list(find_ranges(v))
            for b in wall_objs[k]:
                # print(f"\t{b}")
                if isinstance(b, int):
                    wall = BaseEnvironmentObj(k*CN.LEVEL_TILE_SIZE,b*CN.LEVEL_TILE_SIZE,CN.LEVEL_TILE_SIZE,CN.LEVEL_TILE_SIZE)
                else:
                    wall = BaseEnvironmentObj(k*CN.LEVEL_TILE_SIZE,(b[0])*CN.LEVEL_TILE_SIZE,CN.LEVEL_TILE_SIZE,((b[1]-b[0]+1)*CN.LEVEL_TILE_SIZE))
                self.all_sprite_list.add(wall)
                self.wall_list.add(wall)

        # print(wall_objs)

    def build_enemies(self):
        # print("I'm building my enemies now, yo.")
        for point in self.enemy_spawn_points:
            _ = BaseEnemy(*point, 40, 40, self, 3)
            self.all_sprite_list.add(_)
            self.npc_enemies.add(_)

    def update_player_data(self, username):
        # print(self.player_data.keys())
        for player_name, player_data in self.player_data.items():
            # print(player_name)
            try:
                if player_name not in self.player_names:
                    self.player_names.add(player_name)
                    print(f'{player_name} connected')
                    remote_player = RemotePlayerObj(player_data['un'], self, player_data['color'])
                    self.players.add(remote_player)
                    self.all_sprite_list.add(remote_player)
            except:
                print(traceback.format_exc())



class TestLevel(Level):
    def __init__(self, server_ip, server_port, username):
        super().__init__(server_ip, server_port, username)
        level_path = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "levels", "level_02.txt"))
        self.build_level_objs(level_path)
        self.build_enemies()
