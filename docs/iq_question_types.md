# IQ Question Types Used In Automation

This file documents the non-calculation IQ puzzle types used by `--mode intelligence`.

## Count

There is no single universal global count for IQ question categories.  
For this automation, we use a practical set of **8 puzzle types** designed for short videos.

## Types Implemented

1. Arrangement logic
2. Truth-check constraints
3. Odd-one-out
4. Analogy
5. Syllogism
6. Direction sense
7. Conditional elimination
8. Rotation pattern

## Code Mapping

Implemented in: `src/whiteboard_automation/puzzles.py`

1. `_build_intelligence_arrangement`
2. `_build_intelligence_truth`
3. `_build_intelligence_odd_one`
4. `_build_intelligence_analogy`
5. `_build_intelligence_syllogism`
6. `_build_intelligence_direction`
7. `_build_intelligence_conditional`
8. `_build_intelligence_rotation`

## Selection Rule

`index` decides template by modulo rotation:

- index 1 -> type 1
- index 2 -> type 2
- ...
- index 8 -> type 8
- index 9 -> type 1 again
