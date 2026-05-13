.. meta::
   :description lang=en: Decomposition safety analysis and API-preserving refactor guidance
   :keywords: decomposition, safety, equivalence, refactor
   :property=og:locale: en_GB

.. include:: common.txt

Decomposition Safety Analysis
=============================

This page captures implementation-level guidance for analysing and evolving
ANTS decomposition while preserving public APIs.

Scope
-----

The guidance in this page applies to decomposition behavior implemented in
:mod:`ants.decomposition`, with particular focus on:

* semantic equivalence between decomposed and non-decomposed execution,
* operation categories that are unsafe for decomposition,
* internal refactoring opportunities that do not change public APIs.

Current Behavior Summary
------------------------

Decomposition in :func:`ants.decomposition.decompose` performs the following:

1. determines split behavior from ``[ants_decomposition]`` config,
2. bypasses decomposition when both splits are unset or ``0``,
3. creates source or target mosaics for unary/binary operation styles,
4. executes piecewise via serial or multiprocessing executor,
5. gathers piecewise outputs back to final cube(s), restoring circular status.

The public API currently exposed to users is:

* :func:`ants.decomposition.decompose`,
* decomposition config keys ``x_split``, ``y_split``, ``pad_width``.

Result-Preservation Risk Matrix
-------------------------------

Decomposition is safe only when an operation can be evaluated independently on
piecewise domains and then recombined without changing semantics.

Safe
^^^^

* element-wise transforms (for example, additive or multiplicative scaling),
* local operations where required neighborhood is fully covered by configured
  overlap padding,
* binary operations where source extraction overlap plus operation behavior is
  local and deterministic.

Conditionally Safe
^^^^^^^^^^^^^^^^^^

* stencil-like operations, if ``pad_width`` is at least the maximum required
  neighborhood radius,
* interpolation/regridding where edge behavior is stable under piecewise source
  extraction and target splitting,
* floating-point pipelines where tolerance-based equality is acceptable.

Unsafe
^^^^^^

* global reductions and statistics (for example, global mean, quantiles),
* algorithms requiring global ordering or global topology awareness,
* routines depending on circular-domain context for each piece,
* operations that are sensitive to piece boundaries beyond configurable overlap.

Refactor Goals (Public API Preserved)
-------------------------------------

The following internal refactors can improve maintainability while preserving
existing user-facing API and configuration behavior:

* isolate split planning from execution orchestration,
* isolate source-target relationship validation into explicit helper routine(s),
* isolate result gathering/cleanup from execution runner implementation,
* centralize equivalence precondition checks for operation suitability.

Current internal implementation includes advisory precondition checks before
decomposed execution begins. These checks emit warnings for higher-risk cases
such as reduction-like operations, binary regrid-like operations, and binary
operations with ``pad_width=0``.

A suitable sequencing is:

1. extract pure helpers (split planning, validation, policy),
2. keep :func:`ants.decomposition.decompose` as an adapter calling new helpers,
3. preserve existing call signatures and config semantics,
4. evolve internal executor wiring behind current classes.

Verification Checklist
----------------------

For operations intended to run with decomposition, verify equivalence against
all of the following decomposition modes:

* ``x_split=0, y_split=0`` (framework disabled baseline),
* ``x_split=1, y_split=1`` (single-piece decomposition path),
* ``x_split=2, y_split=2`` (multi-piece path),
* ``x_split=automatic, y_split=automatic`` (auto-split path).

Additionally verify:

* data and mask consistency,
* coordinate points and bounds consistency,
* metadata consistency,
* behavior under single-process and multi-process execution where supported.

Implementation Note
-------------------

The decomposition test matrix in
``lib/ants/tests/decomposition/test_equivalence_matrix.py`` is intended as a
starting point for enforcing these guarantees in CI.
