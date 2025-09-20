# SPDX-FileCopyrightText: 2025 Cooper Dalrymple (@relic-se)
#
# SPDX-License-Identifier: GPLv3

# load included modules if we aren't installed on the root path
if len(__file__.split("/")[:-1]) > 1:
    import adafruit_pathlib as pathlib
    if (modules_directory := pathlib.Path("/".join(__file__.split("/")[:-1])) / "lib").exists():
        import sys
        sys.path.append(str(modules_directory.absolute()))

import asyncio
import displayio
import random
import sys
import supervisor
from terminalio import FONT
import vectorio

from adafruit_display_text.label import Label
import adafruit_fruitjam.peripherals
import adafruit_usb_host_mouse
import relic_usb_host_gamepad

# get Fruit Jam OS config if available
try:
    import launcher_config
    config = launcher_config.LauncherConfig()
except ImportError:
    config = None

# program constants
PADDLE_SPEED = 6
BALL_SPEED = 1

# setup display
adafruit_fruitjam.peripherals.request_display_config(320, 240)
display = supervisor.runtime.display

# setup audio, buttons, and neopixels
peripherals = adafruit_fruitjam.peripherals.Peripherals(
    safe_volume_limit=(config.audio_volume_override_danger if config is not None else 12),
)

# user-defined audio output and volume
if config is not None:
    peripherals.audio_output = config.audio_output
    peripherals.volume = config.audio_volume
else:
    peripherals.audio_output = "headphone"
    peripherals.volume = 12

# create root group
root_group = displayio.Group()
display.root_group = root_group

# generate simple foreground palette
foreground_palette = displayio.Palette(1)
foreground_palette[0] = 0xffffff

# center line
root_group.append(vectorio.Rectangle(
    pixel_shader=foreground_palette,
    width=2, height=display.height,
    x=display.width//2-1, y=0,
))

# labels
score_labels = []
for i in range(2):
    # add score
    label = Label(
        font=FONT, text="0", color=foreground_palette[0], scale=2,
        anchor_point=(.5, 0), anchored_position=(display.width*(1+i*2)//4, 4),
    )
    root_group.append(label)
    score_labels.append(label)

# paddles
paddles = []
for i in range(2):
    paddle = vectorio.Rectangle(
        pixel_shader=foreground_palette,
        width=4, height=32,
        x=(display.width-16 if i else 16),
        y=display.height//2-8,
    )
    root_group.append(paddle)
    paddles.append(paddle)

# ball
ball = vectorio.Rectangle(
    pixel_shader=foreground_palette,
    width=8, height=8,
    x=display.width//2-4, y=display.height//2-4,
)
ball.hidden = True  # start out hidden
root_group.append(ball)

# paddle movement method
def paddle_move(direction: int, player: int = 0) -> None:
    direction = 1 if direction > 0 else -1  # restrict direction to 1 or -1
    y = paddles[player].y  # create temporary copy of y position
    y -= direction * PADDLE_SPEED  # apply movement
    y = min(max(y, 0), display.height - paddle.height)  # clamp the position to the playfield
    paddles[player].y = y  # update rectangle position

# mouse control
async def mouse_task() -> None:
    while True:
        if (mouse := adafruit_usb_host_mouse.find_and_init_boot_mouse("bitmaps/cursor.bmp")) is not None:
            mouse.y = display.height // 2

            timeouts = 0
            previous_pressed_btns = []
            while timeouts < 9999:
                pressed_btns = mouse.update()

                # restrict mouse x position to paddle
                mouse.x = paddles[0].x + paddles[0].width // 2

                # limit mouse y position
                if mouse.y < paddles[0].height // 2:
                    mouse.y = paddles[0].height // 2
                elif mouse.y > display.height - paddles[0].height // 2:
                    mouse.y = display.height - paddles[0].height // 2
                
                # assign mouse position to paddle
                paddles[0].y = mouse.y - paddles[0].height // 2

                if pressed_btns is None:
                    timeouts += 1
                else:
                    timeouts = 0
                    if "left" in pressed_btns and (previous_pressed_btns is None or "left" not in previous_pressed_btns):
                        pass
                previous_pressed_btns = pressed_btns
                await asyncio.sleep(1/30)
        await asyncio.sleep(1)

async def keyboard_task() -> None:
    # flush input buffer
    while supervisor.runtime.serial_bytes_available:
        sys.stdin.read(1)

    while True:
        while (c := supervisor.runtime.serial_bytes_available) > 0:
            key = sys.stdin.read(c)
            if key == "\x1b[A" or key == "\x1b[D":  # up or left
                paddle_move(1)
            elif key == "\x1b[B" or key == "\x1b[C":  # down or right
                paddle_move(-1)
            elif key == "\x1b":  # escape
                peripherals.deinit()
                supervisor.reload()
        await asyncio.sleep(1/30)

# initialize left and right player gamepads
gamepads = [relic_usb_host_gamepad.Gamepad(port=i+1) for i in range(2)]

async def gamepad_task() -> None:
    while True:
        for i, gamepad in enumerate(gamepads):
            if gamepad.update():
                if gamepad.buttons.UP or gamepad.buttons.JOYSTICK_UP:  # up
                    paddle_move(1, player=i)
                elif gamepad.buttons.DOWN or gamepad.buttons.JOYSTICK_DOWN:  # down
                    paddle_move(-1, player=i)
                if gamepad.buttons.HOME:  # home
                    peripherals.deinit()
                    supervisor.reload()
        await asyncio.sleep(1/30 if any(gamepad.connected for gamepad in gamepads) else 1)  # sleep longer if there are no gamepads connected

async def buttons_task() -> None:
    while True:
        if peripherals.button3:  # up
            paddle_move(1)
        elif peripherals.button1:  # down
            paddle_move(-1)
        if peripherals.button1 and peripherals.button2 and peripherals.button3:  # all buttons = exit
            peripherals.deinit()
            supervisor.reload()
        await asyncio.sleep(1/30)

def get_random_velocity() -> tuple:  # returns (-1 or 1, -1 or 1)
    return (
        random.randint(0, 1) * 2 - 1,  # either -1 or 1
        random.randint(0, 1) * 2 - 1
    )

def collides(a: vectorio.Rectangle, b: vectorio.Rectangle) -> bool:
    # if one rectangle is to the right of the other
    if a.x > b.x + b.width or b.x > a.x + a.width:
        return False
    # if one rectangle is above the other
    if a.y > b.y + b.height or b.y > a.y + a.height:
        return False
    # rectangles must intersect
    return True

async def gameplay_task() -> None:
    # show the ball
    ball.hidden = False

    velocity_x, velocity_y = get_random_velocity()  # start with random velocity
    while True:

        # apply velocity to ball position
        ball.x += velocity_x * BALL_SPEED
        ball.y += velocity_y * BALL_SPEED

        # only check if we've hit the bottom if y velocity is positive and if we've hit the top if y velocity is negative
        if (velocity_y < 0 and ball.y <= 0) or (velocity_y > 0 and ball.y + ball.height >= display.height):
            velocity_y = -velocity_y  # invert y velocity
        
        # see if we've collided with a paddle
        if (velocity_x < 0 and collides(ball, paddles[0])) or (velocity_x > 0 and collides(ball, paddles[1])):
            velocity_x = -velocity_x  # invert x velocity

        # check if we've gone out of bounds
        if (velocity_x < 0 and ball.x + ball.width < 0) or (velocity_x > 0 and ball.x >= display.width):

            # hide ball
            ball.hidden = True

            # delay before showing ball again and continuing
            await asyncio.sleep(1)

            # reset ball position to center
            ball.x = (display.width - ball.width) // 2
            ball.y = (display.height - ball.height) // 2

            # randomize velocity
            velocity_x, velocity_y = get_random_velocity()

            # show the ball
            ball.hidden = False

        await asyncio.sleep(1/30)

async def main() -> None:
    await asyncio.gather(
        asyncio.create_task(mouse_task()),
        asyncio.create_task(keyboard_task()),
        asyncio.create_task(gamepad_task()),
        asyncio.create_task(buttons_task()),
        asyncio.create_task(gameplay_task()),
    )

try:
    asyncio.run(main())
except KeyboardInterrupt:
    peripherals.deinit()
