import os
import math
import pygame

import MMX_Combat.constants as CN
from MMX_Combat.weapons import EnemyBuster1

from abc import ABCMeta, abstractmethod


class BaseEnemy(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, level, health):
        # call parent's constructor
        super().__init__()

        # Make a box of specified size for the enemy, make magenta
        self.image = pygame.Surface([width, height])
        self.image.fill(CN.MAGENTA)

        # Make our top-left corner the passed-in location.
        self.rect = self.image.get_rect()
        self.rect.y = y
        self.rect.x = x

        self.health = health
        self.level = level
        self.waiting = 0
        self.target = None
        print("I'm a new enemy!")

    def damage(self, amount):
        print("Ouch!")
        self.health -= amount
        # pass

    def attack(self, target):
        # TODO: Build out
        # print(f"Attacking {target.username}!")
        self.level.all_sprite_list.add(EnemyBuster1(self))
        self.waiting = 60
        pass

    def patrol(self):
        if not self.target:
            # Find closest target
            old_dist = 5000
            for player in self.level.players:
                new_dist = math.hypot(player.rect.x - self.rect.x, player.rect.y - self.rect.y)
                if new_dist <= CN.SCREEN_HREZ/2 and new_dist < old_dist:
                    self.target = player
                    self.waiting = 60
        else:
            # Confirm the target is close enough to attack
            dist = math.hypot(self.target.rect.x - self.rect.x, self.target.rect.y - self.rect.y)
            if dist > 600:
                self.target = None
            else:
                # We're close enough, attack!
                self.attack(self.target)

    def update(self):
        # print(f"Updating enemy {id(self)}")
        if self.health <= 0:
            self.kill()
        if not self.waiting:
            self.patrol()
        else:
            self.waiting -=1
