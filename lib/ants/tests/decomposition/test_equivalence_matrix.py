# (C) Crown Copyright, Met Office. All rights reserved.
#
# This file is part of ANTS and is released under the BSD 3-Clause license.
# See LICENSE.txt in the root of the repository for full licensing details.
"""Equivalence checks between decomposed and non-decomposed execution.

These tests enforce the documented requirement that operations intended for
`ants.decomposition.decompose` must produce consistent outputs with and without
decomposition.
"""

import copy
import os
import unittest.mock as mock

import ants.config
import ants.decomposition as decomp
import ants.tests
import numpy as np
import pytest
from iris.analysis import Linear


def unary_add_one(source):
    return source + 1


def binary_passthrough_target(source, target):
    del source
    return target.copy()


def binary_regrid_linear(source, target):
    return source.regrid(target, Linear())


class TestDecompositionEquivalenceMatrix(ants.tests.TestCase):
    def setUp(self):
        self._original_environment = os.environ.copy()
        os.environ.pop("SLURM_NTASKS", None)
        os.environ.pop("PBS_NP", None)
        os.environ.pop("LSB_DJOB_NUMPROC", None)
        os.environ["ANTS_NPROCESSES"] = "1"

        # Use an isolated configuration object so tests are independent of
        # external config files.
        new_config = copy.copy(ants.config.GlobalConfiguration())
        new_config.__init__()
        patch = mock.patch("ants.decomposition.CONFIG", new=new_config)
        self.mock_config = patch.start()
        self.addCleanup(patch.stop)
        self.mock_config["ants_decomposition"]["pad_width"] = 0

    def tearDown(self):
        os.environ = self._original_environment

    def _run_with_split(self, operation, source, target, split, processes=1):
        x_split, y_split = split
        os.environ["ANTS_NPROCESSES"] = str(processes)
        self.mock_config["ants_decomposition"]["x_split"] = x_split
        self.mock_config["ants_decomposition"]["y_split"] = y_split

        if split == ("automatic", "automatic"):
            split_guess = {"split_x": 2, "split_y": 2}
            with mock.patch("ants.decomposition._guess_split", return_value=split_guess):
                return decomp.decompose(operation, source, target)

        return decomp.decompose(operation, source, target)

    def _assert_cube_equivalent(self, actual, expected):
        self.assertEqual(actual.metadata, expected.metadata)
        self.assertArrayAlmostEqual(actual.data, expected.data, decimal=6)

        actual_mask = np.ma.getmaskarray(actual.data)
        expected_mask = np.ma.getmaskarray(expected.data)
        self.assertArrayEqual(actual_mask, expected_mask)

        actual_dim_coords = actual.coords(dim_coords=True)
        expected_dim_coords = expected.coords(dim_coords=True)
        self.assertEqual(len(actual_dim_coords), len(expected_dim_coords))

        for act_coord, exp_coord in zip(actual_dim_coords, expected_dim_coords):
            self.assertEqual(act_coord.metadata, exp_coord.metadata)
            self.assertArrayAlmostEqual(act_coord.points, exp_coord.points, decimal=10)
            if act_coord.bounds is None or exp_coord.bounds is None:
                self.assertIs(act_coord.bounds, exp_coord.bounds)
            else:
                self.assertArrayAlmostEqual(act_coord.bounds, exp_coord.bounds, decimal=10)

    def test_unary_equivalent_across_split_modes(self):
        source = ants.tests.stock.geodetic((12, 12), name="source")

        baseline = self._run_with_split(unary_add_one, source, None, (0, 0))
        split_modes = [(1, 1), (2, 2), ("automatic", "automatic")]

        for split in split_modes:
            with self.subTest(split=split):
                result = self._run_with_split(unary_add_one, source, None, split)
                self._assert_cube_equivalent(result, baseline)

    def test_binary_equivalent_across_split_modes(self):
        source = ants.tests.stock.geodetic((16, 16), name="source")
        target = ants.tests.stock.geodetic((16, 16), name="target")
        target.data = target.data * 2

        baseline = self._run_with_split(
            binary_passthrough_target, source, target, (0, 0)
        )
        split_modes = [(1, 1), (2, 2), ("automatic", "automatic")]

        for split in split_modes:
            with self.subTest(split=split):
                result = self._run_with_split(
                    binary_passthrough_target, source, target, split
                )
                self._assert_cube_equivalent(result, baseline)

    def test_unary_equivalent_single_vs_multi_process(self):
        source = ants.tests.stock.geodetic((12, 12), name="source")

        single_process = self._run_with_split(unary_add_one, source, None, (2, 2), 1)
        multi_process = self._run_with_split(unary_add_one, source, None, (2, 2), 2)
        self._assert_cube_equivalent(multi_process, single_process)

    def test_binary_equivalent_single_vs_multi_process(self):
        source = ants.tests.stock.geodetic((16, 16), name="source")
        target = ants.tests.stock.geodetic((16, 16), name="target")
        target.data = target.data * 2

        single_process = self._run_with_split(
            binary_passthrough_target, source, target, (2, 2), 1
        )
        multi_process = self._run_with_split(
            binary_passthrough_target, source, target, (2, 2), 2
        )
        self._assert_cube_equivalent(multi_process, single_process)

    @pytest.mark.xfail(
        reason=(
            "Known unsafe case: piecewise linear regrid may not preserve "
            "non-decomposed values across split boundaries."
        ),
        strict=False,
    )
    def test_binary_regrid_not_equivalent_across_split_modes(self):
        source = ants.tests.stock.geodetic((16, 16), name="source")
        target = ants.tests.stock.geodetic((12, 12), name="target")

        baseline = self._run_with_split(binary_regrid_linear, source, target, (0, 0))
        decomposed = self._run_with_split(binary_regrid_linear, source, target, (2, 2))
        self._assert_cube_equivalent(decomposed, baseline)

    @pytest.mark.xfail(
        reason=(
            "Known risk matrix: regrid decomposition can diverge with varying "
            "split and pad settings."
        ),
        strict=False,
    )
    def test_binary_regrid_risk_matrix(self):
        source = ants.tests.stock.geodetic((16, 16), name="source")
        target = ants.tests.stock.geodetic((12, 12), name="target")

        baseline = self._run_with_split(binary_regrid_linear, source, target, (0, 0))
        scenarios = [
            ((1, 1), 0, 1),
            ((2, 2), 0, 1),
            ((2, 2), 1, 1),
            (("automatic", "automatic"), 1, 1),
            ((2, 2), 1, 2),
            (("automatic", "automatic"), 1, 2),
        ]

        for split, pad_width, processes in scenarios:
            with self.subTest(split=split, pad_width=pad_width, processes=processes):
                self.mock_config["ants_decomposition"]["pad_width"] = pad_width
                decomposed = self._run_with_split(
                    binary_regrid_linear, source, target, split, processes
                )
                self._assert_cube_equivalent(decomposed, baseline)
