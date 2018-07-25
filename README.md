An attempt to create a networked Megaman X platformer combat game using pygame, taking inspiration from Super Smash Brothers and Jazz Jackrabbit 2's multiplayer.

Currently two or more players can be in the same level if on one computer, in a separate terminal window from the game, the network/server.py file is run. Right now the game only looks for a server on 'localhost', meaning all instances of the game must be on the same computer. Only one window can be controlled at a time from the keyboard, but if a joystick/controller is installed, the first joystick will control all windows at the same time.

Note: this project utilizes PodSixNet. In order to use PodSixNet (in Python 3, a requirement for this project), all instances of `PodSixNet.async` must be renamed to `PodSixNet.async_`.
