# (C) Crown Copyright, Met Office. All rights reserved.
#
# This file is part of ANTS and is released under the BSD 3-Clause license.
# See LICENSE.txt in the root of the repository for full licensing details.
"""Bounds-coverage regrid equivalence validation suite.

This module validates that decomposed regridding using bounds-coverage source
extraction produces results equivalent to non-decomposed baseline execution
across a range of resolution scenarios and split configurations.

Tests verify that the bounds-coverage extraction method successfully eliminates
split-boundary divergence for various regrid operations.
"""

import copy
import os
import unittest.mock as mock

import ants.config
import ants.decomposition as decomp
import ants.tests
import numpy as np
from iris.analysis import Linear


def compute_divergence_metrics(decomposed_cube, baseline_cube):
    """Compute divergence metrics between decomposed and baseline cubes.

    Args:
        decomposed_cube: Result from decomposed regrid operation
        baseline_cube: Result from non-decomposed baseline regrid

    Returns:
        dict: Metrics including max_abs_error, mean_abs_error, std_abs_error,
              mask_mismatch_count, mask_mismatch_ratio, and coords_match
    """
    metrics = {}

    data_diff = np.abs(decomposed_cube.data - baseline_cube.data)
    metrics["max_abs_error"] = float(np.max(data_diff))
    metrics["mean_abs_error"] = float(np.mean(data_diff))
    metrics["std_abs_error"] = float(np.std(data_diff))

    decomposed_mask = np.ma.getmaskarray(decomposed_cube.data)
    baseline_mask = np.ma.getmaskarray(baseline_cube.data)
    mask_mismatch = np.sum(decomposed_mask != baseline_mask)
    metrics["mask_mismatch_count"] = int(mask_mismatch)
    metrics["mask_mismatch_ratio"] = float(
        mask_mismatch / decomposed_mask.size if decomposed_mask.size > 0 else 0
    )

    coords_match = True
    for d_coord, b_coord in zip(
        decomposed_cube.coords(dim_coords=True), baseline_cube.coords(dim_coords=True)
    ):
        points_diff = np.max(np.abs(d_coord.points - b_coord.points))
        if points_diff > 1e-10:
            coords_match = False
            metrics[f"coord_{d_coord.name()}_max_points_diff"] = float(points_diff)
    metrics["coords_match"] = coords_match

    return metrics


class TestBoundsCoverageRegridEquivalence(ants.tests.TestCase):
    """Validate that bounds-coverage decomposed regridding equals non-decomposed baseline.

    This test class ensures that the bounds-coverage source extraction method
    produces regrid results that match non-decomposed execution across multiple
    split configurations and resolution scenarios.
    """

    def setUp(self):
        """Configure a deterministic single-process decomposition test environment."""
        self._original_environment = os.environ.copy()
        os.environ.pop("SLURM_NTASKS", None)
        os.environ.pop("PBS_NP", None)
        os.environ.pop("LSB_DJOB_NUMPROC", None)
        os.environ["ANTS_NPROCESSES"] = "1"
        os.environ["ANTS_DECOMPOSITION_SOURCE_EXTRACTOR"] = "bounds_coverage"

        new_config = copy.copy(ants.config.GlobalConfiguration())
        new_config.__init__()
        patch = mock.patch("ants.decomposition.CONFIG", new=new_config)
        self.mock_config = patch.start()
        self.addCleanup(patch.stop)

    def tearDown(self):
        """Restore environment and configuration."""
        os.environ = self._original_environment

    def _run_regrid_baseline(self, source, target):
        """Run non-decomposed baseline regrid used as equivalence reference.

        Args:
            source: Source cube
            target: Target cube

        Returns:
            Regridded cube without decomposition
        """
        self.mock_config["ants_decomposition"]["x_split"] = 0
        self.mock_config["ants_decomposition"]["y_split"] = 0

        def regrid_op(src, tgt):
            return src.regrid(tgt, Linear())

        return decomp.decompose(regrid_op, source, target)

    def _run_regrid_decomposed(self, source, target, split):
        """Run decomposed regrid with bounds-coverage extraction.

        Args:
            source: Source cube
            target: Target cube
            split: Tuple (x_split, y_split) specifying target decomposition

        Returns:
            Regridded cube with decomposition and bounds-coverage extraction
        """
        self.mock_config["ants_decomposition"]["x_split"] = split[0]
        self.mock_config["ants_decomposition"]["y_split"] = split[1]
        self.mock_config["ants_decomposition"]["pad_width"] = 1

        def regrid_op(src, tgt):
            return src.regrid(tgt, Linear())

        return decomp.decompose(regrid_op, source, target)

    def _split_configs(self):
        """Return split configurations to test decomposition robustness.

        Returns:
            List of (x_split, y_split) tuples for test sweep
        """
        return [(2, 2), (4, 1), (1, 4), (4, 2)]

    def test_equal_resolution_equivalence(self):
        """Equal resolution: decomposed should match baseline across all splits.

        Validates that decomposed regridding produces identical results to
        non-decomposed baseline when source and target have same resolution.
        """
        source = ants.tests.stock.geodetic((16, 16), name="source")
        target = ants.tests.stock.geodetic((16, 16), name="target")

        baseline = self._run_regrid_baseline(source, target)

        for split in self._split_configs():
            with self.subTest(split=split):
                decomposed = self._run_regrid_decomposed(source, target, split)
                metrics = compute_divergence_metrics(decomposed, baseline)

                self.assertLess(
                    metrics["max_abs_error"],
                    1e-10,
                    msg=f"split={split}: decomposed regrid diverged from baseline",
                )
                self.assertTrue(
                    metrics["coords_match"],
                    msg=f"split={split}: coordinates do not match baseline",
                )
                self.assertEqual(
                    metrics["mask_mismatch_count"],
                    0,
                    msg=f"split={split}: mask mismatch with baseline",
                )

    def test_downsample_2x_equivalence(self):
        """2x downsample: decomposed should match baseline across all splits.

        Validates that bounds-coverage extraction successfully eliminates
        split-boundary divergence for uniform downsampling.
        """
        source = ants.tests.stock.geodetic((16, 16), name="source")
        target = ants.tests.stock.geodetic((8, 8), name="target")

        baseline = self._run_regrid_baseline(source, target)

        for split in self._split_configs():
            with self.subTest(split=split):
                decomposed = self._run_regrid_decomposed(source, target, split)
                metrics = compute_divergence_metrics(decomposed, baseline)

                self.assertLess(
                    metrics["max_abs_error"],
                    1e-10,
                    msg=f"split={split}: bounds-coverage should eliminate divergence",
                )
                self.assertTrue(
                    metrics["coords_match"],
                    msg=f"split={split}: coordinates do not match baseline",
                )
                self.assertEqual(
                    metrics["mask_mismatch_count"],
                    0,
                    msg=f"split={split}: mask mismatch with baseline",
                )

    def test_nonuniform_downsample_equivalence(self):
        """Non-uniform downsample (16->12): decomposed should match baseline.

        Validates equivalence for irregular downsampling ratios.
        """
        source = ants.tests.stock.geodetic((16, 16), name="source")
        target = ants.tests.stock.geodetic((12, 12), name="target")

        baseline = self._run_regrid_baseline(source, target)

        for split in self._split_configs():
            with self.subTest(split=split):
                decomposed = self._run_regrid_decomposed(source, target, split)
                metrics = compute_divergence_metrics(decomposed, baseline)

                self.assertLess(
                    metrics["max_abs_error"],
                    1e-10,
                    msg=f"split={split}: bounds-coverage should eliminate divergence",
                )
                self.assertTrue(
                    metrics["coords_match"],
                    msg=f"split={split}: coordinates do not match baseline",
                )
                self.assertEqual(
                    metrics["mask_mismatch_count"],
                    0,
                    msg=f"split={split}: mask mismatch with baseline",
                )

    def test_upsample_2x_equivalence(self):
        """2x upsample: decomposed should match baseline across all splits.

        Validates that coarseness-aware bounds extraction handles upsample
        operations and maintains circular coordinate wrap-around correctly.
        """
        source = ants.tests.stock.geodetic((8, 8), name="source")
        target = ants.tests.stock.geodetic((16, 16), name="target")

        baseline = self._run_regrid_baseline(source, target)

        for split in self._split_configs():
            with self.subTest(split=split):
                decomposed = self._run_regrid_decomposed(source, target, split)
                metrics = compute_divergence_metrics(decomposed, baseline)

                self.assertLess(
                    metrics["max_abs_error"],
                    1e-10,
                    msg=f"split={split}: bounds-coverage should eliminate divergence",
                )
                self.assertTrue(
                    metrics["coords_match"],
                    msg=f"split={split}: coordinates do not match baseline",
                )
                self.assertEqual(
                    metrics["mask_mismatch_count"],
                    0,
                    msg=f"split={split}: mask mismatch with baseline",
                )

    def test_nonmultiple_downsample_equivalence(self):
        """Non-multiple downsample (16->14): decomposed should match baseline.

        Validates equivalence for non-factorizable downsampling ratios.
        """
        source = ants.tests.stock.geodetic((16, 16), name="source")
        target = ants.tests.stock.geodetic((14, 14), name="target")

        baseline = self._run_regrid_baseline(source, target)

        for split in self._split_configs():
            with self.subTest(split=split):
                decomposed = self._run_regrid_decomposed(source, target, split)
                metrics = compute_divergence_metrics(decomposed, baseline)

                self.assertLess(
                    metrics["max_abs_error"],
                    1e-10,
                    msg=f"split={split}: bounds-coverage should eliminate divergence",
                )
                self.assertTrue(
                    metrics["coords_match"],
                    msg=f"split={split}: coordinates do not match baseline",
                )
                self.assertEqual(
                    metrics["mask_mismatch_count"],
                    0,
                    msg=f"split={split}: mask mismatch with baseline",
                )

    def test_nonmultiple_upsample_equivalence(self):
        """Non-multiple upsample (14->18): decomposed should match baseline.

        Validates equivalence for non-factorizable upsampling ratios and
        circular coordinate handling with coarseness-aware extraction.
        """
        source = ants.tests.stock.geodetic((14, 14), name="source")
        target = ants.tests.stock.geodetic((18, 18), name="target")

        baseline = self._run_regrid_baseline(source, target)

        for split in self._split_configs():
            with self.subTest(split=split):
                decomposed = self._run_regrid_decomposed(source, target, split)
                metrics = compute_divergence_metrics(decomposed, baseline)

                self.assertLess(
                    metrics["max_abs_error"],
                    1e-10,
                    msg=f"split={split}: bounds-coverage should eliminate divergence",
                )
                self.assertTrue(
                    metrics["coords_match"],
                    msg=f"split={split}: coordinates do not match baseline",
                )
                self.assertEqual(
                    metrics["mask_mismatch_count"],
                    0,
                    msg=f"split={split}: mask mismatch with baseline",
                )
