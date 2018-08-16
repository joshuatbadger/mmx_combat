import pygame
# Screen stuff
FPS = 30
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
SCREEN_SIZE = SCREEN_WIDTH, SCREEN_HEIGHT
SCREEN_ASPECTRATIO = float(SCREEN_WIDTH)/float(SCREEN_HEIGHT)

SCREEN_HREZ = int(864/1.5)
SCREEN_VREZ = int(486/1.5)
SCREEN_REZ = SCREEN_HREZ, SCREEN_VREZ

# color stuff
BLACK = 0,0,0
WHITE = 255,255,255
RED = 255,0,0
GREEN = 0,255,0
BLUE = 0,0,255
YELLOW = 255,255,0
CYAN = 0,255,255
MAGENTA = 255,0,255

COLOR_DICT = {
              'BLACK': BLACK,
              'WHITE': WHITE,
              'RED': RED,
              'GREEN': GREEN,
              'BLUE': BLUE,
              'YELLOW': YELLOW,
              'CYAN': CYAN,
              'MAGENTA': MAGENTA,
             }


# font stuff
BASICFONTSIZE = 16
pygame.init()
BASICFONT = pygame.font.Font(None, BASICFONTSIZE)

# player stuff
BASE_HEALTH = 16
GRAVITY = 2
JUMP_SPEED = 22
DELAY_JUMP_PERIOD = 4
RUN_SPEED = 10
DASH_MULT = 2
DASH_TIME = 10
WALL_JUMP_VELOCITY_HOLD = 3
WALL_DRAG_SPEED = 6
MAX_SHOTS = 3
STAGGER_VELOCITY = 5

X_STANDING_HITBOX_W = 20
X_STANDING_HITBOX_H = 42

# reduce key length for more efficient transfers to the server. Universal across the board.
TRANSFER_DICT = {
                    "BASE_HEALTH": 'B_H',
                    "CAN_AIR_DASH": 'C_A_D',
                    "DASH_MULT": 'D_M',
                    "DASH_TIME": 'D_T',
                    "GRAVITY": 'G',
                    "JUMP_SPEED": "J_S",
                    "MAX_SHOTS": 'M_S',
                    "RUN_SPEED": 'R_S',
                    "STAGGER_VELOCITY": 'S_V',
                    "WALL_DRAG_SPEED": 'W_D_S',
                    "WALL_JUMP_VELOCITY_HOLD": 'W_J_V',
                    "can_dash": 'c_d',
                    "can_jump": 'c_j',
                    "charge_level": 'c_l',
                    "dead_wait": 'd_w',
                    "direction": "dir",
                    "health": 'hp',
                    "invulnerable": 'inv',
                    "on_ground": 'o_g',
                    "taking_damage": 't_d',
                    "username": "un",
                    "velocity_hold": 'v_h',
                    "wait_camera": 'w_c',
                    "wait_move_for_weapon": 'w_m_f_w',
                    "wall_hold": 'w_h',
                    "x_velocity": 'x_v',
                    "y_velocity": 'y_v',
                }

REC_DICT = {v: k for k,v in TRANSFER_DICT.items()}

DASH_ECHOS = 3


# level stuff
LEVEL_TILE_SIZE = 40


# server and network stuff
DEFAULT_SERVER_IP = "localhost"
DEFAULT_SERVER_PORT = 12000

# logging stuff
LOG_FMT = '%(relativeCreated)6d %(threadName)s %(levelname)s %(filename)s %(funcName)s, Line %(lineno)d\n\t%(message)s\n'
