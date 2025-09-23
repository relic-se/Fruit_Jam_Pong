# Fruit Jam Pong
Tutorial code for how to make a simple pong game for the Adafruit Fruit Jam in CircuitPython 

## Sections

### [0. Getting Started](./README-0-Getting-Started.md)
Not yet familiar with your Fruit Jam or CircuitPython? We will quickly go over how to get your device set up and running with CircuitPython.

### [1. Bootstrap](./README-1-Bootstrap.md)
Using the [relic-se/Fruit_Jam_Application](https://github.com/relic-se/Fruit_Jam_Application) template to skip a few steps...

### [2. Graphics](./README-2-Graphics.md)
Getting straight to it by using `displayio` to set up our pong playing field.

### [3. Controls](./README-3-Controls.md)
Support a variety of user inputs to control the paddles and the game state including keyboard, mouse, gamepad, and hardware buttons.

### [4. Ball Movement](./README-4-Ball-Movement.md)
Control the pong ball's position with velocity and handle collisions.

### [5. Scoring](./README-5-Scoring.md) *- Coming Soon*
Determine when a player has scored and handle win conditions.

### [6. Increasing Difficulty](./README-6-Increasing-Difficulty.md) *- Coming Soon*
Increase ball speed with each paddle hit.

### [7. Sound Effects](./README-7-Sound-Effects.md) *- Coming Soon*
Using `synthio` to create basic sound effects which closely resemble the original arcade game.

### [8. Computer Control](./README-8-Computer-Control.md) *- Coming Soon*
Control the CPU in a single-player match using simple logic.

### [9. NeoPixels](./README-9-NeoPixels.md) *- Coming Soon*
Add some icing on top by displaying the ball position on the Fruit Jam's NeoPixels.

## Building Project Bundle
Ensure that you have python 3.x installed system-wide and all the prerequisite libraries installed using the following command:

``` shell
pip install circup requests
```

Download all CircuitPython libraries and package the application using the following command:

``` shell
python build/build.py
```

The project bundle should be found within `./dist` as a `.zip` file with the same name as your repository.
