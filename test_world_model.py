from unittest import TestCase

from world_model import *


class ChooseFirstStrategy(ChooseStrategy):

    def chooseOne(self, args: [T]) -> Optional[T]:
        if not args:
            return None
        return args[0]

    def shuffleList(self, args: [T]) -> [T]:
        return args.copy()

class TestElement(TestCase):
    def test_can_displace(self):
        pass

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
        self.assertDictEqual({Point(0, 0): Substrate(Point(0, 0), 2),
                              Point(0, 1): k,
                              Point(1, 0): h,
                              Point(1, 1): l},
                             grid)


class TestLinkProcess(TestCase):
    def test_displace_substrate(self):
        size = 4
        h = Hole(Point(3, 2), size)
        k1 = Catalyst(Point(1, 1), size)
        k2 = Catalyst(Point(1, 3), size)
        k3 = Catalyst(Point(0, 2), size)
        k4 = Catalyst(Point(2, 1), size)
        k5 = Catalyst(Point(0, 1), size)
        k6 = Catalyst(Point(2, 3), size)
        k7 = Catalyst(Point(3, 3), size)
        k8 = Catalyst(Point(3, 1), size)
        s = Substrate(Point(1, 2), size)
        l = Link(Point(0, 3), size)
        l1 = Link(Point(2, 2), size)
        l1.setFree(False)
        e_list = [h, k1, k2, k3, k4, k5, k6, k7, k8, s, l, l1]
        grid: [Point, Element] = {}
        for e in e_list:
            grid[e.point] = e
        expected_grid = grid.copy()
        hole_list = [e for e in e_list if isinstance(e, Hole)]
        substrate_list = [e for e in e_list if isinstance(e, Substrate)]
        catalyst_list = [e for e in e_list if isinstance(e, Catalyst)]
        link_list = [e for e in e_list if isinstance(e, Link)]
        choose_strategy = ChooseFirstStrategy()
        logger = logging.getLogger('test')
        hp = LinkProcess(grid, hole_list, substrate_list, catalyst_list, link_list, choose_strategy, logger)
        hp.displaceSubstrate(l, s)
        expected_grid[Point(3, 2)] = Substrate(Point(3, 2), size)
        expected_grid[Point(1, 2)] = Hole(Point(1, 2), size)
        self.assertDictEqual(expected_grid, grid)


class TestLink(TestCase):
    def test_is_bonding_angle_ok_returnsFalse(self):
        h = Hole(Point(1, 1), 2)
        l = Link(Point(0, 0), 2)
        l1 = Link(Point(1, 0), 2)
        l2 = Link(Point(0, 1), 2)
        l1.addBond(l2)
        l2.addBond(l1)
        e_list = [h, l, l1, l2]
        grid: [Point, Element] = {}
        for e in e_list:
            grid[e.point] = e
        self.assertFalse(l.isBondingAngleOk(l1, grid))
        self.assertFalse(l.isBondingAngleOk(l2, grid))

    def test_is_bonding_angle_ok_returnsTrue(self):
        h = Hole(Point(0, 1), 2)
        l = Link(Point(0, 0), 2)
        l1 = Link(Point(1, 0), 2)
        l2 = Link(Point(1, 1), 2)
        l1.addBond(l2)
        l2.addBond(l1)
        e_list = [h, l, l1, l2]
        grid: [Point, Element] = {}
        for e in e_list:
            grid[e.point] = e
        self.assertTrue(l.isBondingAngleOk(l1, grid))
        self.assertFalse(l.isBondingAngleOk(l2, grid))


class TestProcess(TestCase):
    def test_form_bond1(self):
        l_target = Link(Point(0, 0), 2)
        l1 = Link(Point(1, 0), 2)
        l2 = Link(Point(1, 1), 2)
        l3 = Link(Point(0, 1), 2)
        # l3 is free
        l1.addBond(l2)
        l2.addBond(l1)
        m_list = [l1, l2]
        n_list = [l3]
        grid = {Point(0, 0): l_target, Point(0, 1): l3, Point(1, 0): l1, Point(1, 1): l2}
        hole_list = []
        substrate_list = []
        link_list = [l_target, l1, l2, l3]
        catalyst_list = []
        choose_strategy = ChooseFirstStrategy()
        logger = logging.getLogger('test')
        p = HoleProcess(grid, hole_list, substrate_list, catalyst_list, link_list, choose_strategy, logger)
        p.formBond(l_target, m_list, n_list)
        self.assertCountEqual([l1, l3], l_target.getAllBondedLinks())

    def test_form_bond2(self):
        l_target = Link(Point(0, 0), 2)
        l1 = Link(Point(1, 0), 2)
        l2 = Link(Point(1, 1), 2)
        l3 = Link(Point(0, 1), 2)
        # no free L
        # (L1) -- (L2) -- (L3)
        l1.addBond(l2)
        l2.addBond(l1)
        l2.addBond(l3)
        l3.addBond(l2)
        m_list = [l1, l3]
        n_list = []
        grid = {Point(0, 0): l_target, Point(0, 1): l3, Point(1, 0): l1, Point(1, 1): l2}
        hole_list = []
        substrate_list = []
        link_list = [l_target, l1, l2, l3]
        catalyst_list = []
        choose_strategy = ChooseFirstStrategy()
        logger = logging.getLogger('test')
        p = HoleProcess(grid, hole_list, substrate_list, catalyst_list, link_list, choose_strategy, logger)
        p.formBond(l_target, m_list, n_list)
        self.assertCountEqual([l1, l3], l_target.getAllBondedLinks())
