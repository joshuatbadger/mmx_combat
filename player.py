import pygame

class BasePlayerObj(object):
    def __init__(self):
        super(BasePlayerObj, self).__init__()
        # Get all player possible states
        self.on_ground = True
        self.jumping = False
        self.can_jump = True
        self.x_pos = 320
        self.y_pos = 180
        self.pos = (self.x_pos, self.y_pos)
        self.x_velocity = 0
        self.y_velocity = 0
        self.run = False
        self.charge_level = 0
        self.direction = 'right'
        self.firing = False
        self.wall_hold = False
        self.taking_damage = False
        self.duck = True
        self.hanging = False
        self.dash = -1
        self.can_air_dash = False

    def _display_stats(self):
        for attrib in dir(self):
            if not attrib.startswith("_"):
                print(attrib)
        # pass

    def _update(self, cur_keys):
        # Check current direction
        if cur_keys[pygame.K_RIGHT]:
            # right overrides other directions.
            self.direction = 'right'
        elif cur_keys[pygame.K_LEFT]:
            # not pushing right, so if we're pushing left go ahead and face left
            self.direction = 'left'
        else:
            self.direction = self.direction

        # Check dashing
        if (cur_keys[pygame.K_LSHIFT] or cur_keys[pygame.K_RSHIFT]) and self.dash == -1:
            self.dash = 10
        elif self.dash > 0:
            self.dash -= 1
        elif self.dash == 0 and not (cur_keys[pygame.K_LSHIFT] or cur_keys[pygame.K_RSHIFT]) and self.on_ground:
            self.dash = -1

        # check for whether we're on the ground and can jump
        if self.on_ground and self.can_jump:
            if cur_keys[pygame.K_SPACE]:
                # we're on the ground, jump!
                self.on_ground = False
                self.y_velocity = -10
                self.can_jump = False
        elif self.on_ground and not cur_keys[pygame.K_SPACE]:
            self.y_velocity = 0
            self.can_jump = True
        elif not self.on_ground:
            if self.y_velocity == 10:
                # we're freefalling, go ahead and land (deal with releasing space for jump timing later)
                self.on_ground = True
                self.y_velocity = 0
            else:
                # can't jump if we're not on the ground. accelerate down!
                # if cur_keys[pygame.K_SPACE]:
                self.y_velocity += 2 if self.y_velocity < 10 else 10


        self.run = True if (cur_keys[pygame.K_LEFT] is not cur_keys[pygame.K_RIGHT]) and self.on_ground else False
        if self.dash > 0 or (self.dash == 0 and self.on_ground == False):
            self.x_velocity = 20*((-1)**['right','left'].index(self.direction))
        elif self.run:
            self.x_velocity = 10*((-1)**['right','left'].index(self.direction))
        elif not self.on_ground:
            self.x_velocity = 10*((-1)**['right','left'].index(self.direction))
        else:
            self.x_velocity = 0



        self.x_pos = self.x_pos + self.x_velocity
        self.y_pos = self.y_pos + self.y_velocity
        self.pos = (self.x_pos, self.y_pos)


        ret_dir = dict()
        for attrib in dir(self):
            if not attrib.startswith("_"):
                ret_dir[attrib] = eval('self.{}'.format(attrib))
        return ret_dir
