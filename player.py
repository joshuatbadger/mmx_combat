import pygame

from abc import ABCMeta, abstractmethod

import MMX_Combat.constants as CN

class BasePlayerObj(metaclass=ABCMeta):
    def __init__(self):
        # Get all player possible states
        self.username = None
        self.on_ground = None
        self.jumping = None
        self.can_jump = None
        self.x_velocity = None
        self.y_velocity = None
        self.run = None
        self.charge_level = None
        self.direction = None
        self.firing = None
        self.wall_hold = None
        self.taking_damage = None
        self.ducking = None
        self.hanging = None
        self.dashing = None
        self.can_air_dash = None
        self.level = None

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
    def __init__(self, username, level, x, y):
        super(BasePlayerObj, self).__init__()
        # Get all player possible states
        self.username = username
        self.on_ground = True
        self.jumping = False
        self.can_jump = True
        self.x_velocity = 0
        self.y_velocity = 0
        self.run = False
        self.charge_level = 0
        self.direction = 'right'
        self.firing = False
        self.wall_hold = False
        self.taking_damage = False
        self.ducking = False
        self.hanging = False
        self.dashing = -1
        self.can_air_dash = False

        # Build collision rects and apply standing rectangle
        self.standing_image = pygame.Surface([25,50])
        self.standing_image.fill(CN.WHITE)
        self.standing_rect = self.standing_image.get_rect()

        self.ducking_image = pygame.Surface([25,25])
        self.ducking_image.fill(CN.WHITE)
        self.ducking_rect = self.ducking_image.get_rect()

        self.dashing_image = pygame.Surface([50,25])
        self.dashing_image.fill(CN.WHITE)
        self.dashing_rect = self.dashing_image.get_rect()

        self.image = self.standing_image
        self.rect = self.standing_rect
        self.rect.x = x
        self.rect.y = y

    def _display_stats(self):
        for attrib in dir(self):
            if not attrib.startswith("_"):
                print(attrib)
        # pass

    def update(self):
        """ Move the player """
        # Apply gravity
        self.calc_gravity()

        # Check dashing
        if self.dashing > 0 or (self.dashing == 0 and not self.on_ground):
            self.x_velocity = 20*((-1)**['right','left'].index(self.direction))
            # new_dash = DashEcho(self, self.rect.x, self.rect.y)
            if self.dashing > 0:
                self.dashing -= 1
        elif self.dashing == 0 and self.ducking:
            self.dashing = -1
            self.change_rect(self.ducking_image, self.ducking_rect)
            self.stop()
        elif self.dashing == 0 and self.on_ground:
            self.dashing = -1
            self.change_rect(self.standing_image, self.standing_rect)
            self.stop()
            if pygame.key.get_pressed()[pygame.K_RIGHT]:
                self.go_right()
            elif pygame.key.get_pressed()[pygame.K_LEFT]:
                self.go_left()
            # else:
            #     self.stop()

        # Horizontal motion
        self.rect.x += self.x_velocity
        # Horizontal Collisions!
        block_hit_list = pygame.sprite.spritecollide(self, self.walls, False)
        for block in block_hit_list:
            if self.x_velocity < 0:
                self.rect.left = block.rect.right
            else:
                self.rect.right = block.rect.left

        # Wall hanging?
        # if len(block_hit_list) > 0:



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
                self.rect.bottom = block.rect.top
                self.y_velocity = 0
                self.on_ground = True

        ret_dir = dict()
        for attrib in dir(self):
            if not attrib.startswith("_"):
                ret_dir[attrib] = eval('self.{}'.format(attrib))
        return ret_dir


    def _redraw(self):
        print(f"redrawing {self.username}")

    def calc_gravity(self):
        """Are we gravity-ing?"""
        if not pygame.key.get_pressed()[pygame.K_SPACE] and self.y_velocity < 0:
            self.y_velocity = 0
        else:
            if self.y_velocity == 0:
                self.y_velocity = CN.GRAVITY
            elif self.y_velocity != CN.JUMP_SPEED:
                self.y_velocity += CN.GRAVITY

    def change_rect(self, new_image, new_rect):
        old_image = self.image
        old_rect = self.rect
        new_rect.x = self.rect.x
        new_rect.y = self.rect.y + (self.rect.height - new_rect.height)
        self.image = new_image
        self.rect = new_rect

    def jump(self):
        """Jump action"""
        self.rect.y += 2
        platform_hit_list = pygame.sprite.spritecollide(self, self.walls, False)
        self.rect.y -= 2

        if platform_hit_list:
            self.change_rect(self.standing_image, self.standing_rect)
            self.y_velocity = -1 * CN.JUMP_SPEED
            self.on_ground = False

    def go_left(self):
        self.direction = 'left'
        if not pygame.key.get_pressed()[pygame.K_RIGHT] and not self.ducking:
            self.x_velocity = -10
        else:
            self.x_velocity = 0

    def go_right(self):
        self.direction = 'right'
        if not pygame.key.get_pressed()[pygame.K_LEFT] and not self.ducking:
            self.x_velocity = 10
        else:
            self.x_velocity = 0

    def dash(self):
        if self.dashing == -1 and (self.on_ground or self.can_air_dash):
            self.dashing = 10
            self.change_rect(self.dashing_image, self.dashing_rect)

    def stop(self):
        self.x_velocity = 0

    def duck(self):
        if self.on_ground and pygame.key.get_pressed()[pygame.K_DOWN]:
            self.ducking = True
            self.x_velocity = 0
            self.y_velocity = 0
            self.change_rect(self.ducking_image, self.ducking_rect)

    def standup(self):
        self.ducking = False
        self.change_rect(self.standing_image, self.standing_rect)

class DashEcho(pygame.sprite.Sprite):
    def __init__(self, parent_player,x,y):
        self.rem_frames = CN.DASH_ECHOS
        self.image = parent_player.image
        self.image.fill((*CN.BLUE,self.rem_frames*70))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.rem_frames = CN.DASH_ECHOS

    def update(self):
        self.rem_frames -= 1
        if self.rem_frames == 0:
            self.image.kill()
        else:
            self.image.fill((*BLUE,self.rem_frames*70))
