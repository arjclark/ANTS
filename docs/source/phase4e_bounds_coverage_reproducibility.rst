Phase 4E: Bounds-Coverage Regrid Reproducibility Report
========================================================

Summary
-------

This report captures the decomposition reproducibility investigation outcomes
for binary regridding, including non-multiple resolution changes and split-sweep
validation.

Goal
----

The goal is to ensure decomposed regridding is reproducible across different
split configurations, i.e. results from decomposed execution match the
non-decomposed baseline.

What Was Tested
---------------

The test suite compares two source extraction methods while keeping the target
splitter fixed:

* ``standard``: existing ``ExtractConstraint(..., pad_width=1)`` extraction
* ``bounds_coverage``: source extraction using coordinate bounds coverage,
  with coarseness-aware neighbor inclusion and circular-longitude preservation

For each scenario, tests run:

1. A baseline non-decomposed regrid (reference result)
2. Decomposed regrids with ``standard`` extraction
3. Decomposed regrids with ``bounds_coverage`` extraction
4. A split sweep across ``(2,2)``, ``(4,1)``, ``(1,4)``, and ``(4,2)``

The primary metric shown below is maximum absolute error versus baseline.

Key Findings
------------

* Equal-resolution regrids are reproducible with both methods.
* For all tested downsample, upsample, non-uniform, and non-multiple scenarios,
  ``bounds_coverage`` reduced max error to zero across all tested splits.
* The ``standard`` method remained split-sensitive in terms of reproducibility
  (non-zero error magnitude), while ``bounds_coverage`` remained reproducible
  across the same split sweep.

Limitations Identified During Investigation
-------------------------------------------

* Pad-width tuning alone did not provide robust reproducibility: index padding
  does not guarantee equivalent interpolation neighborhoods to full-domain runs.
* Alternative target splitting strategies did not materially improve
  reproducibility: target chunk geometry was not the dominant cause.
* The dominant cause was source-context mismatch at decomposition boundaries.
* An early upsample issue with bounds coverage was traced to loss of circular
  behavior when slicing longitude; preserving full circular longitude extent
  resolved this.

Results Table (Max Absolute Error vs Baseline)
----------------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 34 10 18 18

   * - Scenario
     - Split
     - Standard (pad=1)
     - Bounds coverage
   * - 16x16 -> 16x16 (equal)
     - (2,2)
     - 0.00e+00
     - 0.00e+00
   * - 16x16 -> 16x16 (equal)
     - (4,1)
     - 0.00e+00
     - 0.00e+00
   * - 16x16 -> 16x16 (equal)
     - (1,4)
     - 0.00e+00
     - 0.00e+00
   * - 16x16 -> 16x16 (equal)
     - (4,2)
     - 0.00e+00
     - 0.00e+00
   * - 16x16 -> 8x8 (2x downsample)
     - (2,2)
     - 5.00e-01
     - 0.00e+00
   * - 16x16 -> 8x8 (2x downsample)
     - (4,1)
     - 5.00e-01
     - 0.00e+00
   * - 16x16 -> 8x8 (2x downsample)
     - (1,4)
     - 5.00e-01
     - 0.00e+00
   * - 16x16 -> 8x8 (2x downsample)
     - (4,2)
     - 5.00e-01
     - 0.00e+00
   * - 16x16 -> 12x12 (non-uniform)
     - (2,2)
     - 8.33e-01
     - 0.00e+00
   * - 16x16 -> 12x12 (non-uniform)
     - (4,1)
     - 8.33e-01
     - 0.00e+00
   * - 16x16 -> 12x12 (non-uniform)
     - (1,4)
     - 8.33e-01
     - 0.00e+00
   * - 16x16 -> 12x12 (non-uniform)
     - (4,2)
     - 8.33e-01
     - 0.00e+00
   * - 8x8 -> 16x16 (2x upsample)
     - (2,2)
     - 7.50e-01
     - 0.00e+00
   * - 8x8 -> 16x16 (2x upsample)
     - (4,1)
     - 7.50e-01
     - 0.00e+00
   * - 8x8 -> 16x16 (2x upsample)
     - (1,4)
     - 7.50e-01
     - 0.00e+00
   * - 8x8 -> 16x16 (2x upsample)
     - (4,2)
     - 7.50e-01
     - 0.00e+00
   * - 16x16 -> 14x14 (non-multiple)
     - (2,2)
     - 9.29e-01
     - 0.00e+00
   * - 16x16 -> 14x14 (non-multiple)
     - (4,1)
     - 9.29e-01
     - 0.00e+00
   * - 16x16 -> 14x14 (non-multiple)
     - (1,4)
     - 9.29e-01
     - 0.00e+00
   * - 16x16 -> 14x14 (non-multiple)
     - (4,2)
     - 9.29e-01
     - 0.00e+00
   * - 14x14 -> 18x18 (non-multiple)
     - (2,2)
     - 1.00e+00
     - 0.00e+00
   * - 14x14 -> 18x18 (non-multiple)
     - (4,1)
     - 1.00e+00
     - 0.00e+00
   * - 14x14 -> 18x18 (non-multiple)
     - (1,4)
     - 1.00e+00
     - 0.00e+00
   * - 14x14 -> 18x18 (non-multiple)
     - (4,2)
     - 1.00e+00
     - 0.00e+00

Conclusion
----------

The bounds-based source extraction method is currently the best-performing
approach tested for reproducible decomposed regridding across varying
split configurations. It directly addresses the identified source-context
boundary mismatch and remains robust across both multiple and non-multiple
resolution transformations.
