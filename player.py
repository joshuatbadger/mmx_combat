from datetime import datetime

import json
import math
import pygame
import random


from abc import ABCMeta, abstractmethod
from .weapons import Buster1

from . import constants as CN

class BasePlayerObj(metaclass=ABCMeta):
    '''
    Metaclass for essential methods (and some attributes, though they don't
    inherit as an ABCMeta). At a minimum, expect all attributes listed here
    to be passed back and forth between clients and server.
    '''
    def __init__(self):
        # Initialize all player possible states

        self.on_ground = None
        self.run = None
        self.ducking = None
        self.dashing = None
        self.firing = None
        self.wall_hold = None
        self.taking_damage = None

        # constants
        self.CAN_AIR_DASH = None
        self.BASE_HEALTH = None
        self.LEVEL = None
        self.username = None
        self.MAX_SHOTS = None
        # self.

        # variables
        self.x_velocity = None
        self.y_velocity = None
        self.charge_level = None
        self.direction = None
        self.velocity_hold = None
        self.can_dash = None
        self.can_jump = None
        self.shot_weapons = None

    @abstractmethod
    def _display_stats(self):
        pass

    @abstractmethod
    def update(self):
        pass


class LocalPlayerObj(BasePlayerObj, pygame.sprite.Sprite, object):
    '''
    Base class for local player objects. Inherits pygame Sprite, BasePlayerObj,
    and python object.
    '''
    def __init__(self, username, level, jstick, color, pu_dict=None):
        super(BasePlayerObj, self).__init__()
        # Initialize all player possible states with real values
        self.on_ground = True
        self.run = False
        self.ducking = False
        self.dashing = -1
        self.firing = False
        self.wall_hold = False
        self.taking_damage = -1
        self.dead_wait = 0
        self.invulnerable = 0

        # constants
        self.CAN_AIR_DASH = False
        self.BASE_HEALTH = CN.BASE_HEALTH
        self.LEVEL = level
        self.GRAVITY = CN.GRAVITY
        self.JUMP_SPEED = CN.JUMP_SPEED
        self.RUN_SPEED = CN.RUN_SPEED
        self.DASH_MULT = CN.DASH_MULT
        self.DASH_TIME = CN.DASH_TIME
        self.WALL_JUMP_VELOCITY_HOLD = CN.WALL_JUMP_VELOCITY_HOLD
        self.WALL_DRAG_SPEED = CN.WALL_DRAG_SPEED
        self.MAX_SHOTS = CN.MAX_SHOTS
        self.STAGGER_VELOCITY = CN.STAGGER_VELOCITY
        self.username = username
        self.jstick = jstick
        self.color = color.upper()

        # Modify constants on first instantiation based on powerup dictionary
        if pu_dict:
            self._apply_powerups(pu_dict)

        # variables

        self.x_velocity = 0
        self.y_velocity = 0
        self.charge_level = 0
        self.direction = 'right'
        self.velocity_hold = 0
        self.can_dash = True
        self.can_jump = True
        self.shot_weapons = []
        self.health = self.BASE_HEALTH
        self.wait_camera = False


        # Initialize current key presses and controller dpad positions
        self._cur_keys = pygame.key.get_pressed()
        self._cur_hat = self.jstick.get_hat(0)

        # Build collision rects and apply standing rectangle
        self.standing_image = pygame.Surface([CN.X_STANDING_HITBOX_W,CN.X_STANDING_HITBOX_H])
        self.standing_image.fill(CN.COLOR_DICT[self.color])
        self.standing_rect = self.standing_image.get_rect()

        self.ducking_image = pygame.Surface([CN.X_STANDING_HITBOX_W,CN.X_STANDING_HITBOX_W])
        self.ducking_image.fill(CN.COLOR_DICT[self.color])
        self.ducking_rect = self.ducking_image.get_rect()

        self.dashing_image = pygame.Surface([CN.X_STANDING_HITBOX_H,CN.X_STANDING_HITBOX_W])
        self.dashing_image.fill(CN.COLOR_DICT[self.color])
        self.dashing_rect = self.dashing_image.get_rect()

        self.image = self.standing_image
        self.rect = self.standing_rect
        self.rect.x, self.rect.y = self._get_spawnpoint()

    def _display_stats(self):
        for attrib in dir(self):
            if not attrib.startswith("_"):
                print(attrib)
        # pass

    def _get_spawnpoint(self):
        spawn_points = self.LEVEL.spawn_points
        if not spawn_points:
            raise Exception("Cannot find spawn_points")
        # point_index = datetime.now().time().microsecond % len(spawn_points)
        # return spawn_points[point_index]
        return random.choice(spawn_points)

    def update(self):
        """ Move the player """

        # First make sure we're not dead, if so then wait a few seconds and then respawn
        # TODO: Implement this...
        if self.dead_wait:
            if self.dead_wait == 1:
                self.respawn()
            self.dead_wait -= 1
            return

        # If we're taking damage, reduce the countdown before we can regain control
        if self.taking_damage > 0:
            self.taking_damage -= 1

        if self.invulnerable:
            self.invulnerable -= 1

        # Get current key presses
        self._cur_keys = pygame.key.get_pressed()
        self._cur_hat = self.jstick.get_hat(0)

        # Apply gravity
        self.calc_gravity()

        if self.velocity_hold > 0:
            self.velocity_hold -= 1

        # Check dashing
        # pdb.set_trace()
        if self.dashing > 0 and self.on_ground:
            # on the ground, i have to dash until I run out.
            self.x_velocity = (self.RUN_SPEED * self.DASH_MULT)*((-1)**['right','left'].index(self.direction))
            self.dashing -= 1
            self.change_rect(self.dashing_image,self.dashing_rect)
        elif self.dashing >= 0 and not self.on_ground:
            # not on the ground, movement is optional. check what's pushed.
            # TODO: Determine whether we should be horizontal or vertical on collision rect
            if self.velocity_hold:
                self.x_velocity += 0
            elif self._check_control_left() and not self._check_control_right():
                # only pushing left, go left
                self.x_velocity = -1 * self.RUN_SPEED * self.DASH_MULT
            elif self._check_control_right() and not self._check_control_left():
                # only pushing right, go right
                self.x_velocity = self.RUN_SPEED * self.DASH_MULT
            else:
                # not pushing anything, no change
                self.x_velocity = 0
            if self.dashing > 0:
                # make sure we decrease dashing down to zero so we don't continue dashing
                self.dashing = 0
        elif self.dashing == 0 and self.ducking:
            # we need to be ducking here, we're at the end of the dash. stop and duck.
            self.change_rect(self.ducking_image, self.ducking_rect)
            self.stop()
            if not self._cur_keys[pygame.K_LSHIFT] and not self._cur_keys[pygame.K_RSHIFT] and not self.jstick.get_button(1):
                self.dashing = -1
        elif self.dashing == 0 and (self.on_ground or self.wall_hold):
            if self.x_velocity == 0:
                self.change_rect(self.standing_image, self.standing_rect)
                self.stop()
            if self._check_control_right():
                self.go_right()
            elif self._check_control_left():
                self.go_left()
            if not self._check_control_dash():
                self.dashing = -1
        elif self.dashing == -1 and not self.ducking:
            self.change_rect(self.standing_image, self.standing_rect)


        dx = self.rect.x
        # Horizontal motion
        self.rect.x += self.x_velocity
        # Horizontal Collisions!
        block_hit_list = pygame.sprite.spritecollide(self, self.walls, False)
        self.wall_hold = False
        for block in block_hit_list:
            self.change_rect(self.standing_image, self.standing_rect)
            if self.x_velocity < 0:
                # if self.rect.x > block.rect.x:
                self.rect.left = block.rect.right
            elif self.x_velocity > 0:
                # if self.rect.x < block.rect.x:
                self.rect.right = block.rect.left
            self.wall_hold = True
            self.can_dash = True
            self.x_velocity = 0
            self.dashing = -1
            break
        dx -= self.rect.x

        dy = self.rect.y

        # Vertical motion
        self.rect.y += self.y_velocity
        # Vertical collisions
        block_hit_list = pygame.sprite.spritecollide(self, self.walls, False)
        for block in block_hit_list:
            # We've collided with something vertically
            if self.y_velocity < 0:
                # Ceiling
                self.rect.top = block.rect.bottom
                self.y_velocity = 0
            else:
                # Ground
                self.rect.bottom = block.rect.top
                self.y_velocity = 0
                self.on_ground = True
                self.wall_hold = False
                if self.taking_damage == 0:
                    self.taking_damage = -1
                if not self._check_control_jump():
                    self.can_jump = True
            break

        if self.on_ground and self.taking_damage == 0:
            self.taking_damage = -1

        dy -= self.rect.y

        # if CN.DEBUG and math.hypot(abs(dx),abs(dy)) > math.hypot(CN.RUN_SPEED, CN.JUMP_SPEED):
        #     print("NEW UPDATE!!!!\n-----------------------------------------------------")
        #     for k,v in sorted(self.__dict__.items()):
        #         print(f'{k}: {v}')
        #     print("-----------------------------------------------------\n")

        if not self.invulnerable:
            enemy_hit_list = pygame.sprite.spritecollide(self, self.LEVEL.npc_enemies, False)
            for enemy in enemy_hit_list:
                self.damage(enemy.collide_damage)
                break

        if self.LEVEL.server_addr:
            # Handle network communication
            self.LEVEL.chat_client.send_update_to_server(self._build_player_dict())
            # self.LEVEL.chat_client.send_update_to_server({'un': self.username, 'data': 24})
            self.LEVEL.chat_client.Loop()

    def _build_player_dict(self):
        upload_dict = dict()
        # types = set()
        for k,v in sorted(self.__dict__.items()):
            # Only send strings, booleans, and integers on obvious params. No hidden ones (usually start with "_")
            if not callable(v) and not k.startswith("_") and isinstance(v, (bool, str, int)):
                upload_dict[CN.TRANSFER_DICT.get(k, k)] = v

        upload_dict[CN.TRANSFER_DICT.get('x', 'x')] = self.rect.x
        upload_dict[CN.TRANSFER_DICT.get('width', 'width')] = self.rect.width
        upload_dict[CN.TRANSFER_DICT.get('y', 'y')] = self.rect.y
        upload_dict[CN.TRANSFER_DICT.get('height', 'height')] = self.rect.height

        return upload_dict

    def _apply_powerups(self, pu_dict):
        for k,v in pu_dict.items():
            setattr(self, k, self.__dict__[k] + v)

    def _check_control_left(self):
        return self.jstick.get_hat(0)[0] == -1 or self._cur_keys[pygame.K_LEFT]

    def _check_control_right(self):
        return self.jstick.get_hat(0)[0] == 1 or self._cur_keys[pygame.K_RIGHT]

    def _check_control_down(self):
        return self.jstick.get_hat(0)[1] == -1 or self._cur_keys[pygame.K_DOWN]

    def _check_control_up(self):
        return self.jstick.get_hat(0)[1] == 1 or self._cur_keys[pygame.K_UP]

    def _check_control_jump(self):
        return self._cur_keys[pygame.K_SPACE] or self.jstick.get_button(0)

    def _check_control_dash(self):
        return self._cur_keys[pygame.K_LSHIFT] or self._cur_keys[pygame.K_RSHIFT] or self.jstick.get_button(1)

    def _check_control_fire(self):
        return self._cur_keys[pygame.K_LCTRL] or self._cur_keys[pygame.K_RCTRL] or self.jstick.get_button(2)

    def calc_gravity(self):
        """Are we gravity-ing?"""
        if self.taking_damage > 0:
            # print("currently taking damage, not gravity-ing")
            return
        if not self._check_control_jump() and self.y_velocity < 0:
            # We've released space and are moving upwards. Stop moving upwards.
            self.can_dash = self.CAN_AIR_DASH
            self.y_velocity = 0
        elif self.wall_hold:
            # We're holding onto the wall. Slide down at a constant speed.
            self.y_velocity = self.WALL_DRAG_SPEED
        else:
            # We're in freefall. Calculate acceleration.
            # if self.y_velocity == 0:
            #     self.y_velocity = self.GRAVITY
            if self.y_velocity < self.JUMP_SPEED:
                self.y_velocity += self.GRAVITY
            else:
                self.y_velocity = self.JUMP_SPEED

            self.can_dash = self.CAN_AIR_DASH

    def change_rect(self, new_image, new_rect):
        # Change hitbox size and position appropriately
        old_image = self.image
        old_rect = self.rect
        if self.direction == "right":
            new_rect.x = self.rect.x
        else:
            new_rect.x = self.rect.x + (self.rect.width - new_rect.width)
        new_rect.y = self.rect.y + (self.rect.height - new_rect.height)
        self.image = new_image
        self.rect = new_rect

    def jump(self):
        """Jump action"""
        # Don't do anything if we can't jump
        if not self.can_jump:
            return

        # Check if we're on the ground
        self.rect.y += 2
        platform_hit_list = pygame.sprite.spritecollide(self, self.walls, False)
        self.rect.y -= 2

        if platform_hit_list:
            # we're on the ground
            self.change_rect(self.standing_image, self.standing_rect)
            self.y_velocity = -1 * self.JUMP_SPEED
            self.on_ground = False
            self.can_jump = False
            self.velocity_hold = 0
            self.can_dash = self.CAN_AIR_DASH

        elif self.wall_hold:
            # not on the ground, but we're wall holding
            # Prevent me from jumping again
            self.can_jump = False
            self.wall_hold = False
            # find out which direction to jump.
            # check left walls
            self.rect.x -= 2
            l_wall_list = pygame.sprite.spritecollide(self, self.walls, False)

            # check right walls
            self.rect.x += 4
            r_wall_list = pygame.sprite.spritecollide(self, self.walls, False)

            # reset position
            self.rect.x -= 2

            self.y_velocity = -1 * self.JUMP_SPEED
            self.velocity_hold = self.WALL_JUMP_VELOCITY_HOLD

            # Build x velocity below, but first check for dashability
            dash = bool(self._check_control_dash() and self.can_dash)
            # print(f"dash? {dash}")
            if dash:
                self.dashing = 0

            if l_wall_list:
                # there's a wall to the left, jump right
                self.x_velocity = self.RUN_SPEED * (self.DASH_MULT ** int(dash))
                self.direction = 'right'
            else:
                # wall on right, jump left
                self.x_velocity = (-1*self.RUN_SPEED) * (self.DASH_MULT ** int(dash))
                self.direction = 'left'

    def allow_jump(self):
        self.can_jump = True

    def allow_dash(self):
        self.can_dash = True

    def go_left(self):
        if self.velocity_hold == 0:
            self.direction = 'left'
            if not self._check_control_right() and not self.ducking:
                # if self.dashing > -1:
                self.x_velocity = -1*self.RUN_SPEED
            else:
                self.x_velocity = 0

    def go_right(self):
        if self.velocity_hold == 0:
            self.direction = 'right'
            if not self._check_control_left() and not self.ducking:
                self.x_velocity = self.RUN_SPEED
            else:
                self.x_velocity = 0

    def dash(self):
        if self.dashing == -1 and (self.on_ground or self.CAN_AIR_DASH):
            self.dashing = self.DASH_TIME
            self.velocity_hold = self.DASH_TIME
            # self.can_dash = False
            self.change_rect(self.dashing_image, self.dashing_rect)
        else:
            self.can_dash = False

    def fire(self):
        if len(self.shot_weapons) < self.MAX_SHOTS:
            if self.charge_level < 15:
                new_buster = Buster1(self, 1, [5,5], CN.YELLOW)
            elif self.charge_level < 50:
                new_buster = Buster1(self, 3, [10,5], CN.CYAN)
            elif self.charge_level >= 50:
                new_buster = Buster1(self, 10, [15,10], CN.GREEN)
            self.shot_weapons.append(new_buster)
            self.LEVEL.all_sprite_list.add(new_buster)
            self.discharge()

    def stop(self):
        if not self.velocity_hold:
            self.x_velocity = 0
        if not self.ducking:
            self.change_rect(self.standing_image, self.standing_rect)
        self.wall_hold = False

    def duck(self):
        if self.on_ground and self._check_control_down() and self.x_velocity == 0:
            self.ducking = True
            self.x_velocity = 0
            self.y_velocity = 0
            self.change_rect(self.ducking_image, self.ducking_rect)
        else:
            self.can_dash = False

    def standup(self):
        self.ducking = False
        self.change_rect(self.standing_image, self.standing_rect)

    def damage(self, amount):
        if self.invulnerable > 0:
            return
        self.health -= amount
        self.change_rect(self.standing_image, self.standing_rect)
        if self.health <= 0:
            self.die()
        else:
            self.x_velocity = self.STAGGER_VELOCITY *((-1)**['left','right'].index(self.direction))
            self.y_velocity = (-1) * self.STAGGER_VELOCITY
            self.velocity_hold = 10
            self.on_ground = False
            self.taking_damage = 8
            self.invulnerable = 45

    def die(self):
        self.x_velocity = 0
        self.y_velocity = 0
        self.kill()
        self.dead_wait = 150

    def charge(self):
        self.charge_level += 1

    def discharge(self):
        self.charge_level = 0

    def respawn(self):
        self.image = self.standing_image
        self.rect = self.standing_rect
        self.rect.x, self.rect.y = self._get_spawnpoint()
        self.LEVEL.all_sprite_list.add(self)


class RemotePlayerObj(BasePlayerObj, pygame.sprite.Sprite, object):
    def __init__(self, username, level, color):
        super(BasePlayerObj, self).__init__()
        # Initialize all player possible states with real values
        self.on_ground = True
        self.run = False
        self.ducking = False
        self.dashing = -1
        self.firing = False
        self.wall_hold = False
        self.taking_damage = -1
        self.dead_wait = 0
        self.invulnerable = 0

        # constants
        self.CAN_AIR_DASH = False
        self.BASE_HEALTH = CN.BASE_HEALTH
        self.LEVEL = level
        self.GRAVITY = CN.GRAVITY
        self.JUMP_SPEED = CN.JUMP_SPEED
        self.RUN_SPEED = CN.RUN_SPEED
        self.DASH_MULT = CN.DASH_MULT
        self.DASH_TIME = CN.DASH_TIME
        self.WALL_JUMP_VELOCITY_HOLD = CN.WALL_JUMP_VELOCITY_HOLD
        self.WALL_DRAG_SPEED = CN.WALL_DRAG_SPEED
        self.MAX_SHOTS = CN.MAX_SHOTS
        self.STAGGER_VELOCITY = CN.STAGGER_VELOCITY
        self.username = username
        self.color = color

        # variables

        self.x_velocity = 0
        self.y_velocity = 0
        self.charge_level = 0
        self.direction = 'right'
        self.velocity_hold = 0
        self.can_dash = True
        self.can_jump = True
        self.shot_weapons = []
        self.health = self.BASE_HEALTH
        self.wait_camera = False


        self.image = pygame.Surface([CN.X_STANDING_HITBOX_W,CN.X_STANDING_HITBOX_H])
        self.image.fill(CN.COLOR_DICT[color])
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = (-800,-800)

        print(f"Instantiating new remote player {self.username}!")

    def update(self):
        all_player_dict = self.LEVEL.player_data
        # print(f"Updating {self.username}")
        try:
            my_player_dict = all_player_dict[self.username]
        except KeyError:
            print(f"Oops, {self.username} is gone!")
            self.kill()
            return

        # print(json.dumps(my_player_dict, indent=4, sort_keys=True))
        for attr, v in my_player_dict.items():
            if attr not in ('x', 'y', 'width', 'height'):
                setattr(self, attr, v)
        self.rect.x = my_player_dict['x']
        self.rect.width = my_player_dict['width']
        self.rect.y = my_player_dict['y']
        self.rect.height = my_player_dict['height']
        # TODO: Need to build in acks check, ie, is the data stale?

    def _display_stats(self):
        pass

    def damage(self, amt):
        pass


class DashEcho(pygame.sprite.Sprite):
    def __init__(self, parent_player,x,y):
        self.rem_frames = CN.DASH_ECHOS
        parent_rect = parent_player.image.get_rect()
        self.image = pygame.Surface([parent_rect.width,parent_rect.height])
        self.image.fill((*CN.BLUE,self.rem_frames*70))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self):
        self.rem_frames -= 1
        if self.rem_frames == 0:
            self.parent.shot_weapons.remove(self)
            self.image.kill()
        else:
            self.image.fill((*BLUE,self.rem_frames*70))

class DummyJoystick:
    def __init__(self):
        print("Dummy joystick, dawg.")

    def get_hat(self, hat_id):
        return (0,0)

    def get_button(self, button_id):
        return 0
