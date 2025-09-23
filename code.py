# SPDX-FileCopyrightText: 2025 Cooper Dalrymple (@relic-se)
#
# SPDX-License-Identifier: GPLv3

# load included modules if we aren't installed on the root path
if len(__file__.split("/")[:-1]) > 1:
    import adafruit_pathlib as pathlib
    if (modules_directory := pathlib.Path("/".join(__file__.split("/")[:-1])) / "lib").exists():
        import sys
        sys.path.append(str(modules_directory.absolute()))

import audiomixer
import array
import asyncio
import displayio
import random
import synthio
import sys
import supervisor
from terminalio import FONT
import vectorio

from adafruit_display_text.label import Label
import adafruit_fruitjam.peripherals
import adafruit_usb_host_mouse
import relic_usb_host_gamepad
import relic_waveform

# get Fruit Jam OS config if available
try:
    import launcher_config
    config = launcher_config.LauncherConfig()
except ImportError:
    config = None

# program constants
PADDLE_SPEED = 6
INITIAL_BALL_SPEED = 1
BALL_SPEED_MODIFIER = 1.25
WIN_SCORE = 11
WIN_DIFF = 2
COMPUTER_MIN_TIME = .1
COMPUTER_MAX_TIME = .4

# setup display
adafruit_fruitjam.peripherals.request_display_config(320, 240)
display = supervisor.runtime.display

# setup audio, buttons, and neopixels
SAMPLE_RATE = 32000
peripherals = adafruit_fruitjam.peripherals.Peripherals(
    safe_volume_limit=(config.audio_volume_override_danger if config is not None else 12),
    sample_rate=SAMPLE_RATE,
)

# user-defined audio output and volume
if config is not None:
    peripherals.audio_output = config.audio_output
    peripherals.volume = config.audio_volume
else:
    peripherals.audio_output = "headphone"
    peripherals.volume = 12

# create sound effects
if peripherals.audio:
    # set up synthesizer
    synth = synthio.Synthesizer(
        sample_rate=SAMPLE_RATE,
        channel_count=1,
    )

    # set up mixer
    mixer = audiomixer.Mixer(
        voice_count=1,
        sample_rate=SAMPLE_RATE,
        channel_count=1,
    )

    # play synthesizer through mixer and audio output
    peripherals.audio.play(mixer)
    mixer.play(synth)

    # original pong game can only generate square waves at a one frequency and +1 octave up
    FREQUENCY = 245
    WAVEFORM = relic_waveform.mix(  # mixes waveforms together
        (relic_waveform.square(size=64), .8),  # primary sound is a square wave
        (relic_waveform.noise(size=64), .2),  # add a little bit of noise into the mix for more authenticity
    )  # using size to "tune" noise
    LFO_WAVEFORM = array.array('h', [32767, 32767, 0, 0])
    def generate_note(duration: float, octave: int = 0, amplitude: float = 1) -> synthio.Note:
        return synthio.Note(
            frequency=FREQUENCY * pow(2, octave),
            waveform=WAVEFORM,
            envelope=synthio.Envelope(
                attack_time=0.01, attack_level=1, decay_time=0,
                sustain_level=1, release_time=0,
            ),
            amplitude=synthio.LFO(
                waveform=LFO_WAVEFORM,
                scale=amplitude,  # should be full amplitude for first half and and 0 for second
                rate=1/(duration*2),  # .04s is our duration, doubled for second half of square wave
                interpolate=False, once=True,
            ),
        )
    
    # all of these values are based on the original pong arcade audio
    SFX_WALL = generate_note(.016)
    SFX_PADDLE = generate_note(.032, 1)
    SFX_SCORE = generate_note(.51)

else:
    SFX_WALL = SFX_SCORE = SFX_PADDLE = None

def play_sfx(note: synthio.Note) -> None:
    if peripherals.audio:
        note.amplitude.retrigger()  # make sure we reset our amplitude lfo
        synth.release_all_then_press(note)  # we only want to play one sound at a time

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
win_labels = []
for i in range(2):
    x = display.width*(1+i*2)//4

    # add score
    label = Label(
        font=FONT, text="0", color=foreground_palette[0], scale=2,
        anchor_point=(.5, 0), anchored_position=(x, 4),
    )
    root_group.append(label)
    score_labels.append(label)

    # add win text
    label = Label(
        font=FONT, text="WIN", color=foreground_palette[0], scale=4,
        anchor_point=(.5, .5), anchored_position=(x, display.height//2),
    )
    label.hidden = True  # hide until the player wins
    root_group.append(label)
    win_labels.append(label)

# paddles
paddles = []
for i in range(2):
    paddle = vectorio.Rectangle(
        pixel_shader=foreground_palette,
        width=4, height=32,
        x=(display.width-20 if i else 16),
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
if peripherals.neopixels:  # clear ball position on neopixels
    peripherals.neopixels.fill(0)
    peripherals.neopixels.show()
root_group.append(ball)

# paddle movement method
def paddle_move(direction: int, player: int = 0) -> None:
    direction = 1 if direction > 0 else -1  # restrict direction to 1 or -1
    y = paddles[player].y  # create temporary copy of y position
    y -= direction * PADDLE_SPEED  # apply movement
    y = min(max(y, 0), display.height - paddle.height)  # clamp the position to the playfield
    paddles[player].y = y  # update rectangle position

# global variable to indicate that we are waiting for user input
waiting = False
async def wait_input() -> None:
    global waiting
    waiting = True
    while waiting:
        await asyncio.sleep(.5)

# mouse control
async def mouse_task() -> None:
    global waiting
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
                        waiting = False
                previous_pressed_btns = pressed_btns
                await asyncio.sleep(1/30)
        await asyncio.sleep(1)

async def keyboard_task() -> None:
    global waiting

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
            elif key == "\n" or key == " ":  # enter or space
                waiting = False
            elif key == "\x1b":  # escape
                peripherals.deinit()
                supervisor.reload()
        await asyncio.sleep(1/30)

# initialize left and right player gamepads
gamepads = [relic_usb_host_gamepad.Gamepad(port=i+1) for i in range(2)]

async def gamepad_task() -> None:
    global waiting
    while True:
        for i, gamepad in enumerate(gamepads):
            if gamepad.update():
                if gamepad.buttons.UP or gamepad.buttons.JOYSTICK_UP:  # up
                    paddle_move(1, player=i)
                elif gamepad.buttons.DOWN or gamepad.buttons.JOYSTICK_DOWN:  # down
                    paddle_move(-1, player=i)
                if gamepad.buttons.A or gamepad.buttons.START:  # A or X on DS4
                    waiting = False
                if gamepad.buttons.HOME:  # home
                    peripherals.deinit()
                    supervisor.reload()
        await asyncio.sleep(1/30 if any(gamepad.connected for gamepad in gamepads) else 1)  # sleep longer if there are no gamepads connected

async def buttons_task() -> None:
    global waiting
    while True:
        if peripherals.button3:  # up
            paddle_move(1)
        elif peripherals.button1:  # down
            paddle_move(-1)
        if waiting and peripherals.button2:  # continue
            waiting = False
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

def apply_brightness(value:int, brightness:float) -> int:
    for i in range(3):
        c = (value >> (8 * i)) & 0xff  # extract color component (rgb)
        c = int(c * brightness)  # apply brightness
        c = min(max(c, 0x00), 0xff)  # clamp value to acceptable range
        value &= 0xffffff ^ (0xff << (8 * i))  # remove old component value
        value |= c << (8 * i)  # insert new component value
    return value

computer_move = 0
async def gameplay_task() -> None:
    global waiting, computer_move

    # wait for initial input
    await wait_input()

    # show the ball
    ball.hidden = False

    ball_x, ball_y = ball.x, ball.y
    velocity_x, velocity_y = get_random_velocity()  # start with random velocity
    ball_speed = INITIAL_BALL_SPEED
    while True:

        # apply velocity to ball position
        ball_x += velocity_x * ball_speed
        ball_y += velocity_y * ball_speed
        ball.x, ball.y = int(ball_x), int(ball_y)

        # only check if we've hit the bottom if y velocity is positive and if we've hit the top if y velocity is negative
        if (velocity_y < 0 and ball.y <= 0) or (velocity_y > 0 and ball.y + ball.height >= display.height):
            velocity_y *= -1  # invert y velocity
            play_sfx(SFX_WALL)
        
        # see if we've collided with a paddle
        if (velocity_x < 0 and collides(ball, paddles[0])) or (velocity_x > 0 and collides(ball, paddles[1])):
            velocity_x *= -1  # invert x velocity
            ball_speed = min(ball_speed * BALL_SPEED_MODIFIER, PADDLE_SPEED)  # increase ball speed by modifier
            play_sfx(SFX_PADDLE)

        # control computer player if gamepad isn't connected
        if not gamepads[1].connected and computer_move != 0:
            paddle_move(computer_move, 1)

        # light up neopixel based on ball position
        if peripherals.neopixels:
            # determine ball float position from 0 to n-1
            pos = ball.x / display.width * (peripherals.neopixels.n - 1)
            for i in range(peripherals.neopixels.n):
                # calculate difference from current index to ball position
                diff = abs(pos - i)
                # apply foreground color brightness based on distance to ball position
                peripherals.neopixels[i] = apply_brightness(foreground_palette[0], 1 - diff) if diff < 1 else 0
            peripherals.neopixels.show()

        # check if we've gone out of bounds
        if (velocity_x < 0 and ball.x + ball.width < 0) or (velocity_x > 0 and ball.x >= display.width):

            # hide ball
            ball.hidden = True
            if peripherals.neopixels:
                peripherals.neopixels.fill(0)
                peripherals.neopixels.show()

            # add to player score depending on x velocity direction
            player = int(velocity_x < 0)  # use velocity boolean as int of 0 or 1
            score = int(score_labels[player].text)  # obtain current score from label text string
            score += 1  # increment player score
            score_labels[player].text = str(score)  # update score label but keep integer variable for later checks

            play_sfx(SFX_SCORE)

            # check if we are above the minimum win score
            if score >= WIN_SCORE:
                # check if we are at least 2 points above the other player
                other_player = 1 - player  # invert player index
                other_score = int(score_labels[other_player].text)  # obtain other player's score form label text string
                if score - other_score >= WIN_DIFF:
                    # show win label
                    win_labels[player].hidden = False

                    # wait for user input
                    await wait_input()

                    # hide win label
                    win_labels[player].hidden = True

                    # reset scores
                    for label in score_labels:
                        label.text = "0"
            
            else:
                # delay before showing ball again and continuing
                await asyncio.sleep(1)

            # reset ball position to center
            ball.x = (display.width - ball.width) // 2
            ball.y = (display.height - ball.height) // 2
            ball_x, ball_y = ball.x, ball.y

            # randomize velocity
            velocity_x, velocity_y = get_random_velocity()

            # reset ball speed
            ball_speed = INITIAL_BALL_SPEED

            # show the ball
            ball.hidden = False

        await asyncio.sleep(1/30)

async def computer_task() -> None:
    global waiting, computer_move
    paddle = paddles[1]
    while True:
        if waiting or 0 < ball.y - paddle.y < paddle.height:  # if gameplay has stopped or we're facing the ball
            computer_move = 0
        else:
            computer_move = int(ball.y < paddle.y) * 2 - 1  # should be 1 if ball is below or -1 if ball is above
        await asyncio.sleep(random.random() * (COMPUTER_MAX_TIME - COMPUTER_MIN_TIME) + COMPUTER_MIN_TIME)

async def main() -> None:
    await asyncio.gather(
        asyncio.create_task(mouse_task()),
        asyncio.create_task(keyboard_task()),
        asyncio.create_task(gamepad_task()),
        asyncio.create_task(buttons_task()),
        asyncio.create_task(gameplay_task()),
        asyncio.create_task(computer_task()),
    )

try:
    asyncio.run(main())
except KeyboardInterrupt:
    peripherals.deinit()
