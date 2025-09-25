# [Fruit Jam Pong Tutorial](.#sections): 6. Increasing Difficulty

This section should be a shorter than the previous systems. Our goal is to elaborate on the `BALL_SPEED` constant by making it... well, less constant.

## Update Constants

Let's establish our foundation:

``` python
INITIAL_BALL_SPEED = 1
BALL_SPEED_MODIFIER = 1.25
```

We still want to start out at the original speed, but we'll change `BALL_SPEED` to `INITIAL_BALL_SPEED` to make that more clear.

Then, we'll add a second constant called `BALL_SPEED_MODIFIER` which will be multiplied against the current ball speed on each paddle hit. I chose `1.25` here which translates to a 25% speed increase.

## Add Speed Variable

In order to this implemented, let's take a look at our gameplay loop:

``` python
async def gameplay_task() -> None:
    # ...
    ball_speed = INITIAL_BALL_SPEED
    while True:
        # apply velocity to ball position
        ball.x += int(velocity_x * ball_speed)
        ball.y += int(velocity_y * ball_speed)
        # ...
```

We'll be using a new local variable called `ball_speed` to store the current speed value. To begin, it should be our starting value, `INITIAL_BALL_SPEED`. Then, just replace our previous references to `BALL_SPEED` with our new variable.

> **Hot Tip:** The x and y position of a `vectorio.Rectangle` object only supports integer values, and will raise a `ValueError` exception if we attempt to set it to a float value. That's why we're using `int()` here to cast it to an integer.

### Modifying Speed on Paddle Collision

This is all good, but the ball is still just putting along at the initial speed. We need to implement the `BALL_SPEED_MODIFIER` constant we defined earlier.

``` python
# see if we've collided with a paddle
if (velocity_x < 0 and collides(ball, paddles[0])) or (velocity_x > 0 and collides(ball, paddles[1])):
    velocity_x *= -1  # invert x velocity
    ball_speed = min(ball_speed * BALL_SPEED_MODIFIER, PADDLE_SPEED)  # increase ball speed by modifier
```

Here, we're updating `ball_speed` whenever we've detected that the ball has collided with a player paddle. I've added in the built-in function `min` which will return the smaller of the two values. In this case, we want to make sure that the ball speed isn't faster than the player paddle speed. If it were, it might be impossible to get the ball! So, let's keep it fair with this method.

> If even `PADDLE_SPEED` feels too fast, try adding another constant, `MAXIMUM_BALL_SPEED` with your preferred maximum ball velocity and putting it in its place.

### Reset Speed to Initial

Now, we need to make sure that when one player scores the ball speed resets back to the initial value. After randomizing the velocity, add the following code to bring us back to speed:

``` python
# reset ball speed
ball_speed = INITIAL_BALL_SPEED
```

## Floating Ball Position

If you run the game, you may notice that the speed doesn't actually change for a while until after a few paddle hits. _Why is that?_ I'll tell you why, because of integers!

When we cast to an integer value using `int(...)`, we truncate the float value down. That means that something like `1.99` actually becomes just `1`. Although `ball_speed` is going up at a smooth rate, it won't actually affect the velocity at a greater pace until it hits the next integer value, in this case `2`.

We definitely need to fix this! And the way to do so is by keeping a separate copy of the ball's x and y position. We can keep updating that float value using our velocity and then truncate it down to the ball's actual position.

> This type of workflow has been used for a long time to achieve smooth movement while being restricted to pixel-based positioning. Try looking up _"Super Mario Bros Subpixel Player Position"_ to see what schenanigans speedrunners get into abusing these systems!

To begin, let's create our new variables, `ball_x` and `ball_y`, when we set up `ball_speed`:

``` python
ball_x, ball_y = ball.x, ball.y
ball_speed = INITIAL_BALL_SPEED
```

Then, instead of updating the ball object, update these new variables instead:

``` python
# apply velocity to ball position
ball_x += velocity_x * ball_speed
ball_y += velocity_y * ball_speed
ball.x, ball.y = int(ball_x), int(ball_y)
```

And right after we update the float variables, we'll truncate them down and update the ball object itself. Simple but effective!

But don't forget to reset our variables when we go out of bounds:

``` python
# reset ball position to center
ball.x = (display.width - ball.width) // 2
ball.y = (display.height - ball.height) // 2
ball_x, ball_y = ball.x, ball.y
```

Try playing the game now. You'll quickly see that the ball speeds up at a steady rate with every paddle hit. Heck, it even gets pretty difficult after a few knocks.

## Final Code

After these quick adjustments, your code should now look something like this:
> [guide/6_increasing-difficulty.py](./guide/6_increasing-difficulty.py)

## Next Steps

Now that we've got a good feeling two player game of Pong, it's still feeling a little dry. [Let's fix that by adding sound effects!](./README-7-Sound-Effects.md)
