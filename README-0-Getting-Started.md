# [Fruit Jam Pong Tutorial](.#sections): 0. Getting Started

## About the Fruit Jam

First thing you are going to need is an [Adafruit Fruit Jam](https://www.adafruit.com/product/6200), and if you already have one, congrats! It is possible to get things running on different platforms, but for the simplicity of this tutorial and application, we are just going to focus on the Fruit Jam.

### Raspberry Pi RP2350b

This device has a few things about it that make it particularly special. The first being the Raspberry Pi RP2350b microcontroller chip that the system revolves around. This tiny, energy efficient chip is reasonably powerful with 2 150MHz ARM Cortex M33 cores as well as 2 RISC V cores which can be used instead _(but not concurrently)_. It also has native USB support which is a perfect match for CircuitPython. And since it is the B variant of the RP2350, it has a whole heck ton of GPIO, 48 in total, which means we can control a lot of external hardware.

Alongside the RP2350b, the Fruit Jam is jam packed with 16 MB of Flash and 8 MB PSRAM (+ 520 Kb SRAM). This essentially guarantees that we shouldn't run into any storage or memory bottlenecks.

### Audio and Video Output

As for audio and video, one trick of the RP2350 platform is HSTX, a built-in high speed serial transfer peripheral. This bus allows us to output a lot of data over DVI (within an HDMI form-factor) without putting too much strain on the processor itself. Divide and conquer!

And for audio, we have a TLV320DAC3100 stereo DAC with headphone output and a provided mono speaker. In my experience, it has provided simple, crystal clear audio and can be used as a line output with a little bit of adjustment of the DAC. As you'll see later, most of this is handled for us.

### USB Host

One thing you don't often see with microcontrollers is USB host support. With the help of TinyUSB and PIO (a unique feature of the Raspberry Pi Pico series of microcontrollers), the Fruit Jam can support a variety of USB peripherals powered by Python user code. This is perfect for HID-compliant devices such as Keyboard, Mice, and Gamepads, all of which we will cover in this tutorial.

All in all, the Fruit Jam has essentially everything you need to operate as a little microcomputer reminiscent of classic platforms of days past.

## CircuitPython

When you received your Fruit Jam, it likely already had some version of CircuitPython installed on it. Even so, I highly recommend installing the latest version of CircuitPython 10.x to ensure full compatibility and performance.

**Don't really know what CircuitPython is?** Before moving forward with this tutorial, it may be best to [learn more about the platform](https://learn.adafruit.com/welcome-to-circuitpython). This tutorial will assume a basic understanding of the Python programming language and the CircuitPython environment.

### Downloading the Firmware

Moving on, you can find the board page for the Fruit Jam on CircuitPython [here](https://circuitpython.org/board/adafruit_fruit_jam/). If you want to live on the bleeding edge _(it's fun here, trust me!)_, you can download the "absolute newest" version of CircuitPython 10.x+ [here](https://circuitpython.org/board/adafruit_fruit_jam/).

### Bootloader Mode

Once you have your firmware image as a `.uf2` file, you'll need to put your Fruit Jam into bootloader mode. This is a simple task on the Fruit Jam since all the necessary buttons are at your disposal. While powered on and plugged into your host computer, simply hold down "Button #1" (you'll see "UF2" written above it) and then press and release the "Reset" button. After a half second or so, you can release "Button #1". If the built-in bootloader did its job, you should see a USB drive labeled "RP2350" available on your computer.

### Installing the Firmware

To install the firmware, simply copy and paste (or drag) the `.uf2` file into the drive. Once the file transfer has completed, the device should reset and present two new USB drives, "CIRCUITPY" and "CPSAVES". You can ignore "CPSAVES" for this tutorial. All of our work will be done within the "CIRCUITPY" drive.

## REPL

You now have a working CircuitPython-powered Fruit Jam! But how do we talk to it? First of all, if you plug your device via HDMI into a display monitor, you should see a bunch of info and a prompt. This prompt is called "REPL". I won't get too deep into it, but this is basically where you can evaluate Python code in real-time ([more info](https://learn.adafruit.com/welcome-to-circuitpython/the-repl)). Heck, plug in a USB keyboard and start typing Python commands into it. If you're familiar with computers of yesteryear, it should remind you a little bit of a BASIC prompt.

Moving on, typing out python commands directly into the device is fine, but I don't recommend it for larger workflows. Instead, I recommend downloading and installing a Python IDE that is compatible with CircuitPython's REPL for writing, testing, and saving code. I personally use a combination of [VS Code](https://learn.adafruit.com/using-the-circuitpython-extension-for-visual-studio-code/overview) and [Thonny](https://thonny.org/), but play around with it and find what works best for you.

## Next Steps

Looks like you are all prepared to start making your first Fruit Jam application. [Let's get started with the bootstrap!](./README-1-Bootstrap.md)
