import math
import pygame
import logging

import MMX_Combat.constants as CN

from abc import ABCMeta, abstractmethod

logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')

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

class PlayerBuster1(BaseWeapon, pygame.sprite.Sprite):
    def __init__(self, parent, energy, size, color, destroyed_by_enemies=True, destroyed_by_walls=True):
        # call parent's constructor
        super(BaseWeapon, self).__init__()

        self.walls = parent.LEVEL.wall_list
        self.parent = parent
        self.energy = energy
        self.size = size
        self.color = color
        self.destroyed_by_enemies = destroyed_by_enemies
        self.destroyed_by_walls = destroyed_by_walls

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

        # check for level out-of-bounds
        if self.rect.x > self.parent.LEVEL.width or self.rect.x < 0:
            # logging.debug(f"{self.id} out of bounded")
            self.destroy()
            return

        # Check for wall collisions
        block_hit_list = pygame.sprite.spritecollide(self, self.walls, False)
        for block in block_hit_list:
            block.damage(self.energy)
            if self.destroyed_by_walls:
                self.destroy()
                return

        # Check for enemy collisions
        enemy_hit_list = pygame.sprite.spritecollide(self, self.parent.LEVEL.npc_enemies, False)
        for enemy in enemy_hit_list:
            enemy.damage(self.energy)
            if self.destroyed_by_enemies:
                self.destroy()
                return

        # Check if we're at least half a screen away. if we are, we can begin firing again.
        # Shots shouldn't die until they impact, but we CAN fire again once they're at least that far away
        if (abs(self.rect.centerx - self.parent.rect.centerx) > (CN.SCREEN_WIDTH/2) + self.x_velocity) or (abs(self.rect.centery - self.parent.rect.centery) > (CN.SCREEN_WIDTH/2) + self.x_velocity):
            if self in self.parent.shot_weapons:
                self.parent.shot_weapons.remove(self)
            return


    def destroy(self):
        if self in self.parent.shot_weapons:
            self.parent.shot_weapons.remove(self)
        self.kill()

class PlayerSaber1(BaseWeapon, pygame.sprite.Sprite):
    def __init__(self, parent, color=CN.YELLOW, energy=2):
        # call parent's constructor
        super(BaseWeapon, self).__init__()
        # print('')
        self.parent = parent
        self.energy = energy
        self.color = color
        # self.build_image_and_rect()
        self.rem_frames = 10
        self.parent.wait_move_for_weapon = True
        self.parent.fire_wait = self.rem_frames + 1
        # Build hitbox data for what frame we're on. This will eventually be replaced by sprites.
        self.hitbox_dict = {
                                 10: {
                                        'size': [10,10],
                                        'attr': {
                                                    'left': {
                                                                'top': 'top',
                                                                'left': 'right'
                                                            },
                                                    'right': {
                                                                'top': 'top',
                                                                'right': 'left'
                                                            }
                                                 }
                                     },
                                  9: {
                                         'size': [25,10],
                                         'attr': {
                                                     'left': {
                                                                 'bottom': 'top',
                                                                 'right': 'right'
                                                             },
                                                     'right': {
                                                                 'bottom': 'top',
                                                                 'left': 'left'
                                                             }
                                                  }
                                      },
                                  8: {
                                         'size': [40,40],
                                         'attr': {
                                                     'left': {
                                                                 'bottom': 'centery',
                                                                 'right': 'left'
                                                             },
                                                     'right': {
                                                                 'bottom': 'centery',
                                                                 'left': 'right'
                                                             }
                                                  }
                                      },
                                  7: {
                                         'size': [50,50],
                                         'attr': {
                                                     'left': {
                                                                 'bottom': 'bottom',
                                                                 'right': 'left'
                                                             },
                                                     'right': {
                                                                 'bottom': 'bottom',
                                                                 'left': 'right'
                                                             }
                                                  }
                                      },
                                  6: {
                                         'size': [50,50],
                                         'attr': {
                                                     'left': {
                                                                 'bottom': 'bottom',
                                                                 'right': 'left'
                                                             },
                                                     'right': {
                                                                 'bottom': 'bottom',
                                                                 'left': 'right'
                                                             }
                                                  }
                                      },
                                  5: {
                                         'size': [30,30],
                                         'attr': {
                                                     'left': {
                                                                 'bottom': 'bottom',
                                                                 'right': 'left'
                                                             },
                                                     'right': {
                                                                 'bottom': 'bottom',
                                                                 'left': 'right'
                                                             }
                                                  }
                                      },
                                  4: {
                                         'size': [15,15],
                                         'attr': {
                                                     'left': {
                                                                 'bottom': 'bottom',
                                                                 'right': 'left'
                                                             },
                                                     'right': {
                                                                 'bottom': 'bottom',
                                                                 'left': 'right'
                                                             }
                                                  }
                                      },
                                  3: {
                                         'size': [12,12],
                                         'attr': {
                                                     'left': {
                                                                 'bottom': 'bottom',
                                                                 'right': 'left'
                                                             },
                                                     'right': {
                                                                 'bottom': 'bottom',
                                                                 'left': 'right'
                                                             }
                                                  }
                                      },
                                  2: {
                                         'size': [10,10],
                                         'attr': {
                                                     'left': {
                                                                 'bottom': 'bottom',
                                                                 'right': 'left'
                                                             },
                                                     'right': {
                                                                 'bottom': 'bottom',
                                                                 'left': 'right'
                                                             }
                                                  }
                                      },
                                  1: {
                                         'size': [7,7],
                                         'attr': {
                                                     'left': {
                                                                 'bottom': 'bottom',
                                                                 'right': 'left'
                                                             },
                                                     'right': {
                                                                 'bottom': 'bottom',
                                                                 'left': 'right'
                                                             }
                                                  }
                                      },
                                  0: {
                                         'size': [5,5],
                                         'attr': {
                                                     'left': {
                                                                 'bottom': 'bottom',
                                                                 'right': 'left'
                                                             },
                                                     'right': {
                                                                 'bottom': 'bottom',
                                                                 'left': 'right'
                                                             }
                                                  }
                                      }
                                }

    def build_image_and_rect(self):
        # logging.debug("Updating Saber")
        current_state = self.hitbox_dict[self.rem_frames]
        cur_dir = self.parent.direction
        self.image = pygame.Surface(current_state['size'])
        self.image.fill(self.color)
        self.rect = self.image.get_rect()

        # Align to parent rect
        for attr, ref in current_state['attr'][cur_dir].items():
            setattr(self.rect, attr, getattr(self.parent.rect, ref ))

    def update(self):
        # logging.debug(f'Saber remaining frames: {self.rem_frames}')
        if self.rem_frames == -1:
            self.destroy()
            return
        self.build_image_and_rect()
        self.rem_frames -= 1

        # Check for enemy collisions
        enemy_hit_list = pygame.sprite.spritecollide(self, self.parent.LEVEL.npc_enemies, False)
        for enemy in enemy_hit_list:
            enemy.damage(self.energy)

    def destroy(self):
        if self in self.parent.shot_weapons:
            self.parent.shot_weapons.remove(self)
        self.parent.wait_move_for_weapon = False
        self.kill()


class EnemyBuster1(BaseWeapon, pygame.sprite.Sprite):
    def __init__(self, parent):
        # call parent's constructor
        super(BaseWeapon, self).__init__()
        # logging.debug("Spawning enemy weapon")

        self.walls = parent.level.wall_list
        self.parent = parent

        self.image = pygame.Surface([15,15])
        self.image.fill(CN.MAGENTA)
        self.rect = self.image.get_rect()
        self.rect.x = self.parent.rect.centerx - self.rect.width/2
        self.rect.y = self.parent.rect.centery - self.rect.height/2
        self.rem_frames = 90
        self.speed = 15.0
        self.hypot = math.hypot(self.parent.target.rect.centerx - self.parent.rect.centerx, self.parent.target.rect.centery - self.parent.rect.centery) / self.speed
        if self.hypot == 0:
            self.hypot = 1
        self.x_velocity = (self.parent.target.rect.centerx - self.parent.rect.centerx) / self.hypot
        self.y_velocity = (self.parent.target.rect.centery - self.parent.rect.centery) / self.hypot

    def update(self):
        # logging.debug("Updating the enemy weapon")
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
