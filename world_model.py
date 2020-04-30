"""World model.

This contains the definition of basic constructs like Elements and then uses
Processes to work on those Elements.
"""
import collections
import itertools
import logging
import math
import random
import typing
from typing import Dict, List, TypeVar, Optional

Point = collections.namedtuple('Point', ['x', 'y'])
Life = collections.namedtuple('Life', ['born', 'dead', 'length'])

T = TypeVar('T', bound='Element')  # Declare type variable
DISINTEGRATE_PROB = 0.1


class ChooseStrategy(object):

    def __init__(self):
        pass

    def chooseOne(self, args: [T]) -> Optional[T]:
        pass

    def shuffleList(self, args: [T]) -> [T]:
        """Returns a new 'shuffled' copy of the list.

        :param args:
        :return:
        """
        pass

    def chooseDisintegrate(self) -> bool:
        """ Returns True with some probability

        :return: True with some probability
        """
        pass

    def chooseIntegrate(self) -> bool:
        """Returns True with some probability

        :return: True with some probability
        """


# TODO: Do I need to mark cells as non-existent to help debugging?
class Element(object):
    """Base class common to L, K, S and H

    Assume grid is laid out in the following manner.
    ----x-->(n-1)
    |
    |
    y
    |
    v
    (n-1)
    """

    def __init__(self, p: Point, n: int):
        assert n > p.x > -1 and n > p.y > -1
        self.point: Point = p
        self._grid_size: int = n

    def canDisplace(self, o: T) -> bool:
        pass

    def getGridSize(self) -> int:
        return self._grid_size

    def isNeighbour(self, o: T) -> bool:
        if o.point in self.getNeighbours():
            return True
        return False

    # TODO: this fn may not be needed
    def hasNeighbourOfType(self, c: typing.Type[T],
                           grid: Dict[Point, T]) -> bool:
        nbours = self.getNeighbours()
        for n in nbours:
            n_o = grid[n]
            if isinstance(n_o, c):
                return True
        return False

    def getNeighboursOfType(self, c: typing.Type[T], grid: Dict[Point, T]) -> [
        T]:
        assert self.hasNeighbourOfType(c, grid)
        nbours = self.getNeighbours()
        l = []
        for n in nbours:
            n_o = grid[n]
            if isinstance(n_o, c):
                l.append(typing.cast(c, n_o))
        return l

    def getNeighbours(self) -> [Point]:
        return self._getNeighbours(1)

    def getOrthoNeighbours(self) -> [Point]:
        return self._getNeighbours(1, ortho=True)

    def _getNeighbours(self, d: int, ortho: bool = False) -> [Point]:
        """

          :return: A list of Points in 2D clockwise order
          """
        n = []
        x = self.point.x
        y = self.point.y

        # north
        if y - d >= 0:
            n.append(Point(x, y - d))

        # east
        if x + d < self._grid_size:
            n.append(Point(x + d, y))

        # south
        if y + d < self._grid_size:
            n.append(Point(x, y + d))

        # west
        if x - d >= 0:
            n.append(Point(x - d, y))

        if d < 2 and not ortho:
            # NW
            if y - d >= 0 and x - d >= 0:
                n.append(Point(x - d, y - d))
            # NE
            if y - d >= 0 and x + d < self._grid_size:
                n.append(Point(x + d, y - d))
            # SE
            if y + d < self._grid_size and x + d < self._grid_size:
                n.append(Point(x + d, y + d))
            # SW
            if y + d < self._grid_size and x - d >= 0:
                n.append(Point(x - d, y + d))
        return n

    def getExtendedNeighbours(self) -> [Point]:
        return self._getNeighbours(2)

    def chooseNeighbour(self, chooser: ChooseStrategy) -> T:
        return chooser.chooseOne(self.getNeighbours())

    def swap(self, o: T):
        temp = o.point
        o.point = self.point
        self.point = temp

    def __repr__(self):
        return '{0}:({1},{2})'.format(self.__class__.__name__, self.point.x,
                                      self.point.y)

    def __eq__(self, other):
        if type(self) == type(other) and self.point == other.point:
            return True
        return False


class Hole(Element):

    def chooseNeighbour(self, chooser: ChooseStrategy) -> Element:
        return super().chooseNeighbour(chooser)

    def __init__(self, p: Point, n: int):
        super().__init__(p, n)

    def canDisplace(self, o):
        return False


class Substrate(Element):

    @staticmethod
    def createsubstrate(x: int, y: int, n: int):
        return Substrate(Point(x, y), n)

    def __init__(self, p: Point, n: int):
        super().__init__(p, n)

    def canDisplace(self, o):
        if isinstance(o, Hole):
            return True
        else:
            return False


class Catalyst(Element):

    def __init__(self, p: Point, n: int):
        super().__init__(p, n)

    def canDisplace(self, o):
        # TODO: Consider bonded links cannot be broken
        if isinstance(o, (Hole, Substrate, Link)):
            return True
        else:
            return False


class Link(Element):

    @staticmethod
    def createlink(x: int, y: int, n: int):
        return Link(Point(x, y), n)

    def __init__(self, p: Point, n: int):
        self._bonded: ['Link'] = []
        super().__init__(p, n)

    def canDisplace(self, o):
        if isinstance(o, (Hole, Substrate)):
            return True
        else:
            return False

    def setFree(self, b: bool):
        self._free = b

    def isFree(self):
        return len(self._bonded) == 0

    def canBond(self):
        return len(self._bonded) < 2

    def isSinglyBonded(self) -> bool:
        return len(self._bonded) == 1

    def addBond(self, l: 'Link'):
        assert self.isNeighbour(l)
        assert len(self._bonded) <= 1
        if l in self._bonded:
            # TODO: log a warning here
            return
        self._bonded.append(l)

    def removeBond(self, l: 'Link') -> bool:
        if l in self._bonded:
            self._bonded.remove(l)
            l.removeBond(self)

    def getAllBondedLinks(self) -> ['Link']:
        return self._bonded

    def getBondedLink(self, index: int) -> 'Link':
        assert -1 < index < 2
        return self._bonded[index]

    def isBondingAngleOk(self, l: 'Link', grid: Dict[Point, Element]) -> bool:
        """Return True if resulting bonding angle will be >= 90 deg.

        This impl uses the following observation.
        1. If l is in ortho list then l1 must not be in ortho list (i.e. can be a neighbour)
        2. if l is not in ortho list then l1 must not be a neighbour

        :param l: the singly bonded neighbour to consider
        :param grid: the grid layout
        :return: True if resulting bond angle >=90 deg False otherwise
        """
        # TODO: Fix cond when singly wants to bond to with free and two singly want to bond together
        if self.isFree() and l.isFree():
            return True
        if not self.canBond() or not l.canBond():
            return False
        this, other = sorted([self, l],
                             key=lambda x: len(x.getAllBondedLinks()))
        assert other.isSinglyBonded()
        l1 = other.getBondedLink(0)
        ortho_list = [grid[n] for n in this.getOrthoNeighbours()]
        n_list = [grid[n] for n in this.getNeighbours()]
        assert other in n_list
        if other in ortho_list:
            if l1 in ortho_list:
                return False
        else:
            if l1 in n_list:
                return False
        return True

    def __eq__(self, other):
        return super().__eq__(other) and self._bonded == other._bonded


# base class for creating the overall algorithm
class Process(object):

    def __init__(self,
                 grid: Dict[Point, Element],
                 hole_list: List[Hole],
                 substrate_list: List[Substrate],
                 catalyst_list: List[Catalyst],
                 link_list: [List],
                 choose_strategy: ChooseStrategy,
                 logger: logging.Logger):
        self.grid: Dict[Point, Element] = grid
        self.h_list: List[Hole] = hole_list
        self.s_list: List[substrate_list] = substrate_list
        self.k_list: List[Catalyst] = catalyst_list
        self.l_list: List[Link] = link_list
        self.chooser: ChooseStrategy = choose_strategy
        self.logger: logging.Logger = logger

    def doSwap(self, this: Element, other: Element):
        self.logger.debug('Swapping {0} and {1}'.format(this, other))
        temp = self.grid[this.point]
        self.grid[this.point] = other
        self.grid[other.point] = temp
        this.swap(other)

    def checkBondAngle(self, l1: Link, l2: Link):
        return l1.isBondingAngleOk(l2, self.grid) and l2.isBondingAngleOk(l1, self.grid)

    def dobondTwo(self, l1: Link, l2: Link):
        self.logger.debug('Bonding {0} and {1}'.format(l1, l2))
        assert l1.isBondingAngleOk(l2, self.grid) and l2.isBondingAngleOk(l1, self.grid)
        l1.addBond(l2)
        l2.addBond(l1)

    def formBond(self, target: Link, m_list: [Link], n_list: [Link]):
        def bondWithFreeL(target: Link, n_list: [Link]):
            # 6.41
            n_list_filtered = [n for n in n_list if
                               self.checkBondAngle(n, target)]
            # 6.42
            if not n_list_filtered:
                return
            # 6.43
            n = self.chooser.chooseOne(n_list_filtered)
            self.dobondTwo(target, n)

        # 6.2
        m_list = [m for m in m_list if self.checkBondAngle(target, m)]
        # 6.3
        if len(m_list) >= 1:
            m1 = self.chooser.chooseOne(m_list)
            self.dobondTwo(target, m1)
            # 6.3 contd
            if len(m_list) > 1:
                # remove m1
                m_list.remove(m1)
                m2 = self.chooser.chooseOne([m for m in m_list if self.checkBondAngle(target, m)])
                if m2 is None:
                    bondWithFreeL(target, n_list)
                    return
                else:
                    self.dobondTwo(target, m2)
                    return
        # 6.4
        bondWithFreeL(target, n_list)

    def doBond(self):
        # 6
        new_list = [l for l in self.l_list if l.isFree()]
        if not new_list:
            return
        for link in self.chooser.shuffleList(new_list):
            # 6.1
            if link.hasNeighbourOfType(Link, self.grid):
                m_list = [n for n in link.getNeighboursOfType(Link, self.grid)
                          if n.isSinglyBonded()]
                n_list = [n for n in link.getNeighboursOfType(Link, self.grid)
                          if n.isFree()]
                self.formBond(link, m_list, n_list)

    def doStep(self):
        # check grid is valid
        bonded_l_list = [l for l in self.l_list if not l.isFree()]
        for l in bonded_l_list:
            for n in l.getAllBondedLinks():
                # check that bonds is between links only
                assert isinstance(n, Link)
                # check that the bond is mutually recognised by both links
                assert l in n.getAllBondedLinks()

    def displaceSubstrate(self, element: T, neighbour: T):

        # 2.321
        if neighbour.hasNeighbourOfType(Hole, self.grid):
            neighbour_hole = self.chooser.chooseOne(
                neighbour.getNeighboursOfType(Hole, self.grid))
            self.doSwap(neighbour, neighbour_hole)
            self.doSwap(element, neighbour_hole)
        # 2.322
        elif neighbour.hasNeighbourOfType(Link, self.grid):
            links = neighbour.getNeighboursOfType(Link, self.grid)
            # remove 'this'
            links.remove(element) if element in links else None
            l = self.chooser.chooseOne([l for l in links if not l.isFree()])
            if not l:
                # 2.323
                self.doSwap(element, neighbour)
                return
            h = self.chooser.chooseOne([h for h in l.getNeighboursOfType(Hole,
                                                                         self.grid)]) if l.hasNeighbourOfType(
                Hole, self.grid) else []
            if not h:
                # 2.323
                self.doSwap(element, neighbour)
                return
            self.doSwap(neighbour, h)
            self.doSwap(element, h)
        # 2.323
        else:
            self.doSwap(element, neighbour)

    def moveLink(self, link: Link, neighbour: Element) -> bool:
        # 2.32 'S will be displaced'
        if isinstance(neighbour, Substrate):
            self.displaceSubstrate(link, neighbour)
            return True
        # 2.33
        elif isinstance(neighbour, Hole):
            self.doSwap(link, neighbour)
            return True
        # 2.31
        elif isinstance(neighbour, (Link, Catalyst)):
            # do nothing
            return False


def GridPrettyPrintHelper(grid: Dict[Point, T]) -> str:
    m = int(math.sqrt(len(grid)))
    out = []
    for j in range(m):
        for i in range(m):
            c = grid[(i, j)]
            if isinstance(c, Hole):
                out.append('H')
            elif isinstance(c, Substrate):
                out.append('S')
            elif isinstance(c, Link):
                if c.isFree():
                    out.append('L')
                elif c.isSinglyBonded():
                    out.append('b')
                else:
                    out.append('B')
            elif isinstance(c, Catalyst):
                out.append('K')
            out.append(' ')  # space between chars
        out.append('\n')
    return ''.join(out)


class HoleProcess(Process):

    def __init__(self, grid: Dict[Point, Element], hole_list: List[Hole],
                 substrate_list: List[Substrate],
                 catalyst_list: List[Catalyst], link_list: [List],
                 choose_strategy: ChooseStrategy,
                 logger: logging.Logger):
        super().__init__(grid, hole_list, substrate_list, catalyst_list,
                         link_list, choose_strategy, logger)

    def doStep(self):
        super().doStep()
        for hole in self.chooser.shuffleList(self.h_list):
            n = self.grid[hole.chooseNeighbour(self.chooser)]
            # 1.30
            if isinstance(n, (Substrate, Catalyst)):
                self.doSwap(hole, n)
            elif isinstance(n, Link):
                if n.isFree():
                    self.doSwap(hole, n)
                # 1.32 'L is bonded, swap with extended neighbour S'
                elif n.hasNeighbourOfType(Substrate, self.grid):
                    s_list = [s for s in
                              n.getNeighboursOfType(Substrate, self.grid)]
                    en_list = hole.getExtendedNeighbours()
                    # find the right extended neighbour
                    common_s = [e for e in en_list if e in s_list]
                    self.doSwap(hole, common_s[0]) if common_s else None
            # 1.31
            elif isinstance(n, Hole):
                # do nothing
                pass
            # 1.4
            self.doBond()


class LinkProcess(Process):

    def __init__(self, grid: Dict[Point, Element], hole_list: List[Hole],
                 substrate_list: List[Substrate],
                 catalyst_list: List[Catalyst], link_list: [List],
                 choose_strategy: ChooseStrategy,
                 logger: logging.Logger):
        super().__init__(grid, hole_list, substrate_list, catalyst_list,
                         link_list, choose_strategy, logger)

    def doStep(self):
        super().doStep()
        free_l_list = [l for l in self.l_list if l.isFree()]
        for link in self.chooser.shuffleList(free_l_list):
            # only choose one neighbour to operate upon
            n = self.grid[link.chooseNeighbour(self.chooser)]
            # this is best effort so don't care about return type
            self.moveLink(link, n)
            # 2.4
            self.doBond()


class CatalystProcess(Process):

    def __init__(self, grid: Dict[Point, Element], hole_list: List[Hole],
                 substrate_list: List[Substrate],
                 catalyst_list: List[Catalyst], link_list: [List],
                 choose_strategy: ChooseStrategy,
                 logger: logging.Logger):
        super().__init__(grid, hole_list, substrate_list, catalyst_list,
                         link_list, choose_strategy, logger)

    def doStep(self):
        super().doStep()
        # 3.1
        for catalyst in self.chooser.shuffleList(self.k_list):
            # 3.2
            n = self.grid[catalyst.chooseNeighbour(self.chooser)]
            # 3.32 except bonding
            moved_link = False
            if (isinstance(n, Link)) and n.isFree():
                for nl in self.chooser.shuffleList(n.getNeighbours()):
                    # if L was moved then swap K and L
                    if self.moveLink(n, nl):
                        self.doSwap(catalyst, nl)
                        moved_link = True
                        break
                # 3.34
                if not moved_link:
                    self.doSwap(catalyst, n)
            # 3.33
            elif isinstance(n, Substrate):
                self.displaceSubstrate(catalyst, n)
            # 3.35
            elif isinstance(n, Hole):
                self.doSwap(catalyst, n)
            # 3.3
            elif isinstance(n, Catalyst) or (
                    isinstance(n, Link) and not n.isFree()):
                pass
            # moved the bonding of 3.32 and 3.34 here
            self.doBond()


class ProductionProcess(Process):

    def __init__(self, grid: Dict[Point, Element], hole_list: List[Hole],
                 substrate_list: List[Substrate],
                 catalyst_list: List[Catalyst], link_list: [List],
                 choose_strategy: ChooseStrategy,
                 logger: logging.Logger):
        super().__init__(grid, hole_list, substrate_list, catalyst_list,
                         link_list, choose_strategy, logger)

    def doStep(self):
        super().doStep()
        for catalyst in self.chooser.shuffleList(self.k_list):
            # !! Use only 1 S instead of 2 to avoid non-local effects during disintegration
            # K + S ->  K + L
            # 4.1
            if catalyst.hasNeighbourOfType(Substrate, self.grid):
                # execute action with some probability
                if self.chooser.chooseIntegrate():
                    # 4.2
                    self.produce(catalyst)
        # 4.3
        self.doBond()

    def produce(self, catalyst):
        s = self.chooser.chooseOne(
            catalyst.getNeighboursOfType(Substrate, self.grid))
        l = Link.createlink(s.point.x, s.point.y, s.getGridSize())
        self.logger.debug('{0} becomes {1}'.format(s, l))
        self.grid[l.point] = l
        self.l_list.append(l)
        self.s_list.remove(s)
        del s  # delete the substrate element


class DisintegrationProcess(Process):

    def __init__(self, grid: Dict[Point, Element], hole_list: List[Hole],
                 substrate_list: List[Substrate],
                 catalyst_list: List[Catalyst], link_list: [List],
                 choose_strategy: ChooseStrategy,
                 logger: logging.Logger):
        super().__init__(grid, hole_list, substrate_list, catalyst_list,
                         link_list, choose_strategy, logger)

    def doRebond(self, p: Point):
        element = self.grid[p]
        # 7.1 start with singly bonded Ls
        candidate_l_list = [typing.cast(Link, e) for e in
                            element.getNeighboursOfType(Link, self.grid) if
                            typing.cast(Link,
                                        e).isSinglyBonded()] if element.hasNeighbourOfType(
            Link,
            self.grid) else []
        free_l_list = [typing.cast(Link, e) for e in
                       element.getNeighboursOfType(Link, self.grid) if
                       typing.cast(Link,
                                   e).isFree()] if element.hasNeighbourOfType(
            Link, self.grid) else []

        used_links = []
        while candidate_l_list:
            for c in candidate_l_list:
                if c in used_links:
                    # if we ever reach a condition where a link is
                    # both used and available for use then likely
                    # __eq__ fails
                    assert False
            candidate_pairs: [(Link, Link)] = itertools.combinations(
                candidate_l_list, 2)
            valid_pairs: [(Link, Link)] = []
            for (c0, c1) in candidate_pairs:
                if not c0.isNeighbour(c1):
                    continue
                if c0 in c1.getAllBondedLinks():
                    continue
                if not self.checkBondAngle(c0, c1):
                    continue
                valid_pairs.append((c0, c1))
            # start forming bonds
            for (l0, l1) in self.chooser.shuffleList(valid_pairs):
                if not self.checkBondAngle(l0, l1):
                    continue
                if l0.canBond():
                    self.dobondTwo(l0, l1)
                    used_links.append(l0)
                    used_links.append(l1)
            # 7.4
            new_candidate_l_list = candidate_l_list.copy()
            if free_l_list:
                new_candidate_l_list.extend(free_l_list)
                free_l_list.clear()
            # 7.5
            new_candidate_l_list = [c for c in new_candidate_l_list if
                                    c not in used_links]
            # This is used to break the infinite loop when no more new candidates can be found
            if new_candidate_l_list == candidate_l_list:
                break
            candidate_l_list = new_candidate_l_list

    def doStep(self):
        super().doStep()
        for link in self.chooser.shuffleList(self.l_list):
            if self.chooser.chooseDisintegrate():
                self.logger.debug('{0} is disintegrating'.format(link))
                p = self.disintegrate(link)
                self.doRebond(p)

    def disintegrate(self, link):
        p = link.point
        bb = link.getAllBondedLinks().copy()
        for bonded in bb:
            # TODO: Revisit if I have to care about return type
            # probably not since bonded is guaranteed to be in link bonded list
            # and we assume that we formed bond correctly and put link in bonded_list of bonded
            link.removeBond(bonded)
        # disintegrate L to S
        new_s = Substrate.createsubstrate(p.x, p.y, link.getGridSize())
        self.grid[p] = new_s
        self.s_list.append(new_s)
        self.l_list.remove(
            link)  # ok to remove this since iterating through copy
        # destroy L
        del link
        return p


class CycleObserver(Process):

    def __init__(self, grid: Dict[Point, Element], hole_list: List[Hole],
                 substrate_list: List[Substrate], catalyst_list: List[Catalyst],
                 link_list: [List], choose_strategy: ChooseStrategy,
                 logger: logging.Logger):
        super().__init__(grid, hole_list, substrate_list, catalyst_list,
                         link_list, choose_strategy, logger)
        self.min_cycle_length = 4
        self.cycles = []
        self.born = {}
        self.cycle_size = {}

    def getCycleKey(self, cycle: [Link]) -> frozenset([Point]):
        # sort by distance from origin
        return frozenset(sorted([i.point for i in cycle], key=lambda p: math.sqrt((p.x) ** 2 + (p.y) ** 2)))

    def cycEq(self, cycle1: [Link], cycle2: [Link]) -> bool:
        return self.getCycleKey(cycle1) == self.getCycleKey(cycle2)

    @staticmethod
    def FindCycle(link: 'Link', visited: ['Link']) -> List['Link']:
        if link.isFree():
            return []
        if link.isSinglyBonded():
            return []
        if len(link.getAllBondedLinks()) == 2:
            if not link.getBondedLink(0) in visited:
                r = CycleObserver.FindCycle(link.getBondedLink(0), visited + [link])
            elif not link.getBondedLink(1) in visited:
                r = CycleObserver.FindCycle(link.getBondedLink(1), visited + [link])
            else:
                return [link]
            if not r:
                return []
            else:
                return [link] + r

    def doStep(self, exp: 'Experiment'):
        super().doStep()
        # process existing/bad cycles
        cycles_copy = [inner.copy() for inner in self.cycles.copy()]
        for cycle in cycles_copy:
            links = [e for e in [self.grid[p] for p in cycle] if isinstance(e, Link) and not typing.cast(Link,
                                                                                                         e).canBond()]
            if links:
                r = CycleObserver.FindCycle(links[0], [])
                if not r:
                    b = self.born[cycle]
                    d = exp.getTime()
                    l = self.cycle_size[cycle]
                    exp.addRecord(b, d, l)
                    self.cycles.remove(cycle)
                    del self.born[cycle]
                    del self.cycle_size[cycle]
                    self.logger.info('cycle broken:{0} len:{1} iter:{2}'.format(cycle, len(cycle), exp.getTime()))
                elif self.getCycleKey(r) != cycle and len(r) >= self.min_cycle_length and self.getCycleKey(r) not in \
                        self.cycles:
                    # cycle has mutated but is still a cycle
                    # Add new cycle
                    self.cycles.append(self.getCycleKey(r))
                    self.born[self.getCycleKey(r)] = self.born[cycle]
                    self.cycle_size[self.getCycleKey(r)] = len(r)

                    # delete old cycle
                    self.cycles.remove(cycle)
                    del self.born[cycle]
                    del self.cycle_size[cycle]
                    self.logger.info('Repaired cycle:{0} len:{1} iter:{2}'.format(r, len(r), exp.getTime()))
                elif self.getCycleKey(r) == cycle:
                    # nothing to do here
                    self.logger.info('Maintained cycle:{0} len:{1} iter:{2}'.format(r,
                                                                                    len(
                                                                                        r), exp.getTime()))
                else:  # cycle length < self.min_cycle_length
                    # delete old cycle
                    self.cycles.remove(cycle)
                    del self.born[cycle]
                    del self.cycle_size[cycle]
                    self.logger.info(
                        'cycle discarded:{0} len:{1} iter:{2}'.format(r, len(r), exp.getTime()))
            else:  # no links found
                b = self.born[cycle]
                d = exp.getTime()
                l = self.cycle_size[cycle]
                exp.addRecord(b, d, l)
                self.cycles.remove(cycle)
                del self.born[cycle]
                del self.cycle_size[cycle]
                self.logger.info('cycle broken:{0} len:{1} iter:{2}'.format(cycle, len(cycle), exp.getTime()))

        # process new cycles
        link_list = [l for l in self.l_list if
                     len(l.getAllBondedLinks()) == 2]
        for l in link_list:
            r = CycleObserver.FindCycle(l, [])
            if self.getCycleKey(r) in self.cycles:
                # we already recorded this link, goto next
                continue
            if len(r) >= self.min_cycle_length:
                self.logger.info('Found cycle:{0} len:{1} iter:{2}'.format(r, len(r), exp.getTime()))
                self.cycles.append(self.getCycleKey(r))
                self.born[self.getCycleKey(r)] = exp.getTime()
                self.cycle_size[self.getCycleKey(r)] = len(r)

class ChooseRandomStrategy(ChooseStrategy):

    def __init__(self, seed, disintegration_prob=DISINTEGRATE_PROB):
        self._rng = random.seed(seed)
        self._disint_prob = disintegration_prob

    def chooseDisintegrate(self) -> bool:
        return random.random() < self._disint_prob

    def chooseIntegrate(self) -> bool:
        return random.random() >= self._disint_prob

    def chooseOne(self, args: [T]) -> Optional[T]:
        if not args:
            return None
        return random.choice(args)

    def shuffleList(self, args: [T]) -> [T]:
        return random.sample(args, k=len(args))


class WorldFactory(object):

    def __init__(self, logging_level='WARNING'):
        self.logging_level = logging_level

    def createRandomGrid(self, grid_size: int, random_seed: int = 0, weights: [int] = [9, 90, 1]) -> Dict[Point, T]:
        # this grid will not have L starting out
        random.seed(random_seed)
        grid = {}
        element_list = random.choices([Hole, Substrate, Catalyst], weights=weights, \
                                      k=grid_size * grid_size)
        for i, e in enumerate(element_list):
            y: int = int(i / grid_size)
            x: int = i % grid_size
            element = e(Point(x, y), grid_size)
            grid[element.point] = element
        return grid

    def createGrid(self, hole_list: [Hole], substrate_list: [Substrate],
                   catalyst_list: [Catalyst], link_list: [Link],
                   default: typing.TypeVar(T), grid_size: int) -> Dict[
        Point, T]:
        grid = {}
        for j in range(grid_size):
            for i in range(grid_size):
                grid[Point(i, j)] = default(Point(i, j), grid_size)
        for e in itertools.chain(hole_list, substrate_list, catalyst_list,
                                 link_list):
            grid[e.point] = e
        return grid

    def getListsFromGrid(self, grid: Dict[Point, T]) -> (
            [Hole], [Substrate], [Catalyst], [Link]):
        h_list = []
        s_list = []
        k_list = []
        l_list = []
        for p in grid.keys():
            e = grid[p]
            if isinstance(e, Hole):
                h_list.append(e)
            elif isinstance(e, Substrate):
                s_list.append(e)
            elif isinstance(e, Catalyst):
                k_list.append(e)
            elif isinstance(e, Link):
                l_list.append(e)
        return h_list, s_list, k_list, l_list

    def createRandomWorld(self, grid_size, weights: [int], grid_random_seed: int, max_iter: int, proc_random_seed: int,
                          disintegrate_prob: float) -> 'WorldContext':
        grid = self.createRandomGrid(grid_size, grid_random_seed, weights=weights)
        hole_process, link_process, catalyst_process, \
        prod_process, disintegrate_process, cycle_observer \
            = self.createAllProcesses(grid, proc_random_seed, disintegrate_prob)
        return WorldContext(max_iter=max_iter, grid=grid, hole_process=hole_process, link_process=link_process,
                            catalyst_process=catalyst_process, production_process=prod_process,
                            disintegration_process=disintegrate_process, cycle_observer=cycle_observer)

    def createWorld(self, config: 'helper.Config'):
        grid = self.createGrid(config.h_plist,
                               config.s_plist,
                               config.k_plist,
                               config.l_plist,
                               config.default_element,
                               config.grid_size)
        hole_process, link_process, catalyst_process, \
        prod_process, disintegrate_process, cycle_observer \
            = self.createAllProcesses(grid, config.disintegrate_prob)
        return WorldContext(max_iter=config.iter, grid=grid, hole_process=hole_process, link_process=link_process,
                            catalyst_process=catalyst_process, production_process=prod_process,
                            disintegration_process=disintegrate_process, cycle_observer=cycle_observer)

    def createAllProcesses(self, grid, random_seed: int, disintegration_prob: float = DISINTEGRATE_PROB) -> (
            HoleProcess, LinkProcess, CatalystProcess, ProductionProcess,
            DisintegrationProcess):
        choose_strategy = ChooseRandomStrategy(seed=random_seed,
                                               disintegration_prob=
                                               disintegration_prob)
        logger = logging.getLogger('world')
        logger.setLevel(self.logging_level)
        (hh, ss, kk, ll) = self.getListsFromGrid(grid)
        hp = HoleProcess(grid, hh, ss, kk, ll, choose_strategy, logger)
        lp = LinkProcess(grid, hh, ss, kk, ll, choose_strategy, logger)
        kp = CatalystProcess(grid, hh, ss, kk, ll, choose_strategy, logger)
        pp = ProductionProcess(grid, hh, ss, kk, ll, choose_strategy, logger)
        dp = DisintegrationProcess(grid, hh, ss, kk, ll, choose_strategy,
                                   logger)
        co = CycleObserver(grid, hh, ss, kk, ll, choose_strategy, logger)
        return hp, lp, kp, pp, dp, co


class WorldContext(object):

    def __init__(self, max_iter: int, grid: Dict[Point, T], hole_process: HoleProcess, link_process: LinkProcess,
                 catalyst_process:
                 CatalystProcess, production_process: ProductionProcess, disintegration_process: DisintegrationProcess,
                 cycle_observer: CycleObserver):
        self.grid = grid
        self.cycle_observer = cycle_observer
        self.disintegration_process = disintegration_process
        self.production_process = production_process
        self.catalyst_process = catalyst_process
        self.link_process = link_process
        self.hole_process = hole_process
        self.max_iter = max_iter


class Experiment(object):

    def __init__(self):
        self._time = 0

    def incTime(self):
        self._time = self._time + 1

    def getTime(self):
        return self._time

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
