import os
import sys
import pygame

# from MMX_Combat.player import BasePlayerObj


# Initialize Globals
# Screen stuff
FPS = 15
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_SIZE = SCREEN_WIDTH, SCREEN_HEIGHT

# color stuff
BLACK = 0,0,0
WHITE = 255,255,255

# font stuff
BASICFONTSIZE = 20


def test():
    os.system("cls")
    print("Beginning the pygame test\n\n")
    print("pygame version: {}".format(pygame.__version__))

    # for item in sorted(dir(pygame)):
    #     print(item)


    start_game()

def make_text(text, color, bgcolor, top, left):
    textSurf = BASICFONT.render(text, True, color, bgcolor)
    textRect = textSurf.get_rect()
    textRect.topleft = (top, left)
    return (textSurf, textRect)

def start_game():
    global FPS, SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_SIZE, BLACK, WHITE, SCREEN, BASICFONT, BASICFONTSIZE

    from MMX_Combat.player import BasePlayerObj

    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    SCREEN = pygame.display.set_mode(SCREEN_SIZE)
    pygame.display.set_caption("Testing input")

    BASICFONT = pygame.font.Font(None, BASICFONTSIZE)

    player = BasePlayerObj()
    # print("\n\nPlayer attribs:\n")
    # player._display_stats()

    # main game loop
    while True:
        # os.system("cls")
        pressed_keys = []
        pressed_keys_str = ''
        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()
            # print(event)
        # if pygame.key.get_pressed()[pygame.K_LEFT]:
        #     pressed_keys.append("LEFT")
        # if pygame.key.get_pressed()[pygame.K_RIGHT]:
        #     pressed_keys.append("RIGHT")
        # if pygame.key.get_pressed()[pygame.K_UP]:
        #     pressed_keys.append("UP")
        # if pygame.key.get_pressed()[pygame.K_DOWN]:
        #     pressed_keys.append("DOWN")

        # pressed_keys_str = ', '.join(sorted(pressed_keys))
        # print(pygame.key.get_pressed())
        # print(pressed_keys_str)
        # text_surf, text_rect = make_text(pressed_keys_str, WHITE, BLACK, 120, 350)

        SCREEN.fill(BLACK)
        state = player._update(pygame.key.get_pressed())
        i = 0
        for k,v in state.items():
            text_surf, text_rect = make_text("{}: {}".format(k,str(v)), WHITE, BLACK, 10, 10+(i*1.1*BASICFONTSIZE))
            SCREEN.blit(text_surf, text_rect)
            i += 1


        # SCREEN.fill(BLACK)
        # SCREEN.blit(text_surf, text_rect)
        pygame.display.flip()
        FPSCLOCK.tick(FPS)


if __name__ == "__main__":
    mmx_main_path = os.path.normpath(os.path.join(os.path.realpath(__file__), "..", ".."))
    if mmx_main_path not in sys.path:
        sys.path.append(mmx_main_path)
    test()
