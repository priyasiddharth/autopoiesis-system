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
