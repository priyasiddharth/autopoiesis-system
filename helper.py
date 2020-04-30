import ast

from python_json_config import ConfigBuilder

from world_model import *

LINKS_CONFIG = 'Links'

CATALYSTS_CONFIG = 'Catalysts'

SUBSTRATES_CONFIG = 'Substrates'

HOLES_CONFIG = 'Holes'

DEFAULT_CONFIG = 'default'

MAX_ITER = 'max_iter'

GRID_CONFIG = 'grid_size'

DISINTEGRATE_PROB_CONFIG = 'disintegration_probability'

STR_TO_CLASS = {'Hole': Hole, 'Substrate': Substrate,
                'Catalyst': Catalyst, 'Link': Link}


# This is a data object
class Config(object):

    def __init__(self, grid_size, default_elem, iter, h_plist, s_plist,
                 k_plist, l_plist, disint_prob: float):
        self.grid_size = grid_size
        self.default_element = default_elem
        self.iter: int = iter
        self.h_plist = h_plist
        self.s_plist = s_plist
        self.k_plist = k_plist
        self.l_plist = l_plist
        self.disintegrate_prob: float = disint_prob

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
        builder.add_required_field(DISINTEGRATE_PROB_CONFIG)

        builder.validate_field_type(GRID_CONFIG, int)
        builder.validate_field_type(MAX_ITER, int)
        builder.validate_field_type(DEFAULT_CONFIG, str)
        builder.validate_field_type(HOLES_CONFIG, [(int, int)])
        builder.validate_field_type(SUBSTRATES_CONFIG, [(int, int)])
        builder.validate_field_type(CATALYSTS_CONFIG, [(int, int)])
        builder.validate_field_type(LINKS_CONFIG, [(int, int)])
        builder.validate_field_type(DISINTEGRATE_PROB_CONFIG, float)

        # set up
        grid_size = config.grid_size
        default_element: T = STR_TO_CLASS[config.default]
        iter = config.max_iter
        disint_prob = config.disintegration_probability
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
                      k_plist, l_plist, disint_prob)
