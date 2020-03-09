from unittest import TestCase

from world_model import *


class ChooseFirstStrategy(ChooseStrategy):

    def chooseOne(self, *args):
        assert len(args) > 0
        return args[1]


class TestElement(TestCase):
    def test_can_displace(self):
        self.fail()

    def test_get_neighbours(self):
        e = Element(Point(5, 5), 10)
        self.assertCountEqual([(4, 5), (5, 4), (6, 5), (5, 6)], e.getNeighbours(), e)

        # LU corner
        e = Element(Point(0, 0), 5)
        self.assertCountEqual([(0, 1), (1, 0)], e.getNeighbours(), e)

        # LL corner
        e = Element(Point(0, 4), 5)
        self.assertCountEqual([(0, 3), (1, 4)], e.getNeighbours(), e)

        # RL corner
        e = Element(Point(4, 4), 5)
        self.assertCountEqual([(4, 3), (3, 4)], e.getNeighbours(), e)

        # RU corner
        e = Element(Point(4, 0), 5)
        self.assertCountEqual([(3, 0), (4, 1)], e.getNeighbours(), e)
