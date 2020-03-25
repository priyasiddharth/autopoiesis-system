import itertools
import logging
import os
import pickle
import statistics
from typing import Dict

import helper
import world_model as world
import world_viewer as viewer


class WorldPresenter(object):

    def __init__(self, viewer: viewer.WorldViewer, context: world.WorldContext):
        self._ctx = context
        self._viewer = viewer
        self._iter = 0
        self._hole_process: world.HoleProcess = self._ctx.hole_process
        self._link_process: world.LinkProcess = self._ctx.link_process
        self._catalyst_process: world.CatalystProcess = self._ctx.catalyst_process
        self._prod_process: world.ProductionProcess = self._ctx.production_process
        self._disintegrate_process: world.DisintegrationProcess = self._ctx.disintegration_process
        self._cycle_observer: world.CycleObserver = self._ctx.cycle_observer
        self._grid: Dict[world.Point: world.T] = self._ctx.grid
        self._iter: int = self._ctx.max_iter

    def _doSingleStep(self):
        self._hole_process.doStep()
        self._link_process.doStep()
        self._catalyst_process.doStep()
        self._prod_process.doStep()
        self._disintegrate_process.doStep()

    def postProcess(self):
        pass

    def doSimulate(self):
        self._viewer.updateView(self._grid, iteration=0)
        for i in range(self._iter):
            self._doSingleStep()
            self._viewer.updateView(self._grid, i)
            self.postProcess()


class ConsolePresenter(WorldPresenter):

    def __init__(self, viewer: viewer.ConsoleViewer, config: helper.Config,
                 exp: world.Experiment
                 ) -> None:
        super().__init__(viewer, config)
        self._experiment = exp

    def postProcess(self):
        self._cycle_observer.doStep(self._experiment)
        self._experiment.incTime()


def batch_run():
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "WARNING"))
    grid_size = 10
    iter = 100
    view = viewer.NullViewer()
    grid_seeds = range(0, 5)
    proc_seeds = range(100, 105)
    disint_prbs = [x / 100 for x in range(2, 12, 2)]
    # H S K
    # weights_list = [[9 + int(i/2), 90 - i, 1 + int(i/2)] for i in range(0, 45, 5)]
    weights_list = [[9, 90, 1]]
    result = {}
    factory = world.WorldFactory()
    for grid_seed, proc_seed, disint_prb, weights in itertools.product(grid_seeds, proc_seeds, disint_prbs,
                                                                       weights_list):
        exp = world.AliveDurationExperiment()
        ctx: world.WorldContext = factory.createRandomWorld(grid_size, weights, grid_random_seed=grid_seed,
                                                            max_iter=iter,
                                                            proc_random_seed=proc_seed,
                                                            disintegrate_prob=disint_prb)
        wp = ConsolePresenter(view, ctx, exp)
        wp.doSimulate()
        result[(grid_seed, proc_seed, disint_prb, tuple(weights))] = exp.process() if exp.process() else [[0, 0]]

    result_dict = {}
    display_dict = {}
    for prob, weights in itertools.product(disint_prbs, weights_list):
        alive_stats = []
        size_stats = []
        for grid_seed, proc_seed in itertools.product(grid_seeds, proc_seeds):
            alive_stats.extend([i[0] for i in result[grid_seed, proc_seed, prob, tuple(weights)]])
            size_stats.extend([i[1] for i in result[grid_seed, proc_seed, prob, tuple(weights)]])
        result_dict[prob, tuple(weights)] = (alive_stats, size_stats)
        display_dict[prob, tuple(weights)] = ((alive_stats), statistics.mean(size_stats))
    print(display_dict)
    with open('outputfile', 'wb') as fout:
        pickle.dump(result_dict, fout)

def main():
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))
    path = 'config.json'
    view = viewer.ConsoleViewer()
    exp = world.AliveDurationExperiment()
    config: helper.Config = helper.Config.loadConfigFromFile(path)
    presenter = ConsolePresenter(view, config, exp)
    presenter.doSimulate()
    print(exp.alive_durations)
    print(exp.process())


if __name__ == '__main__':
    batch_run()
