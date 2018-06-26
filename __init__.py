import os
import sys
import pygame
import datetime

from MMX_Combat.network.client import get_remote_player_data

def test():
    os.system("cls")
    print("Beginning the pygame test\n\n")
    print(f"pygame version: {pygame.__version__}")
    global USERNAME

    if CN.DEBUG:
        USERNAME = "Eclipse_JTB"
    else:
        USERNAME = input("Username: ")

    # USERNAME = "Eclipse_JTB"
    # for item in sorted(dir(pygame)):
    #     print(item)

    prompt = ''

    while prompt not in CN.COLOR_DICT:
        prompt = input("color: ").upper()


    start_game(player_color=prompt)

def make_text(text, color, bgcolor, top, left):
    textSurf = CN.BASICFONT.render(text, True, color, bgcolor)
    textRect = textSurf.get_rect()
    textRect.topleft = (top, left)
    return (textSurf, textRect)

def get_all_remote_players(level):
    global all_player_dict
    all_player_dict = get_remote_player_data(dict(), level.server_addr)
    return [k for k,v in all_player_dict.items()]

def get_proper_screen_size(w,h):
    # print(f'Resize Attempt width: {w}')
    # print(f'Resize Attempt height: {h}')
    while float(w)/float(h) != CN.SCREEN_ASPECTRATIO:
        if float(w)/float(h) > CN.SCREEN_ASPECTRATIO:
            # too wide, base off of height
            w = int(16*(float(h)/9))
        else:
            # too narrow, base off of width
            h = int(9*(float(w)/16))
    return w,h

def start_game(player_color='BLUE'):


    from MMX_Combat.player import BasePlayerObj, LocalPlayerObj
    from MMX_Combat.environment import BaseEnvironmentObj, TestLevel
    from MMX_Combat.camera import Camera, complex_camera

    global all_player_dict
    all_player_dict = dict()

    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    SCREEN = pygame.display.set_mode(CN.SCREEN_SIZE, pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
    CAMERA_SCREEN = pygame.Surface(CN.SCREEN_REZ)
    pygame.display.set_caption("Testing input")

    BASICFONT = pygame.font.Font(None, CN.BASICFONTSIZE)

    if not pygame.joystick.get_init():
        pygame.joystick.init()

    attached_joysticks = pygame.joystick.get_count()
    if attached_joysticks:
        # print(f"Attached joysticks: {attached_joysticks}")
        # print("Getting first joystick")
        jstick = pygame.joystick.Joystick(0)
        jstick.init()

    level = TestLevel(CN.DEFAULT_SERVER_IP, CN.DEFAULT_SERVER_PORT)

    all_players = []

    local_player = LocalPlayerObj(USERNAME, level, jstick or None, player_color)
    # local_player = LocalPlayerObj(USERNAME, level, jstick or None, player_color, {"MAX_SHOTS":2})
    all_players.append(local_player)

    # for remote_player in get_all_remote_players(level):
    #     all_players.append(remote_player)

    for player in all_players:
        player.walls = level.wall_list
        level.all_sprite_list.add(player)
        level.players.add(player)

    longest_proc_frame = 0

    player_camera = Camera(complex_camera, level.width, level.height)

    in_focus = True

    # main game loop
    while True:
        # os.system("cls")
        pressed_keys = []
        pressed_keys_str = ''
        cur_keys = pygame.key.get_pressed()
        cur_hat = jstick.get_hat(0)
        if cur_keys[pygame.K_LEFT] or cur_keys[pygame.K_RIGHT] or cur_hat[0] != 0:
            if cur_keys[pygame.K_LEFT] or cur_hat[0] == -1:
                local_player.go_left()
            if cur_keys[pygame.K_RIGHT] or cur_hat[0] == 1:
                local_player.go_right()
        else:
            local_player.stop()


        if cur_keys[pygame.K_DOWN] or cur_hat[1] == -1:
            local_player.duck()
        if cur_keys[pygame.K_SPACE] or jstick.get_button(0):
            local_player.jump()
        if cur_keys[pygame.K_LCTRL] or cur_keys[pygame.K_RCTRL] or jstick.get_button(2):
            local_player.charge()
        if cur_keys[pygame.K_LSHIFT] or cur_keys[pygame.K_RSHIFT] or jstick.get_button(1):
            local_player.dash()
        if cur_keys[pygame.K_KP_MINUS] and CN.FPS > 1:
            CN.FPS -= 1
        if cur_keys[pygame.K_KP_PLUS] and CN.FPS < 30:
            CN.FPS += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print(f"  Longest frame process: {longest_proc_frame} seconds")
                frame_update = 1.0/CN.FPS
                print(f"Single frame update max: {frame_update} seconds")
                print("")
                print("            Code status: {}".format("All good\n" if frame_update > longest_proc_frame else "Too heavy\n"))
                sys.exit()

            # elif event.type == pygame.ACTIVEEVENT:
            #     # print(event)
            #     # print(event.state)
            #     print('state:', event.state, '| gain:', event.gain,)
            #     if event.state == 1:
            #         if event.gain == 0:
            #             print("| mouse out",)
            #         elif event.gain == 1:
            #             print("| mouse in",)
            #     elif event.state == 2:
            #         if event.gain == 0:
            #             print("| titlebar pressed",)
            #         elif event.gain == 1:
            #             print("| titlebar unpressed",)
            #     elif event.state == 6:
            #         if event.gain == 0:
            #             print("| window minimized",)
            #     elif event.state == 4:
            #         if event.gain == 1:
            #             print("| window normal",)

            elif event.type == pygame.VIDEORESIZE:
                # print(f"Resizing to {event.dict['size']}!")
                SCREEN = pygame.display.set_mode(get_proper_screen_size(*event.dict['size']), pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)

            # Check for keys being released.
            elif event.type == pygame.KEYUP:
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
                if event.key == pygame.K_SPACE:
                    local_player.allow_jump()
                if (event.key == pygame.K_LSHIFT and not cur_keys[pygame.K_RSHIFT]) or (event.key == pygame.K_RSHIFT and not cur_keys[pygame.K_LSHIFT]):
                    local_player.allow_dash()
                if event.key == pygame.K_LCTRL and not cur_keys[pygame.K_RCTRL]:
                    if local_player.charge_level > 2:
                        local_player.fire()

            # Check for keys being pressed.
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LCTRL, pygame.K_RCTRL):
                    local_player.fire()

            elif event.type == pygame.JOYBUTTONDOWN:
                # print(f"Joystick button {event.button} pressed.")
                if event.button == 2:
                    local_player.fire()
            elif event.type == pygame.JOYBUTTONUP:
                # print(f"Joystick button {event.button} released.")
                if event.button == 0:
                    local_player.allow_jump()
                if event.button == 1:
                    local_player.allow_dash()
                if event.button == 2:
                    if local_player.charge_level > 5:
                        local_player.fire()
                    local_player.discharge()


            # Now we check for whether the hat is being pressed/released
            elif event.type == pygame.JOYHATMOTION:
                if event.value[0] == 0:
                    local_player.stop()
                if event.value[1] == 0:
                    local_player.standup()

        CAMERA_SCREEN.fill(CN.BLACK)

        # Update info on all players
        proc_start_time = datetime.datetime.now()

        # all_player_dict = get_remote_player_data(all_player_dict, level.server_addr)

        level.all_sprite_list.update()
        if local_player not in level.all_sprite_list:
            local_player.update()
        player_camera.update(local_player)
        proc_end_time = (datetime.datetime.now() - proc_start_time).total_seconds()
        if proc_end_time > longest_proc_frame:
            longest_proc_frame = proc_end_time

        # Apply camera
        for s in level.all_sprite_list:
            CAMERA_SCREEN.blit(s.image, player_camera.apply(s))

        SCREEN.blit(pygame.transform.scale(CAMERA_SCREEN, [*SCREEN.get_size()], SCREEN), [0,0])

        # Display debug and/or controls
        if CN.DEBUG:
            text_surf, text_rect = make_text("{}: {}".format('username',str(local_player.__dict__['username'])), CN.WHITE, CN.BLACK, 50, 10)
            SCREEN.blit(text_surf, text_rect)
            i = 1
            text_surf, text_rect = make_text("{}: {}".format('FPS',str(CN.FPS)), CN.WHITE, CN.BLACK, 50, 10+(i*1.1*CN.BASICFONTSIZE))
            SCREEN.blit(text_surf, text_rect)
            i+=1
            for k,v in sorted(local_player.__dict__.items()):
                # print(k)
                # print("\t" + str(type(v)))
                if k != 'username' and not callable(v) and not k.startswith("_"):
                    text_surf, text_rect = make_text("{}: {} ({})".format(k,str(v), type(v)), CN.WHITE, CN.BLACK, 50, 10+(i*1.1*CN.BASICFONTSIZE))
                    SCREEN.blit(text_surf, text_rect)
                    i += 1
        else:
            text = """Controls:
                    Movement: Arrow Keys or Controller D-Pad
                    Jump: Spacebar or bottom Controller button (X)
                    Dash: Shift or right Controller button (O)"""
            for i, line in enumerate(text.split("\n")):
                text_surf, text_rect = make_text(line.replace("    ", ""), CN.WHITE, CN.BLACK, 50, 10+(i*1.1*CN.BASICFONTSIZE))
                SCREEN.blit(text_surf, text_rect)


        pygame.display.flip()
        FPSCLOCK.tick(CN.FPS)


if __name__ == "__main__":
    mmx_main_path = os.path.normpath(os.path.join(os.path.realpath(__file__), "..", ".."))
    if mmx_main_path not in sys.path:
        sys.path.append(mmx_main_path)
    import MMX_Combat.constants as CN
    test()
