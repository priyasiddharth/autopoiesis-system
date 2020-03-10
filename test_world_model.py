from unittest import TestCase

from world_model import *


class ChooseFirstStrategy(ChooseStrategy):

    def chooseOne(self, args: [Element]) -> Element:
        assert len(args) > 0
        return args[0]


class TestElement(TestCase):
    def test_can_displace(self):
        self.fail()

    def test_get_neighbours(self):
        e = Element(Point(5, 5), 10)
        self.assertCountEqual([(4, 4), (6, 4), (6, 6), (4, 6), (4, 5), (5, 4), (6, 5), (5, 6)], e.getNeighbours())

        # LU corner
        e = Element(Point(0, 0), 5)
        self.assertCountEqual([(0, 1), (1, 0), (1, 1)], e.getNeighbours())

        # LL corner
        e = Element(Point(0, 4), 5)
        self.assertCountEqual([(0, 3), (1, 4), (1, 3)], e.getNeighbours())

        # RL corner
        e = Element(Point(4, 4), 5)
        self.assertCountEqual([(4, 3), (3, 4), (3, 3)], e.getNeighbours())

        # RU corner
        e = Element(Point(4, 0), 5)
        self.assertCountEqual([(3, 0), (4, 1), (3, 1)], e.getNeighbours())


class TestHoleProcess(TestCase):
    def test_do_step(self):
        h = Hole(Point(0, 0), 2)
        k = Catalyst(Point(0, 1), 2)
        s = Substrate(Point(1, 0), 2)
        l = Link(Point(1, 1), 2)
        grid = {Point(0, 0): h, Point(0, 1): k, Point(1, 0): s, Point(1, 1): l}
        hole_list = [h]
        substrate_list = [s]
        link_list = [l]
        catalyst_list = [k]
        choose_strategy = ChooseFirstStrategy()
        logger = logging.getLogger('test')
        hp = HoleProcess(grid, hole_list, substrate_list, catalyst_list, link_list, choose_strategy, logger)
        hp.doStep()
        self.assertDictEqual({Point(0, 0): Catalyst(Point(0, 0), 2),
                              Point(0, 1): Hole(Point(0, 1), 2),
                              Point(1, 0): s,
                              Point(1, 1): l},
                             grid)
