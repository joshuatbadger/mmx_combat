from datetime import datetime

import os
import math
import json
import pygame
import random
import logging
import traceback

import MMX_Combat.constants as CN
from MMX_Combat.weapons import EnemyBuster1

from abc import ABCMeta, abstractmethod

logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')

class BaseEnemy(pygame.sprite.Sprite):
    def __init__(self, id, x, y, width, height, level, health, from_network=False):
        # call parent's constructor
        super().__init__()

        self.id = f'{self.__class__.__name__}_{id}' if isinstance(id, int) else id
        # Determine which update function to use based on whether calculations
        # are done on the server or local
        self.update = self.update_remote if from_network else self.update_local
        # logging.warning(f"Current update method: {self.update.__name__}")

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
        # logging.info(f'{self.level.server} - I am enemy {self.id}')
        self.level.data_cache['npc'][self.id] = self.build_npc_dict()
        # logging.debug("I'm a new enemy!")

    def damage(self, amount):
        # logging.debug("Ouch!")
        self.health -= amount
        # pass

    def attack(self):
        # logging.debug(f"Attacking {target.id}!")
        self.level.all_sprite_list.add(EnemyBuster1(self))
        self.waiting = 60

    def follow(self):
        # TODO: Build out
        # logging.debug(f"Following {self.target.id}!")
        if self.following == 0:
            self.following = 45
        else:
            self.following -=1

        if self.following == 0:
            self.waiting = 60
        else:
            hypot = math.hypot(self.target.rect.centerx - self.rect.centerx, self.target.rect.centery - self.rect.centery) / (CN.RUN_SPEED*.5)
            if hypot == 0:
                hypot = 1
            if hypot < self.rect.width / 6:
                self.x_velocity = 0
                self.y_velocity = 0
                self.waiting = 60
                self.following = 0
            else:
                self.x_velocity = (self.target.rect.centerx - self.rect.centerx) / hypot
                self.y_velocity = (self.target.rect.centery - self.rect.centery) / hypot


    def patrol(self):
        # Find closest target
        old_dist = 5000
        # if self.id == 'BaseEnemy_0':
        #     logging.debug("I'm patrolling")
        me_rect = self.rect

        for player in self.level.players:
            new_dist = math.hypot(player.rect.centerx - self.rect.centerx, player.rect.centery - self.rect.centery)
            # if self.id == 'BaseEnemy_0':
            #     logging.debug(f"Distance to potential new target: {new_dist} Me: {self.rect.center}, Old Target: {player.rect.center}")
            if new_dist <= CN.SCREEN_HREZ/2 and new_dist < old_dist:
                old_dist = new_dist
            # if new_dist < old_dist:
                self.target = player
                # if self.id == 'BaseEnemy_0':
                #     logging.debug(f"I have a new target: {self.target.id}")
                self.waiting = 60

        if self.target:
            # Confirm the target is close enough to attack
            dist = math.hypot(self.target.rect.centerx - me_rect.centerx, self.target.rect.centery - me_rect.centery)
            if dist > 600: #TODO: Fix arbitrary number
                # logging.warning(f"Lost the target.... {dist}")
                self.target = None
            else:
                # We're close enough, attack!
                # random.choice([self.attack, self.follow])()
                self.follow()

    def update_local(self):
        if self.health <= 0:
            self.destroy()
        if not self.following and not self.waiting:
            self.patrol()
        elif self.following:
            self.follow()
            self.rect.x += self.x_velocity
            self.rect.y += self.y_velocity
        elif self.waiting:
            self.waiting -=1
        self.level.data_cache['npc'][self.id] = self.build_npc_dict()

    def update_remote(self):
        # logging.info(f'Updating: {self.id}')
        data = self.level.data_cache['npc']
        try:
            self.rect.x = data[self.id]['x']
            self.rect.y = data[self.id]['y']
        except:
            logging.error("Failed to update {self.id}")
            logging.error(f'{json.dumps(data, indent=4)}')

    def build_npc_dict(self):
        npc_dict = dict()
        npc_dict['x'] = self.rect.x
        npc_dict['y'] = self.rect.y
        npc_dict['width'] = self.rect.width
        npc_dict['height'] = self.rect.height
        npc_dict['health'] = self.health

        return npc_dict

    def destroy(self):
        # TODO: rather than kill, keep in memory so we can respawn once
        # players are far enough away
        logging.debug(f'Blargh, {self.id} is dead!')
        self.kill()
