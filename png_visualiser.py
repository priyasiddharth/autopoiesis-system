import itertools
import logging
import math
import os
import shutil

from PIL import Image, ImageDraw, ImageFont

import world_model as world
import world_presenter as presenter
import world_viewer as viewer

OUT_DIR = './simulation_images'
GRID_SIZE = 20
HEIGHT = 600
WIDTH = HEIGHT


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


def create_grid_lines(image: Image, grid_size: int):
    # Draw some lines
    draw = ImageDraw.Draw(image)
    y_start = 0
    y_end = image.height
    step_size = int(image.width / grid_size)

    for x in range(0, image.width, step_size):
        line = ((x, y_start), (x, y_end))
        draw.line(line, fill='grey')

    x_start = 0
    x_end = image.width

    for y in range(0, image.height, step_size):
        line = ((x_start, y), (x_end, y))
        draw.line(line, fill='grey')

    del draw


def draw_line(image: Image, draw: ImageDraw, pstart: world.Point, pend: world.Point, grid_size: int, style: int):
    step_size = int(image.width / grid_size)
    x0 = step_size * pstart.x + int(step_size / 2)
    y0 = step_size * pstart.y + int(step_size / 2)
    x1 = step_size * pend.x + int(step_size / 2)
    y1 = step_size * pend.y + int(step_size / 2)
    draw.line(((x0, y0), (x1, y1)), fill='orange', width=1)


def draw_on_grid(image: Image, grid: [world.Point, world.T], grid_size: int):
    font = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeMono.ttf', 16)
    draw: ImageDraw = ImageDraw.Draw(image)
    step_size = int(image.width / grid_size)
    grid_x = 0
    for x0, x1 in pairwise(range(0, image.width + 1, step_size)):
        grid_y = 0
        for y0, y1 in pairwise(range(0, image.height + 1, step_size)):
            xmid = x0 + int((x1 - x0) / 2)
            ymid = y0 + int((y1 - y0) / 2)
            grid_element: world.T = grid[(grid_x, grid_y)]
            p = 'U'
            if isinstance(grid_element, world.Hole):
                p = 'H'
            elif isinstance(grid_element, world.Substrate):
                p = 'S'
            elif isinstance(grid_element, world.Link):
                if grid_element.isFree():
                    p = 'L'
                elif grid_element.isSinglyBonded():
                    p = 'b'
                    friend = grid[grid_element.getBondedLink(0).point]
                    draw_line(image, draw, pstart=grid_element.point, pend=friend.point, grid_size=grid_size, style=100)
                else:
                    p = 'B'
                    friend = grid[grid_element.getBondedLink(0).point]
                    draw_line(image, draw, pstart=grid_element.point, pend=friend.point, grid_size=grid_size, style=150)
                    friend = grid[grid_element.getBondedLink(1).point]
                    draw_line(image, draw, pstart=grid_element.point, pend=friend.point, grid_size=grid_size, style=150)
            elif isinstance(grid_element, world.Catalyst):
                p = 'K'
            draw.text((xmid, ymid), p, font=font, fill='black')

            grid_y += 1
        grid_x += 1
    del draw


def write_grid_to_disk(image: Image, iteration: int):
    with open('{0}/out_{1}.png'.format(OUT_DIR, iteration), 'wb') as f:
        image.save(f)


class PngViewer(viewer.WorldViewer):

    def updateView(self, grid: [world.Point, world.T], iteration):
        n = int(math.sqrt(len(grid)))
        print('iter:{0}'.format(iteration))
        image: Image = Image.new(mode='RGB', size=(HEIGHT, WIDTH), color='white')
        create_grid_lines(image, n)
        draw_on_grid(image, grid, n)
        write_grid_to_disk(image, iteration)

    def __init__(self):
        pass


def main():
    if os.path.isdir(OUT_DIR):
        shutil.rmtree(OUT_DIR)
    os.mkdir(OUT_DIR)
    path = 'config.json'
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
    view = PngViewer()
    # ctx = world.WorldFactory(logging_level='INFO').createWorld(helper.Config.loadConfigFromFile(path))
    grid_size = GRID_SIZE
    # weights = [14, 80, 6]  # H S K
    weights = [10, 88, 2]  # H S K
    grid_seed = 0
    proc_seed = 100
    disint_prb = 0.02
    iter = 25
    ctx: world.WorldContext = world.WorldFactory(logging_level='INFO').createRandomWorld(grid_size, weights,
                                                                                         grid_random_seed=grid_seed,
                                                                                         max_iter=iter,
                                                                                         proc_random_seed=proc_seed,
                                                                                         disintegrate_prob=disint_prb)
    exp = world.AliveDurationExperiment()
    presenter.ConsolePresenter(view, ctx, exp).doSimulate()


if __name__ == '__main__':
    main()
