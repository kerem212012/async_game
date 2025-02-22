import asyncio
import curses
import os
import random
import time

from animations.curses_tools import draw_frame, get_frame_size, read_controls
from animations.fire_animation import fire
from animations.obstacles import Obstacle, show_obstacles
from animations.physics import update_speed
from animations.stars import blink
from animations.starship import get_rockets, twice_cycle

COROUTINES = []
TIC_TIMEOUT = 0.1
OBSTACLES = []


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0

    rows, columns = get_frame_size(garbage_frame)
    current_obstacle = Obstacle(row, column, rows, columns)
    OBSTACLES.append(current_obstacle)

    try:
        while row < rows_number:
            draw_frame(canvas, row, column, garbage_frame)
            await asyncio.sleep(0)
            draw_frame(canvas, row, column, garbage_frame, negative=True)
            row += speed
            current_obstacle.row += speed
    finally:
        OBSTACLES.remove(current_obstacle)



def get_stars(canvas, row, column):
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
    frame_height, frame_width = get_frame_size(rockets[0])
    motion_height = row_height - frame_height
    motion_width = column_width - frame_width
    for frame in twice_cycle(rockets):
        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        row_speed, column_speed = update_speed(0, 0, rows_direction, columns_direction)
        row = max(1, min(row + row_speed, motion_height))
        column = max(1, min(column + column_speed, motion_width))
        draw_frame(canvas, row, column, frame)
        if space_pressed:
            COROUTINES.append(fire(canvas, row, column + 2))
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, frame, negative=True)


def draw(canvas):
    curses.curs_set(False)
    canvas.nodelay(True)
    row, column = curses.window.getmaxyx(canvas)
    ship = animate_spaceship(canvas, row / 2 - 3, column / 2)
    for _ in range(random.randint(50, 200)):
        COROUTINES.append(
            blink(canvas, random.randint(2, b=row - 2), random.randint(2, b=column - 2),
                  random.choice(["*", ".", ":", "+"])))
    COROUTINES.append(ship)
    COROUTINES.append(fill_orbit_with_garbage(canvas, column))
    loop = asyncio.get_event_loop()
    loop.create_task(show_obstacles(canvas, OBSTACLES))
    loop.create_task(async_draw(canvas))
    loop.run_forever()
async def async_draw(canvas):
    while True:
        for coroutine in COROUTINES.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                COROUTINES.remove(coroutine)

        canvas.refresh()
        await asyncio.sleep(TIC_TIMEOUT)

if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
