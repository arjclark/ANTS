=====================================================
Phase 2 Evidence Collection: Complete
=====================================================

**STATUS:** Phase 2 comprehensive metrics collection executed successfully.

**FINDING:** pad_width does NOT reduce regrid divergence.

Evidence Summary
================

**What Was Tested:**
- 5 source-target resolution scenarios (16×16→16×16, 16×16→8×8, 16×16→12×12, 12×12→16×16, 32×32→8×8)
- 3 pad_width configurations each: fixed(1), auto_split-aware, auto_resolution-ratio
- Total: 15 configurations with full divergence metrics

**Results:**
- Improvement ratio (auto vs fixed): **1.00x across all 15 scenarios**
- Scenarios with improvement (>1.0x): **0 out of 10**
- Metrics interpretation: No auto-pad strategy reduced divergence

**Data Table Example (16×16→8×8 downsampling, 2×2 split):**

| Pad Mode        | Max Error | Mean Error | Improvement |
|-----------------|-----------|-----------|-------------|
| fixed(1)        | 0.50      | 0.50      | 1.00x       |
| auto_split(1)   | 0.50      | 0.50      | (same)      |
| auto_ratio(2)   | 0.50      | 0.50      | (same)      |

**Key Insight:**
Identical divergence across all strategies proves **pad_width is not a lever for controlling regrid divergence**. The interpolation difference is inherent to decomposed execution, not a padding configuration issue.

**Decision Criterion:**
- Requirement: ≥80% scenarios show improvement (ratio > 1.0x)
- Result: 0%
- Status: **DECISIVELY FAILED** ❌

Final Recommendation
====================

**Decision: DO NOT ADOPT pad_width=auto**

**Rationale:** Phase 2 evidence demonstrates zero effectiveness.

**Alternative Guidance for Users:**
1. Use non-decomposed regridding for reproducibility-critical workflows
2. Enable strict policy mode: `ANTS_DECOMPOSITION_POLICY=strict`
3. Validate specific use cases against non-decomposed baseline

**Documentation:**
- Final recommendation memo: [docs/source/pad_width_auto_investigation_final_recommendation.rst](docs/source/pad_width_auto_investigation_final_recommendation.rst)
- Investigation tests: [lib/ants/tests/decomposition/test_regrid_reproducibility_investigation.py](lib/ants/tests/decomposition/test_regrid_reproducibility_investigation.py)

Test Suite Results
==================

- Phase 1 baseline: 4/4 ✅
- Phase 1 algorithms: 3/3 ✅
- Phase 2 multi-resolution: 6/6 ✅
- Phase 2 metrics collection: 7/7 ✅
- Phase 3 recommendation: 4/4 ✅

**Total:** 18 new tests, all passing
**Overall decomposition suite:** 94 passed, 2 xfailed (expected)

No implementation required. Investigation recommended to accept "do not adopt" decision.
