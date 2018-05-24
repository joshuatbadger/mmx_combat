import pygame

import MMX_Combat.constants as CN

from abc import ABCMeta, abstractmethod


class BaseEnvironmentObj(pygame.sprite.Sprite):
    def __init__(self,x,y,width, height):
        # call parent's constructor
        super().__init__()

        # Make a blue wall, of the size specified in the parameters
        self.image = pygame.Surface([width, height])
        self.image.fill((128,128,128))

        # Make our top-left corner the passed-in location.
        self.rect = self.image.get_rect()
        self.rect.y = y
        self.rect.x = x

class Level(object):
    """Generic Base Level class"""
    def __init__(self):
        self.wall_list = pygame.sprite.Group()
        self.misc_objs = pygame.sprite.Group()
        self.all_sprite_list = pygame.sprite.Group()

    def update(self):
        self.wall_list.update()
        self.misc_objs.update()
        self.all_sprite_list.update()

    def draw(self, screen):
        screen.fill(BLACK)
        self.wall_list.draw(screen)
        self.misc_objs.draw(screen)

class TestLevel(Level):
    def __init__(self):
        super().__init__()

        # Create list of all walls/obstacles and add them to sprite lists

        wall_specs = [(0,CN.SCREEN_HEIGHT-100,CN.SCREEN_WIDTH,25),
                      (0,0,25,CN.SCREEN_HEIGHT-100),
                      (CN.SCREEN_WIDTH-25,0,25,CN.SCREEN_HEIGHT-100),
                      (300, CN.SCREEN_HEIGHT - 200, 200, 25),
                      (625, CN.SCREEN_HEIGHT - 300, 200, 25),
                      ]

        for wall_spec in wall_specs:
            wall = BaseEnvironmentObj(*wall_spec)
            self.all_sprite_list.add(wall)
            self.wall_list.add(wall)
