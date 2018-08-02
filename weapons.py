import math
import pygame

import MMX_Combat.constants as CN

from abc import ABCMeta, abstractmethod


class BaseWeapon(metaclass=ABCMeta):
    def __init__(self):
        # Initialize all possible variables
        self.parent = None
        self.x_velocity = None
        self.y_velocity = None

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def destroy(self):
        pass

class Buster1(BaseWeapon, pygame.sprite.Sprite):
    def __init__(self, parent, energy, size, color):
        # call parent's constructor
        super(BaseWeapon, self).__init__()

        self.walls = parent.LEVEL.wall_list
        self.parent = parent
        self.energy = energy
        self.size = size
        self.color = color

        self.build_image_and_rect()

        self.x_velocity = 25 * (-1)**['right','left'].index(self.parent.direction)
        if self.parent.wall_hold:
            self.x_velocity *= -1
        self.rem_frames = -1

    def build_image_and_rect(self):
        self.image = pygame.Surface(self.size)
        self.image.fill(self.color)
        self.rect = self.image.get_rect()
        self.rect.x = self.parent.rect.centerx - self.rect.width/2
        self.rect.y = self.parent.rect.centery - self.rect.height/2

    def update(self):
        if self.rem_frames > 0:
            self.rem_frames -= 1
        if self.rem_frames == 0:
            self.destroy()
            return
        self.rect.x += self.x_velocity
        # Check for wall collisions
        block_hit_list = pygame.sprite.spritecollide(self, self.walls, False)
        for block in block_hit_list:
            block.damage(self.energy)
            self.destroy()
            return

        # Check for enemy collisions
        enemy_hit_list = pygame.sprite.spritecollide(self, self.parent.LEVEL.npc_enemies, False)
        for enemy in enemy_hit_list:
            enemy.damage(self.energy)
            self.destroy()
            return

        # Check if we're at least half a screen away. if we are, we can begin firing again.
        # Shots shouldn't die until they impact, but we CAN fire again once they're at least that far away
        if (abs(self.rect.x - self.parent.rect.x) > (CN.SCREEN_WIDTH/2) + self.x_velocity) or (abs(self.rect.y - self.parent.rect.y) > (CN.SCREEN_WIDTH/2) + self.x_velocity):
            if self in self.parent.shot_weapons:
                self.parent.shot_weapons.remove(self)
            return


    def destroy(self):
        if self in self.parent.shot_weapons:
            self.parent.shot_weapons.remove(self)
        self.kill()


class EnemyBuster1(BaseWeapon, pygame.sprite.Sprite):
    def __init__(self, parent):
        # call parent's constructor
        super(BaseWeapon, self).__init__()
        # print("Spawning enemy weapon")

        self.walls = parent.level.wall_list
        self.parent = parent

        self.image = pygame.Surface([5,5])
        self.image.fill(CN.MAGENTA)
        self.rect = self.image.get_rect()
        self.rect.x = self.parent.rect.centerx + self.rect.width/2
        self.rect.y = self.parent.rect.centery + self.rect.height/2
        self.rem_frames = 90
        self.speed = 15.0
        self.hypot = math.hypot(self.parent.target.rect.centerx - self.parent.rect.centerx, self.parent.target.rect.centery - self.parent.rect.centery) / self.speed
        if self.hypot == 0:
            self.hypot = 1
        self.x_velocity = (self.parent.target.rect.centerx - self.parent.rect.centerx) / self.hypot
        self.y_velocity = (self.parent.target.rect.centery - self.parent.rect.centery) / self.hypot

    def update(self):
        # print("Updating the enemy weapon")
        if self.rem_frames > 0:
            self.rem_frames -= 1
        if self.rem_frames == 0:
            self.destroy()
            return
        self.image.fill([CN.MAGENTA, CN.GREEN][self.rem_frames % 2])
        self.rect.x += self.x_velocity
        self.rect.y += self.y_velocity
        # Check for wall collisions
        # block_hit_list = pygame.sprite.spritecollide(self, self.walls, False)
        # for block in block_hit_list:
        #     block.damage(1)
        #     self.destroy()
        #     return
        # Check for enemy collisions
        enemy_hit_list = pygame.sprite.spritecollide(self, self.parent.level.players, False)
        for enemy in enemy_hit_list:
            enemy.damage(1)
            self.destroy()
            return

    def destroy(self):
        self.kill()
