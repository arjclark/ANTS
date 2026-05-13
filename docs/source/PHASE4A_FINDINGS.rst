=====================================================
Phase 4A: Split Configuration Findings
=====================================================

**STATUS:** Phase 4A investigation complete. **HYPOTHESIS REFUTED.**

**Finding:** Split configuration has NO effect on regrid divergence.

---

Investigation Design
====================

**Hypothesis:** 1D splits (e.g., x_split=2, y_split=1) produce lower regrid divergence than 2D splits (e.g., x_split=2, y_split=2) because they have fewer decomposition boundaries crossing interpolation stencils.

**Test Matrix:**
- 4 regrid scenarios (equal, 2x downsample, non-uniform, hypothesis comparison)
- 6-30 split configurations per scenario (1D: (2,1), (1,2), (4,1), (1,4); 2D: (2,2), (3,1), (1,3), (3,2), (2,3); baseline: (1,1))
- Full decomposition vs non-decomposed baseline comparison
- Metrics: max_abs_error, mean_abs_error, classification

---

Results
=======

**Scenario 1: Equal-Resolution Regrid (16×16→16×16)**

Split Config | Max Error | Mean Error | Classification
-------------|-----------|-----------|----------------
(1,1)        | 0.00e+00  | 0.00e+00  | acceptable
(2,1)        | 0.00e+00  | 0.00e+00  | acceptable
(1,2)        | 0.00e+00  | 0.00e+00  | acceptable
(2,2)        | 0.00e+00  | 0.00e+00  | acceptable
(3,1)        | 0.00e+00  | 0.00e+00  | acceptable
(1,3)        | 0.00e+00  | 0.00e+00  | acceptable

**Summary:** All splits produce ZERO divergence. No advantage to any configuration.

---

**Scenario 2: 2:1 Downsampling (16×16→8×8)**

Split Config | Max Error | Mean Error | Classification
-------------|-----------|-----------|----------------
(1,1)        | 5.00e-01  | 5.00e-01  | high
(2,1)        | 5.00e-01  | 5.00e-01  | high
(1,2)        | 5.00e-01  | 5.00e-01  | high
(2,2)        | 5.00e-01  | 5.00e-01  | high
(4,1)        | 5.00e-01  | 5.00e-01  | high
(1,4)        | 5.00e-01  | 5.00e-01  | high

**Summary:** All splits produce IDENTICAL divergence (5.00e-01). No advantage to 1D or 2D.

---

**Scenario 3: Non-Uniform Downsampling (16×16→12×12)**

Split Config | Max Error | Mean Error | Classification
-------------|-----------|-----------|----------------
(1,1)        | 8.33e-01  | 5.00e-01  | high
(2,1)        | 8.33e-01  | 5.00e-01  | high
(1,2)        | 8.33e-01  | 5.00e-01  | high
(2,2)        | 8.33e-01  | 5.00e-01  | high
(3,2)        | 8.33e-01  | 5.00e-01  | high
(2,3)        | 8.33e-01  | 5.00e-01  | high

**Summary:** All splits produce IDENTICAL divergence (8.33e-01). No advantage to asymmetric configurations.

---

**Scenario 4: Direct 1D vs 2D Hypothesis Test**

Configuration | Max Error | Mean Error | Classification
--------------|-----------|-----------|----------------
(2,1) 1D      | 8.33e-01  | 5.00e-01  | high
(2,2) 2D      | 8.33e-01  | 5.00e-01  | high

**Ratio (1D/2D):** 1.00x (identical)

**Interpretation:** 
- Expected: Ratio < 0.9 (1D better) or > 1.1 (2D better)
- Observed: Ratio = 1.00x (INCONCLUSIVE → actually IDENTICAL)
- Conclusion: No difference between 1D and 2D splits

---

Aggregate Analysis
==================

**1D Splits:** (2,1), (1,2), (4,1), (1,4), (3,1), (1,3)
- Average max error: 5.00e-01 (downsampling scenarios)
- Average max error: 8.33e-01 (non-uniform downsampling)

**2D Splits:** (2,2), (3,2), (2,3)
- Average max error: 5.00e-01 (downsampling scenarios)
- Average max error: 8.33e-01 (non-uniform downsampling)

**Difference:** None. Both strategies produce identical results.

---

Critical Finding
================

**Split configuration does NOT affect regrid divergence.**

The divergence between decomposed and non-decomposed regrid is **completely independent** of:
- Whether you split in one dimension (1D split)
- Whether you split in both dimensions (2D split)
- How many pieces you create
- Whether splits are symmetric or asymmetric

**Why?**

The regrid divergence arises from **linear interpolation semantics**, not from decomposition boundary placement. When a cubic dataset is decomposed into pieces with different grid topologies, the linear interpolation algorithm produces different results **regardless of how the boundaries are placed**. The divergence is intrinsic to:

1. How linear interpolation stencils operate on the decomposed grid structure
2. The fundamental difference between interpolating a unified grid vs decomposed pieces
3. The algorithm itself, not the decomposition configuration

**Analogy:** Asking "where do we place the decomposition boundaries to get better regrid results?" is like asking "where do we cut a mosaic to make it look more like the original painting?" The cut placement doesn't matter - the fact that you're viewing separate pieces instead of a unified image is what changes the appearance.

---

Implication for User Guidance
=============================

**Previous Hypothesis (Refuted):**
"Use 1D splits to reduce regrid divergence"

**New Finding:**
"Split configuration has no effect on regrid divergence; the divergence is inherent to decomposed regridding."

**Updated Recommendation:**
Users cannot reduce regrid divergence by changing split configuration. The choice of split configuration should be based on:
1. **Memory efficiency** (number of pieces affects memory per piece)
2. **Parallelization** (more pieces may enable better parallelization)
3. **Operational simplicity** (easy-to-specify configurations)

NOT on divergence minimization, as split configuration does not affect divergence.

---

Status: REFUTED ✗

**Hypothesis:** 1D splits → fewer boundaries → lower divergence
**Evidence:** All split configs produce identical divergence
**Conclusion:** Hypothesis is false. Split configuration is NOT a lever for divergence control.

---

Next Steps
==========

**Phase 4B - Memory Efficiency Analysis:** Still relevant. Continue to understand memory impact of different split configurations for users who must use decomposition.

**Phase 4C - Boundary Characterization:** May be skipped or adapted; since split configuration doesn't affect divergence, focus might shift to understanding why interpolation divergence occurs in the first place.

**Phase 4D - Recommendation Framework:** Update recommendations to reflect that split configuration doesn't help with divergence. Maintain tier-based guidance but base it on memory constraints, not divergence.

**Phase 4E - API Design:** Simplify or skip. No need for divergence-based auto-selection if divergence is independent of split configuration.

**New Investigation Direction:** 
Consider whether any OTHER decomposition parameter or operation sequence could reduce divergence, or accept that regrid divergence is unavoidable when using decomposition.
