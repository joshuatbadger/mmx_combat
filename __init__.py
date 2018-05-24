import os
import sys
import pygame

def test():
    os.system("cls")
    print("Beginning the pygame test\n\n")
    print(f"pygame version: {pygame.__version__}")
    global USERNAME

    # if DEBUG:
    #     USERNAME = "Eclipse_JTB"
    # else:
    #     USERNAME = input("Username: ")

    USERNAME = "Eclipse_JTB"
    # for item in sorted(dir(pygame)):
    #     print(item)


    start_game()

def make_text(text, color, bgcolor, top, left):
    textSurf = CN.BASICFONT.render(text, True, color, bgcolor)
    textRect = textSurf.get_rect()
    textRect.topleft = (top, left)
    return (textSurf, textRect)

def get_all_remote_players():
    # TODO: Get information from remote people about their locations/states
    return []

def start_game():


    from MMX_Combat.player import BasePlayerObj, LocalPlayerObj
    from MMX_Combat.environment import BaseEnvironmentObj, TestLevel

    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    SCREEN = pygame.display.set_mode(CN.SCREEN_SIZE)
    pygame.display.set_caption("Testing input")

    BASICFONT = pygame.font.Font(None, CN.BASICFONTSIZE)

    level = TestLevel()

    all_players = []

    local_player = LocalPlayerObj(USERNAME, level, 250, CN.SCREEN_HEIGHT-150)
    all_players.append(local_player)

    for remote_player in get_all_remote_players():
        all_players.append(remote_player)

    for player in all_players:
        player.walls = level.wall_list
        level.all_sprite_list.add(player)



    # main game loop
    while True:
        # os.system("cls")
        pressed_keys = []
        pressed_keys_str = ''
        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()
            # print(event)
            if event.type == pygame.KEYDOWN:
                print(event.key)
                if event.key == pygame.K_SPACE:
                    local_player.jump()
                if event.key == pygame.K_LEFT:
                    local_player.go_left()
                if event.key == pygame.K_RIGHT:
                    local_player.go_right()
                if event.key == pygame.K_DOWN:
                    local_player.duck()
                if event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                    local_player.dash()
                if event.key == 269 and CN.FPS > 1:
                    CN.FPS -= 1
                if event.key == 270 and CN.FPS < 30:
                    CN.FPS += 1

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT and local_player.x_velocity < 0 and local_player.dashing < 0:
                    if not pygame.key.get_pressed()[pygame.K_RIGHT]:
                        local_player.stop()
                    else:
                        local_player.go_right()
                if event.key == pygame.K_RIGHT and local_player.x_velocity > 0 and local_player.dashing < 0:
                    if not pygame.key.get_pressed()[pygame.K_LEFT]:
                        local_player.stop()
                    else:
                        local_player.go_left()
                if event.key == pygame.K_DOWN:
                    local_player.standup()

            # if (not pygame.key.get_pressed().get(pygame.K_LEFT, None) and not pygame.key.get_pressed().get(pygame.K_LEFT, None)) and local_player.dashing < 0:
            # cur_pressed = set(pygame.key.get_pressed())
            # if not set([pygame.K_LEFT, pygame.K_RIGHT]) & cur_pressed:
            #     local_player.stop()

        SCREEN.fill(CN.BLACK)

        # Update info on all players
        for i, player in enumerate(all_players):
            # Get remote players through different arguments
            if i > 0:
                pass
            # Get local player's update
            # TODO: allow remapping?
            else:
                local_state = player.update()

        if CN.DEBUG:
            text_surf, text_rect = make_text("{}: {}".format('username',str(local_state['username'])), CN.WHITE, CN.BLACK, 30, 10)
            SCREEN.blit(text_surf, text_rect)
            i = 1
            text_surf, text_rect = make_text("{}: {}".format('FPS',str(CN.FPS)), CN.WHITE, CN.BLACK, 30, 10+(i*1.1*CN.BASICFONTSIZE))
            SCREEN.blit(text_surf, text_rect)
            i+=1
            for k,v in local_state.items():
                if k != 'username':
                    text_surf, text_rect = make_text("{}: {}".format(k,str(v)), CN.WHITE, CN.BLACK, 30, 10+(i*1.1*CN.BASICFONTSIZE))
                    SCREEN.blit(text_surf, text_rect)
                    i += 1

        level.all_sprite_list.draw(SCREEN)
        pygame.display.flip()
        FPSCLOCK.tick(CN.FPS)


if __name__ == "__main__":
    mmx_main_path = os.path.normpath(os.path.join(os.path.realpath(__file__), "..", ".."))
    if mmx_main_path not in sys.path:
        sys.path.append(mmx_main_path)
    import MMX_Combat.constants as CN
    test()
