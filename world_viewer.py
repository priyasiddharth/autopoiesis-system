"""
Copyright 2020 Siddharth Priya

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import world_model as world


class WorldViewer(object):

    def __init__(self):
        pass

    def updateView(self, grid: [world.Point, world.T], iteration: int):
        pass


class ConsoleViewer(WorldViewer):

    def updateView(self, grid: [world.Point, world.T], iteration):
        print('iter:{0}'.format(iteration))
        print(world.GridPrettyPrintHelper(grid))

    def __init__(self):
        pass


class NullViewer(WorldViewer):

    def __init__(self):
        super().__init__()

    def updateView(self, grid: [world.Point, world.T], iteration: int):
        pass
