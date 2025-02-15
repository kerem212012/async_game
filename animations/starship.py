import asyncio
from itertools import cycle

from animations.curses_tools import draw_frame, get_frame_size, read_controls


def twice_cycle(iterable):
    for ship in cycle(iterable):
        for _ in range(2):
            yield ship


def get_rockets():
    with open("rocket/rocket_frame_1.txt", "r") as f1:
        frame_1 = f1.read()
    with open("rocket/rocket_frame_2.txt", "r") as f2:
        frame_2 = f2.read()
    rockets = [frame_1, frame_2]
    return rockets


async def animate_spaceship(canvas, row, column):
    rockets = get_rockets()
    row_height, column_width = canvas.getmaxyx()
    frame_height ,frame_width = get_frame_size(rockets[0])
    motion_height = row_height-frame_height
    motion_width = column_width-frame_width
    for frame in twice_cycle(rockets):
        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        row = max(1, min(row + rows_direction, motion_height))
        column = max(1, min(column + columns_direction, motion_width))
        draw_frame(canvas, row, column, frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, frame, negative=True)
