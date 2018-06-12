import os
import pygame

import MMX_Combat.constants as CN

from MMX_Combat.enemies import BaseEnemy

from abc import ABCMeta, abstractmethod


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

class Level(object):
    """Generic Base Level class"""
    def __init__(self):
        self.wall_list = pygame.sprite.Group()
        self.misc_objs = pygame.sprite.Group()
        self.npc_enemies = pygame.sprite.Group()
        self.all_sprite_list = pygame.sprite.Group()
        self.players = pygame.sprite.Group()

    def update(self):
        self.wall_list.update()
        self.misc_objs.update()
        self.all_sprite_list.update()

    def draw(self, screen):
        screen.fill(BLACK)
        self.wall_list.draw(screen)
        self.misc_objs.draw(screen)
        self.all_sprite_list.draw(screen)

class TestLevel(Level):
    def __init__(self):
        super().__init__()

        self.spawn_points = []
        self.enemy_spawn_points = []

        level_path = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "levels", "level_01.txt"))
        print(level_path)
        with open(level_path) as level:
            l = level.readlines()
            for y, line in enumerate(l):
                for x, char in enumerate(line):
                    if char in ("M","X"):
                        # TODO: Build fewer objects. I believe this is what's messing with some of the collisions
                        wall = BaseEnvironmentObj(x*CN.LEVEL_TILE_SIZE,y*CN.LEVEL_TILE_SIZE,CN.LEVEL_TILE_SIZE,CN.LEVEL_TILE_SIZE)
                        self.all_sprite_list.add(wall)
                        self.wall_list.add(wall)

                    if char in ("E"):
                        self.enemy_spawn_points.append([x*CN.LEVEL_TILE_SIZE, y*CN.LEVEL_TILE_SIZE])
                    # Find spawn points (max 10 for now)
                    if char in [str(c) for c in range(0,10)]:
                        # print(f"Found spawn point {char}!")
                        self.spawn_points.append([x*CN.LEVEL_TILE_SIZE, y*CN.LEVEL_TILE_SIZE])

        # print([len(line)*CN.LEVEL_TILE_SIZE,len(l)*CN.LEVEL_TILE_SIZE])
        self.width = len(line)*CN.LEVEL_TILE_SIZE
        self.height = len(l)*CN.LEVEL_TILE_SIZE
        self.build_enemies()

    def build_enemies(self):
        # print("I'm building my enemies now, yo.")
        for point in self.enemy_spawn_points:
            _ = BaseEnemy(*point, 40, 40, self, 3)
            self.all_sprite_list.add(_)
            self.npc_enemies.add(_)
