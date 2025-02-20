import os
import random
import time
import asyncio
import curses
from animations.starship import get_rockets,twice_cycle
from animations.fire_animation import fire
from animations.space_garbage import fly_garbage
from animations.stars import blink
from animations.curses_tools import draw_frame, get_frame_size, read_controls
from animations.physics import update_speed

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
async def animate_spaceship(canvas, row, column):
    rockets = get_rockets()
    row_height, column_width = canvas.getmaxyx()
    frame_height ,frame_width = get_frame_size(rockets[0])
    motion_height = row_height-frame_height
    motion_width = column_width-frame_width
    for frame in twice_cycle(rockets):
        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        row_speed, column_speed = update_speed(0,0,rows_direction,columns_direction)
        row = max(1, min(row + row_speed, motion_height))
        column = max(1, min(column + column_speed, motion_width))
        draw_frame(canvas, row, column, frame)
        if space_pressed:
            COROUTINES.append(fire(canvas,row,column+2))
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, frame, negative=True)

def draw(canvas):
    curses.curs_set(False)
    canvas.nodelay(True)
    row, column = curses.window.getmaxyx(canvas)
    ship = animate_spaceship(canvas, row / 2 - 3, column / 2)
    for _ in range(random.randint(50, 200)):
        COROUTINES.append(
            blink(canvas, random.randint(2, b=row - 2), random.randint(2, b=column - 2), random.choice(["*", ".", ":", "+"])))
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
