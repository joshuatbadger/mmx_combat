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

class Buster_1(BaseWeapon, pygame.sprite.Sprite):
    def __init__(self, parent):
        # call parent's constructor
        super(BaseWeapon, self).__init__()

        self.walls = parent.LEVEL.wall_list
        self.parent = parent

        self.image = pygame.Surface([5,5])
        self.image.fill(CN.YELLOW)
        self.rect = self.image.get_rect()
        self.rect.x = parent.rect.x + parent.rect.width/2
        self.rect.y = parent.rect.y + parent.rect.height/2
        self.x_velocity = 25 * (-1)**['right','left'].index(self.parent.direction)
        if self.parent.wall_hold:
            self.x_velocity *= -1
        self.rem_frames = -1

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
            block.damage(1)
            self.destroy()
            return
        # Check for enemy collisions
        enemy_hit_list = pygame.sprite.spritecollide(self, self.parent.LEVEL.npc_enemies, False)
        for enemy in enemy_hit_list:
            enemy.damage(1)
            self.destroy()
            return

    def destroy(self):
        self.parent.shot_weapons.remove(self)
        self.kill()

class Enemy_Buster_1(BaseWeapon, pygame.sprite.Sprite):
    def __init__(self, parent):
        # call parent's constructor
        super(BaseWeapon, self).__init__()

        self.walls = parent.LEVEL.wall_list
        self.parent = parent

        self.image = pygame.Surface([5,5])
        self.image.fill(CN.YELLOW)
        self.rect = self.image.get_rect()
        self.rect.x = parent.rect.x + parent.rect.width/2
        self.rect.y = parent.rect.y + parent.rect.height/2
        self.x_velocity = 25 * (-1)**['right','left'].index(self.parent.direction)
        if self.parent.wall_hold:
            self.x_velocity *= -1
        self.rem_frames = -1

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
            block.damage(1)
            self.destroy()
            return
        # Check for enemy collisions
        enemy_hit_list = pygame.sprite.spritecollide(self, self.parent.LEVEL.npc_enemies, False)
        for enemy in enemy_hit_list:
            enemy.damage(1)
            self.destroy()
            return

    def destroy(self):
        self.parent.shot_weapons.remove(self)
        self.kill()
