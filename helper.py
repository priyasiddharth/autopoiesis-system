import ast
import collections
from typing import List

from python_json_config import ConfigBuilder

from world_model import *

LINKS_CONFIG = 'Links'

CATALYSTS_CONFIG = 'Catalysts'

SUBSTRATES_CONFIG = 'Substrates'

HOLES_CONFIG = 'Holes'

DEFAULT_CONFIG = 'default'

MAX_ITER = 'max_iter'

GRID_CONFIG = 'grid_size'

STR_TO_CLASS = {'Hole': Hole, 'Substrate': Substrate,
                'Catalyst': Catalyst, 'Link': Link}

Life = collections.namedtuple('Life', ['born', 'dead', 'length'])


def FindCycle(link: 'Link', visited: ['Link']) -> List['Link']:
    if link.isFree():
        return []
    if link.isSinglyBonded():
        return []
    if len(link.getAllBondedLinks()) == 2:
        if not link.getBondedLink(0) in visited:
            r = FindCycle(link.getBondedLink(0), visited + [link])
        elif not link.getBondedLink(1) in visited:
            r = FindCycle(link.getBondedLink(1), visited + [link])
        else:
            return [link]
        if not r:
            return []
        else:
            return [link] + r


# This is a data object
class Config(object):

    def __init__(self, grid_size, default_elem, iter, h_plist, s_plist,
                 k_plist, l_plist):
        self.grid_size = grid_size
        self.default_element = default_elem
        self.iter: int = iter
        self.h_plist = h_plist
        self.s_plist = s_plist
        self.k_plist = k_plist
        self.l_plist = l_plist

    @staticmethod
    def loadConfigFromFile(path) -> 'Config':
        def makeElement(x: int, y: int, c: typing.TypeVar(T),
                        grid_size: int):
            return c(Point(x, y), grid_size)

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
        default_element: T = STR_TO_CLASS[config.default]
        iter = config.max_iter
        h_plist = [makeElement(x, y, Hole, grid_size) for x, y in
                   list(ast.literal_eval(config.Holes))] if config.Holes else []
        s_plist = [makeElement(x, y, Substrate, grid_size) for x, y in
                   list(ast.literal_eval(
                       config.Substrates))] if config.Substrates else []
        k_plist = [makeElement(x, y, Catalyst, grid_size) for x, y in
                   list(ast.literal_eval(
                       config.Catalysts))] if config.Catalysts else []
        l_plist = [makeElement(x, y, Link, grid_size) for x, y in
                   list(ast.literal_eval(config.Links))] if config.Links else []
        return Config(grid_size, default_element, iter, h_plist, s_plist,
                      k_plist, l_plist)


class Experiment(object):

    def __int__(self):
        pass

    def addRecord(self, born: int, dead: int, length: int):
        pass

    def process(self):
        pass


class AliveDurationExperiment(Experiment):

    def __init__(self):
        super().__init__()
        self.alive_durations: List[Life] = []

    def addRecord(self, born: int, dead: int, length: int):
        self.alive_durations.append(Life(born, dead, length))

    def process(self):
        return [(d.dead - d.born, d.length) for d in self.alive_durations]
