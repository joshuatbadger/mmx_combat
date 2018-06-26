from datetime import datetime

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
        self.spawn_point = (x,y)

        self.health = health
        self.level = level
        self.waiting = 0
        self.following = 0
        self.target = None

        self.x_velocity = 0
        self.y_velocity = 0

        self.collide_damage = 1
        # print("I'm a new enemy!")

    def damage(self, amount):
        # print("Ouch!")
        self.health -= amount
        # pass

    def attack(self, target):
        # print(f"Attacking {target.username}!")
        self.level.all_sprite_list.add(EnemyBuster1(self))
        self.waiting = 60

    def follow(self, target):
        # TODO: Build out
        # print(f"Following {target.username}!")
        if self.following == 0:
            self.following = 45
        else:
            self.following -=1

        if self.following == 0:
            self.waiting = 60
        else:
            hypot = math.hypot(self.target.rect.x - self.rect.x, self.target.rect.y - self.rect.y) / (CN.RUN_SPEED*.5)
            if hypot == 0:
                hypot = 1
            self.x_velocity = ((self.target.rect.x + self.rect.width/2) - (self.rect.x + self.rect.width/2)) / hypot
            self.y_velocity = ((self.target.rect.y + self.rect.height/2) - (self.rect.y + self.rect.height/2)) / hypot


    def patrol(self):
        if not self.target:
            # Find closest target
            old_dist = 5000
            for player in self.level.players:
                new_dist = math.hypot(player.rect.x - self.rect.x, player.rect.y - self.rect.y)
                if new_dist <= CN.SCREEN_HREZ/2 and new_dist < old_dist:
                    self.target = player
                    self.waiting = 60
            # if not self.target:

        else:
            # Confirm the target is close enough to attack
            dist = math.hypot(self.target.rect.x - self.rect.x, self.target.rect.y - self.rect.y)
            if dist > 600:
                self.target = None
            else:
                # We're close enough, attack!
                [self.attack, self.follow][datetime.now().time().microsecond % 2](self.target)

    def update(self):
        if self.health <= 0:
            self.kill()
        if not self.following and not self.waiting:
            self.patrol()
        elif self.following:
            self.follow(self.target)
            self.rect.x += self.x_velocity
            self.rect.y += self.y_velocity
        elif self.waiting:
            self.waiting -=1
