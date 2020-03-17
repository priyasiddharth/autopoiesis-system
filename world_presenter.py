import ast
import typing
from typing import Dict

from python_json_config import ConfigBuilder

import helper
import world_model as world
import world_viewer as viewer
from world_model import Hole, Catalyst, Substrate, Link

LINKS_CONFIG = 'Links'

CATALYSTS_CONFIG = 'Catalysts'

SUBSTRATES_CONFIG = 'Substrates'

HOLES_CONFIG = 'Holes'

DEFAULT_CONFIG = 'default'

MAX_ITER = 'max_iter'

GRID_CONFIG = 'grid_size'

STR_TO_CLASS = {'Hole': world.Hole, 'Substrate': world.Substrate,
                'Catalyst': world.Catalyst, 'Link': world.Link}


class WorldPresenter(object):

    def __init__(self, viewer: viewer.WorldViewer):
        self._viewer = viewer
        self._iter = 0
        self._hole_process: world.HoleProcess = None
        self._link_process: world.LinkProcess = None
        self._catalyst_process: world.CatalystProcess = None
        self._prod_process: world.ProductionProcess = None
        self._disintegrate_process: world.DisintegrationProcess = None
        self._grid: Dict[world.Point: world.T] = {}

    def loadConfigFromFile(self, path):
        def makeElement(x: int, y: int, c: typing.TypeVar(world.T), grid_size: int):
            return c(world.Point(x, y), grid_size)

        builder = ConfigBuilder()
        config = builder.parse_config(path)
        builder.set_field_access_required()
        builder.add_required_field(GRID_CONFIG)
        builder.add_required_field(MAX_ITER)
        builder.add_required_field(DEFAULT_CONFIG)

        builder.validate_field_type(GRID_CONFIG, int)
        builder.validate_field_type(MAX_ITER, int)
        builder.validate_field_type(DEFAULT_CONFIG, str)
        builder.validate_field_type(HOLES_CONFIG, [(int, int)])
        builder.validate_field_type(SUBSTRATES_CONFIG, [(int, int)])
        builder.validate_field_type(CATALYSTS_CONFIG, [(int, int)])
        builder.validate_field_type(LINKS_CONFIG, [(int, int)])

        # set up
        grid_size = config.grid_size
        default_element: world.T = STR_TO_CLASS[config.default]
        self._iter = config.max_iter
        h_plist = [makeElement(x, y, Hole, grid_size) for x, y in
                   list(ast.literal_eval(config.Holes))] if config.Holes else []
        s_plist = [makeElement(x, y, Substrate, grid_size) for x, y in
                   list(ast.literal_eval(config.Substrates))] if config.Substrates else []
        k_plist = [makeElement(x, y, Catalyst, grid_size) for x, y in
                   list(ast.literal_eval(config.Catalysts))] if config.Catalysts else []
        l_plist = [makeElement(x, y, Link, grid_size) for x, y in
                   list(ast.literal_eval(config.Links))] if config.Links else []
        factory = world.WorldFactory()
        self._grid = factory.createGrid(h_plist, s_plist, k_plist, l_plist, default_element, grid_size)
        self._hole_process, self._link_process, self._catalyst_process, self._prod_process, self._disintegrate_process = factory.createAllProcesses(
            self._grid)

    def _doSingleStep(self):
        self._hole_process.doStep()
        self._link_process.doStep()
        self._catalyst_process.doStep()
        self._prod_process.doStep()
        self._disintegrate_process.doStep()
        link_list = [l for l in self._disintegrate_process.l_list if len(l.getAllBondedLinks()) == 2]
        r = []
        for l in link_list:
            r = helper.FindCycle(l, [])
            if r:
                return r
        return r

    def doSimulate(self):
        self._viewer.updateView(self._grid)
        for i in range(self._iter):
            r = self._doSingleStep()
            if len(r) >= 4:
                print('Found cycle:{0} len:{1} iter:{2}'.format(r, len(r), i))
                break
        self._viewer.updateView(self._grid)
        print('done')


class ConsolePresenter(WorldPresenter):

    def __init__(self, viewer: viewer.ConsoleViewer) -> None:
        super().__init__(viewer)


def main():
    path = 'config.json'
    view = viewer.ConsoleViewer()
    presenter = ConsolePresenter(view)
    presenter.loadConfigFromFile(path)
    presenter.doSimulate()


if __name__ == '__main__':
    main()
