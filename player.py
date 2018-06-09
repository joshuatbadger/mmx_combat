from datetime import datetime

import pygame


from abc import ABCMeta, abstractmethod
from .weapons import Buster_1

import MMX_Combat.constants as CN

class BasePlayerObj(metaclass=ABCMeta):
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

    @abstractmethod
    def _redraw(self):
        pass

class LocalPlayerObj(BasePlayerObj, pygame.sprite.Sprite):
    def __init__(self, username, level, jstick, pu_dict=None):
        super(BasePlayerObj, self).__init__()
        # Initialize all player possible states with real values
        self.on_ground = True
        self.run = False
        self.ducking = False
        self.dashing = -1
        self.firing = False
        self.wall_hold = False
        self.taking_damage = False

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
        self.MAX_SHOTS = CN.WALL_DRAG_SPEED
        self.username = username
        self.jstick = jstick

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


        # Initialize current key presses and controller dpad positions
        self._cur_keys = pygame.key.get_pressed()
        self.cur_hat = jstick.get_hat(0) or None

        # Build collision rects and apply standing rectangle
        self.standing_image = pygame.Surface([CN.X_STANDING_HITBOX_W,CN.X_STANDING_HITBOX_H])
        self.standing_image.fill(CN.BLUE)
        self.standing_rect = self.standing_image.get_rect()

        self.ducking_image = pygame.Surface([CN.X_STANDING_HITBOX_W,CN.X_STANDING_HITBOX_W])
        self.ducking_image.fill(CN.BLUE)
        self.ducking_rect = self.ducking_image.get_rect()

        self.dashing_image = pygame.Surface([CN.X_STANDING_HITBOX_H,CN.X_STANDING_HITBOX_W])
        self.dashing_image.fill(CN.BLUE)
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
        point_index = datetime.now().time().microsecond % len(spawn_points)
        return spawn_points[point_index]

    def update(self):
        """ Move the player """
        # Get current key presses
        self._cur_keys = pygame.key.get_pressed()
        if self.jstick:
            self.cur_hat = self.jstick.get_hat(0)
        else:
            self.cur_hat = (0,0)
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
            if not self._cur_keys[pygame.K_LSHIFT] and not self._cur_keys[pygame.K_RSHIFT] and not self.jstick.get_button(1):
                self.dashing = -1
        elif self.dashing == -1 and not self.ducking:
            self.change_rect(self.standing_image, self.standing_rect)

        # Horizontal motion
        self.rect.x += self.x_velocity
        # Horizontal Collisions!
        block_hit_list = pygame.sprite.spritecollide(self, self.walls, False)
        self.wall_hold = False
        for block in block_hit_list:
            self.change_rect(self.standing_image, self.standing_rect)
            if self.x_velocity < 0:
                self.rect.left = block.rect.right
            elif self.x_velocity > 0:
                self.rect.right = block.rect.left
            self.wall_hold = True
            self.can_dash = True
            self.x_velocity = 0
            self.dashing = -1




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
                if not (self._cur_keys[pygame.K_SPACE] or self.jstick.get_button(0)):
                    self.can_jump = True

    def _apply_powerups(self, pu_dict):
        for k,v in pu_dict.items():
            setattr(self, k, self.__dict__[k] + v)

    def _redraw(self):
        print(f"redrawing {self.username}")

    def _check_control_left(self):
        if self.jstick:
            return self.jstick.get_hat(0)[0] == -1 or self._cur_keys[pygame.K_LEFT]
        else:
            return self._cur_keys[pygame.K_LEFT]

    def _check_control_right(self):
        if self.jstick:
            return self.jstick.get_hat(0)[0] == 1 or self._cur_keys[pygame.K_RIGHT]
        else:
            return self._cur_keys[pygame.K_RIGHT]

    def _check_control_down(self):
        if self.jstick:
            return self.jstick.get_hat(0)[1] == -1 or self._cur_keys[pygame.K_DOWN]
        else:
            return self._cur_keys[pygame.K_DOWN]

    def _check_control_up(self):
        if self.jstick:
            return self.jstick.get_hat(0)[1] == 1 or self._cur_keys[pygame.K_UP]
        else:
            return self._cur_keys[pygame.K_UP]

    def calc_gravity(self):
        """Are we gravity-ing?"""
        if not (self._cur_keys[pygame.K_SPACE] or self.jstick.get_button(0)) and self.y_velocity < 0:
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
        new_rect.x = self.rect.x
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
            dash = bool((self._cur_keys[pygame.K_LSHIFT] or self._cur_keys[pygame.K_RSHIFT] or self.jstick.get_button(1)) and self.can_dash)
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
            new_buster = Buster_1(self)
            # print(f"Firing buster id {id(new_buster)}!")
            self.shot_weapons.append(new_buster)
            self.LEVEL.all_sprite_list.add(new_buster)

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
