import pdb
import json
import math
import pygame
import random
import logging
import threading
import traceback

import MMX_Combat.constants as CN

from abc import ABCMeta, abstractmethod

logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')


def build_weapon_id(weapon):

    id = None
    # logging.debug(f"New weapon instantiated. {str(id)}")
    while id == None:
        num = random.randint(0,10000)
        # num = 100
        id = f'{weapon.__class__.__name__}_{weapon.parent.id}_{num}'
        # logging.debug(f"Trying weapon id {str(id)}")
        if id in weapon.parent.LEVEL.data_cache['weapon']:
            id = None
    return id


class BaseWeapon(metaclass=ABCMeta):
    def __init__(self):
        # Initialize all possible variables
        self.parent = None
        self.x_velocity = None
        self.y_velocity = None

    @abstractmethod
    def destroy(self):
        pass

class PlayerBuster1(BaseWeapon, pygame.sprite.Sprite):
    def __init__(self, parent=None, energy=None, size=None, color=None, destroyed_by_enemies=True, destroyed_by_walls=True, rem_frames = 300, on_network = False, id = None, velocity_magnitudes = None, position_override = None, **kwargs):
        # call parent's constructor
        super(BaseWeapon, self).__init__()

        self.parent = parent
        self.walls = self.parent.LEVEL.wall_list
        self.energy = energy
        self.size = size
        self.color = color
        self.destroyed_by_enemies = destroyed_by_enemies
        self.destroyed_by_walls = destroyed_by_walls
        self.id = id or build_weapon_id(self)

        self.is_master_instance = self.parent.LEVEL.server != None

        self.waiting_for_server = 3

        self.build_image_and_rect(position_override)

        # self.x_velocity = 1 * (-1)**['right','left'].index(self.parent.direction)
        if velocity_magnitudes:
            self.x_velocity, self.y_velocity = velocity_magnitudes
        else:
            self.x_velocity = 25 * (-1)**['right','left'].index(self.parent.direction)
            self.y_velocity = 0
            if self.parent.wall_hold:
                self.x_velocity *= -1
        self.rem_frames = -1

        if on_network and not self.is_master_instance:
            self.update = self.update_remote
            self.parent.LEVEL.chat_client.send_weapon_to_server(self._build_weapon_dict())
        elif on_network and self.is_master_instance:
            self.update = self.update_local
            self.rect.x += self.x_velocity
            self.rect.y += self.y_velocity
            # Rebuild image and rect to reflect network lag
            self.build_image_and_rect()
        else:
            self.update = self.update_local

        # logging.debug("BUILD WEAPON")
        self.parent.LEVEL.all_sprite_list.add(self)
        self.parent.LEVEL.weapon_ids.add(self.id)
        self.parent.LEVEL.weapons.add(self)
        self.parent.fire_wait = 7


    def build_image_and_rect(self, position_override=None):
        self.image = pygame.Surface(self.size)
        self.image.fill(self.color)
        self.rect = self.image.get_rect()
        if position_override:
            self.rect.x, self.rect.y = position_override
        else:
            self.rect.x = self.parent.rect.centerx - self.rect.width/2
            self.rect.y = self.parent.rect.centery - self.rect.height/2

    def _build_weapon_dict(self):
        weapon_dict = dict()
        weapon_dict['x'] = self.rect.x
        weapon_dict['y'] = self.rect.y
        weapon_dict['x_velocity'] = self.x_velocity
        weapon_dict['y_velocity'] = self.y_velocity
        weapon_dict['width'] = self.rect.width
        weapon_dict['height'] = self.rect.height
        weapon_dict['energy'] = self.energy
        weapon_dict['color'] = self.color
        weapon_dict['destroyed_by_walls'] = self.destroyed_by_walls
        weapon_dict['destroyed_by_enemies'] = self.destroyed_by_enemies
        weapon_dict['id'] = self.id
        # logging.debug(f"ID: {self.id}")
        weapon_dict['rem_frames'] = self.rem_frames

        return weapon_dict

    def update_local(self):
        if self.rem_frames > 0:
            self.rem_frames -= 1
        if self.rem_frames == 0:
            self.destroy()
            return
        self.rect.x += self.x_velocity

        weap_dict = self._build_weapon_dict()

        if self.parent.LEVEL.server:
            self.parent.LEVEL.data_cache[self.id] = weap_dict
            send_dict = {'action': 'updateserver', 'type': 'weapon', 'id': weap_dict['id'], 'data': weap_dict}
            self.parent.LEVEL.server.UpdateData(send_dict)

        # check for level out-of-bounds
        if self.rect.x > self.parent.LEVEL.width or self.rect.x < 0:
            logging.debug(f"{self.id} out of bounded")
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

    def update_remote(self):

        data = self.parent.LEVEL.data_cache['weapon']
        try:
            self.rect.x = data[self.id]['x']
            self.rect.y = data[self.id]['y']
        except:
            # logging.error(f"Failed to update {self.id} remotely, doing locally")
            self.rect.x += self.x_velocity
            self.rect.y += self.y_velocity
            pass
        logging.debug(f'{self.id}: ({self.rect.x},{self.rect.y})')

    def destroy(self):
        if self in self.parent.shot_weapons:
            self.parent.shot_weapons.remove(self)
        try:
            self.parent.LEVEL.data_cache['weapon'].pop(self.id)
        except KeyError:
            # It's already been pulled from the level's data_cache, move on
            pass
        self.parent.LEVEL.weapon_ids.remove(self.id)
        # logging.debug(json.dumps(self.parent.LEVEL.data_cache, indent=4, sort_keys=True))
        # logging.debug(self.id + ' dying now')
        self.kill()

class PlayerSaber1(BaseWeapon, pygame.sprite.Sprite):
    def __init__(self, parent=None, color=CN.YELLOW, energy=2, id=None, on_network=False, **kwargs):
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
        self.id = id or build_weapon_id(self)
        logging.debug(f"Created saber id {self.id}")
        self.is_master_instance = self.parent.LEVEL.server != None
        self.waiting_for_server = 3

        if on_network and not self.is_master_instance:
            # self.update = self.update_remote
            self.update = self.update_local
            self.parent.LEVEL.chat_client.send_weapon_to_server(self._build_weapon_dict())
        elif on_network and self.is_master_instance:
            self.update = self.update_local
            self.rect.x += self.x_velocity
            self.rect.y += self.y_velocity
            # Rebuild image and rect to reflect network lag
            self.build_image_and_rect()
        else:
            self.update = self.update_local

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

        self.parent.LEVEL.all_sprite_list.add(self)
        self.parent.LEVEL.weapon_ids.add(self.id)
        self.parent.LEVEL.weapons.add(self)
        # self.parent.fire_wait = 7

    def build_image_and_rect(self):
        # logging.debug("Updating Saber")
        current_state = self.hitbox_dict[self.rem_frames]
        # Wall hold needs to swap direction like it does for busters
        cur_dir = self.parent.direction if not self.parent.wall_hold else ['left', 'right'][['right', 'left'].index(self.parent.direction)]
        self.image = pygame.Surface(current_state['size'])
        self.image.fill(self.color or CN.YELLOW)
        self.rect = self.image.get_rect()

        # Align to parent rect
        for attr, ref in current_state['attr'][cur_dir].items():
            setattr(self.rect, attr, getattr(self.parent.rect, ref ))

    def _build_weapon_dict(self):
        weapon_dict = dict()
        # weapon_dict['x'] = self.rect.x
        # weapon_dict['y'] = self.rect.y
        # weapon_dict['x_velocity'] = self.x_velocity
        # weapon_dict['y_velocity'] = self.y_velocity
        # weapon_dict['width'] = self.rect.width
        # weapon_dict['height'] = self.rect.height
        weapon_dict['energy'] = self.energy
        # weapon_dict['color'] = self.color
        # weapon_dict['destroyed_by_walls'] = self.destroyed_by_walls
        # weapon_dict['destroyed_by_enemies'] = self.destroyed_by_enemies
        weapon_dict['id'] = self.id
        # logging.debug(f"ID: {self.id}")
        weapon_dict['rem_frames'] = self.rem_frames

        return weapon_dict

    def update_local(self):
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

    def update_remote(self):
        my_dict = self.parent.LEVEL.data_cache['weapon'].get(self.id, None)
        if not my_dict:
            logging.error(f"Why can't I find myself?! {self.id}")
            # return
        else:
            self.rect.width = my_dict['width']
            self.rect.height = my_dict['height']
            self.rect.x = my_dict

    def destroy(self):
        if self in self.parent.shot_weapons:
            self.parent.shot_weapons.remove(self)
        try:
            self.parent.LEVEL.data_cache['weapon'].pop(self.id)
        except KeyError:
            # It's already been pulled from the level's data_cache, move on
            pass
        self.parent.LEVEL.weapon_ids.remove(self.id)
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
