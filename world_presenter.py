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

"""Presentation logic + experiment execution logic.

"""
import itertools
import logging
import multiprocessing
import os
import pickle
import statistics
from typing import Dict

import helper
import world_model as world
import world_viewer as viewer

NUM_ITERATIONS = 1000

GRID_SIZE = 10

NUM_PROCESS = 20


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
        for i in range(self._iter):
            self._viewer.updateView(self._grid, i)
            self._doSingleStep()
            self.postProcess()
        self._viewer.updateView(self._grid, i + 1)


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
    jobs = []
    grid_seeds = range(0, 5)
    proc_seeds = range(100, 105)
    disint_prbs = [x / 100 for x in range(2, 12, 2)]
    # H S K
    weights_list = [[9 + int(i / 2), 90 - i, 1 + int(i / 2)] for i in range(0, 45, 5)]
    result = multiprocessing.Manager().dict()
    params_iter = [i for i in itertools.product(grid_seeds, proc_seeds, disint_prbs, weights_list)]
    jobs_per_proc = int(len(params_iter) / NUM_PROCESS)

    params_split_iter = grouper(params_iter, jobs_per_proc)

    for i, params in enumerate(params_split_iter):
        p = multiprocessing.Process(target=runSimulOnProcessor, args=(params, result, i))
        jobs.append(p)

    for job in jobs:
        job.start()
    for job in jobs:
        job.join()

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


def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue=fillvalue)


def runSimulOnProcessor(params, result, i):
    factory = world.WorldFactory()
    grid_size = GRID_SIZE
    iter = NUM_ITERATIONS
    view = viewer.NullViewer()
    print('Starting job:', i)
    # the iterator may iterate over None values so remove those
    params = [param for param in params if param is not None]
    for grid_seed, proc_seed, disint_prb, weights in params:
        exp = runSimulForParam(disint_prb, factory, grid_seed, grid_size, iter, proc_seed, view, weights)
        result[(grid_seed, proc_seed, disint_prb, tuple(weights))] = exp.process() if exp.process() else [[0, 0]]
    print('Stopping job:', i)


def runSimulForParam(disint_prb, factory, grid_seed, grid_size, iter, proc_seed, view, weights):
    exp = world.AliveDurationExperiment()
    ctx: world.WorldContext = factory.createRandomWorld(grid_size, weights, grid_random_seed=grid_seed,
                                                        max_iter=iter,
                                                        proc_random_seed=proc_seed,
                                                        disintegrate_prob=disint_prb)
    wp = ConsolePresenter(view, ctx, exp)
    wp.doSimulate()
    return exp


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
