# Internet Question Sources (Used For New Video Templates)

These are the online references used to design the two new puzzle templates in `internet` mode.
The scripts are adapted/originalized for short video format (not copied verbatim).

## 1) Bat-and-ball cognitive trap

- Source: https://en.wikipedia.org/wiki/Cognitive_reflection_test
- Used for: video template `Bat And Ball Trap`
- In code: `src/whiteboard_automation/puzzles.py` (`_build_internet_bat_ball`)

## 2) Chickens-and-rabbits heads/legs puzzle

- Source: https://www.numbrix.net/problems/chickens-and-rabbits-head-and-feet-puzzle/
- Used for: video template `Heads And Legs Puzzle`
- In code: `src/whiteboard_automation/puzzles.py` (`_build_internet_heads_legs`)

## Notes

1. Puzzle wording is rewritten for short-video narration.
2. Visual layout and explanation steps are original code and template logic.
3. Metadata now stores `source_url` and `source_note` for each generated internet-mode puzzle.
