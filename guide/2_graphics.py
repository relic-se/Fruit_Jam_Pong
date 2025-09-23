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
import sys
import supervisor
from terminalio import FONT
import vectorio

from adafruit_display_text.label import Label
import adafruit_fruitjam.peripherals
import adafruit_usb_host_mouse

# get Fruit Jam OS config if available
try:
    import launcher_config
    config = launcher_config.LauncherConfig()
except ImportError:
    config = None

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
root_group.append(ball)

# mouse control
async def mouse_task() -> None:
    while True:
        if (mouse := adafruit_usb_host_mouse.find_and_init_boot_mouse("bitmaps/cursor.bmp")) is not None:
            mouse.y = display.height // 2

            timeouts = 0
            previous_pressed_btns = []
            while timeouts < 9999:
                pressed_btns = mouse.update()
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
            if key == "\x1b":  # escape
                peripherals.deinit()
                supervisor.reload()
        await asyncio.sleep(1/30)

async def main() -> None:
    await asyncio.gather(
        asyncio.create_task(mouse_task()),
        asyncio.create_task(keyboard_task()),
    )

try:
    asyncio.run(main())
except KeyboardInterrupt:
    peripherals.deinit()
