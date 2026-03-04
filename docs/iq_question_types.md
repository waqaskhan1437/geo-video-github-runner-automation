# IQ Question Types Used In Automation

This file documents the non-calculation IQ puzzle types used by `--mode intelligence`.

## Count

There is no single universal global count for IQ question categories.  
For this automation, we use a practical set of **9 puzzle types** designed for short videos.

## Types Implemented

1. Arrangement logic
2. No-crossing line maze
3. Truth-check constraints
4. Odd-one-out
5. Analogy
6. Syllogism
7. Direction sense
8. Conditional elimination
9. Rotation pattern

## Code Mapping

Implemented in: `src/whiteboard_automation/puzzles.py`

1. `_build_intelligence_arrangement`
2. `_build_intelligence_link_maze_one`
3. `_build_intelligence_link_maze_two`
4. `_build_intelligence_truth`
5. `_build_intelligence_odd_one`
6. `_build_intelligence_analogy`
7. `_build_intelligence_syllogism`
8. `_build_intelligence_direction`
9. `_build_intelligence_conditional`
10. `_build_intelligence_rotation`

## Selection Rule

`index` decides template by modulo rotation:

- index 1 -> type 1
- index 2 -> type 2
- ...
- index 9 -> type 9
- index 10 -> type 1 again
