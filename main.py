import asyncio
import curses
import os
import random

from animations.curses_tools import draw_frame, get_frame_size, read_controls
from animations.explosion import explode
from animations.obstacles import Obstacle, show_obstacles
from animations.physics import update_speed
from animations.stars import blink, sleep
from animations.starship import get_rockets, twice_cycle

COROUTINES = []
TIC_TIMEOUT = 0.1
OBSTACLES = []
obstacles_in_last_collisions = []
YEAR = 1957
PHRASES = {
    1957: "First Sputnik",
    1961: "Gagarin flew!",
    1969: "Armstrong got on the moon!",
    1971: "First orbital space station Salute-1",
    1981: "Flight of the Shuttle Columbia",
    1998: 'ISS start building',
    2011: 'Messenger launch to Mercury',
    2020: "Take the plasma gun! Shoot the garbage!",
}


def get_garbage_delay_tics(year):
    if year < 1961:
        return None
    elif year < 1969:
        return 20
    elif year < 1981:
        return 14
    elif year < 1995:
        return 10
    elif year < 2010:
        return 8
    elif year < 2020:
        return 6
    else:
        return 2


async def get_text_for_info_frame(info_frame):
    global YEAR
    while True:
        await sleep(10)
        YEAR += 1
        massage = f"year: {YEAR} - {PHRASES.get(YEAR, '')}"
        info_frame.addstr(1, 1, massage)
        await asyncio.sleep(0)


async def show_game_over(canvas):
    with open(os.path.join("game_over", "game_over.txt"), "r") as f:
        game_over = f.read()
    row, column = curses.window.getmaxyx(canvas)
    while True:
        draw_frame(canvas, round(row / 2), round(column / 3), game_over)
        await asyncio.sleep(0)


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    while 0 < row < max_row and 0 < column < max_column:
        for obstacle in OBSTACLES.copy():
            if obstacle.has_collision(row, column):
                obstacles_in_last_collisions.append(obstacle)
                await explode(canvas, row, column)
                return
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


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
            if current_obstacle in obstacles_in_last_collisions:
                obstacles_in_last_collisions.remove(current_obstacle)
                return
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
        with open(os.path.join("garbage", garbage), "r") as f:
            trash = f.read()
        delay = get_garbage_delay_tics(YEAR)
        if delay:
            COROUTINES.append(fly_garbage(canvas, random.randint(1, column), trash))
            await sleep(delay)
        await asyncio.sleep(0)

async def animate_spaceship(canvas, row, column):
    rockets = get_rockets()
    row_height, column_width = canvas.getmaxyx()
    frame_height, frame_width = get_frame_size(rockets[0])
    motion_height = row_height - frame_height
    motion_width = column_width - frame_width
    for frame in twice_cycle(rockets):
        for obstacle in OBSTACLES.copy():
            if obstacle.has_collision(row, column):
                COROUTINES.append(show_game_over(canvas))
                return
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
    info_frame_length = 50
    info_frame_height = 4
    info_frame = canvas.derwin(row - info_frame_height, column - info_frame_length)
    COROUTINES.append(get_text_for_info_frame(info_frame))
    loop = asyncio.get_event_loop()
    loop.create_task(async_draw(canvas, info_frame))
    loop.run_forever()


async def async_draw(canvas, info_frame):
    while True:
        for coroutine in COROUTINES.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                COROUTINES.remove(coroutine)
        canvas.refresh()
        info_frame.refresh()
        await asyncio.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
