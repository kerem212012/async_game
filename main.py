import os
import random
import time
from animations.fire_animation import *
from animations.space_garbage import fly_garbage
from animations.stars import blink
from animations.starship import animate_spaceship

COROUTINES = []
TIC_TIMEOUT = 0.1

def get_stars(canvas,row,column):
    symbols = ["*", ".", ":", "+"]
    stars_count = random.randint(50, 200)
    for _ in range(stars_count):
        COROUTINES.append(
            blink(canvas, random.randint(0, b=row - 1), random.randint(0, b=column - 1), random.choice(symbols)))

async def fill_orbit_with_garbage(canvas, column):
    while True:
        garbage = random.choice(os.listdir("garbage"))
        with open(f"garbage/{garbage}", "r") as f:
            trash = f.read()
        COROUTINES.append(fly_garbage(canvas, random.randint(1, column), trash))
        await asyncio.sleep(0)


def draw(canvas):
    curses.curs_set(False)
    canvas.nodelay(True)
    row, column = curses.window.getmaxyx(canvas)
    ship = animate_spaceship(canvas, row / 2 - 3, column / 2)
    get_stars(canvas,row, column)
    COROUTINES.append(ship)
    COROUTINES.append(fill_orbit_with_garbage(canvas, column))
    while True:
        for coroutine in COROUTINES.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                COROUTINES.remove(coroutine)

        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
