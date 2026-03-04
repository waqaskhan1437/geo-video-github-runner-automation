from __future__ import annotations

import random
from dataclasses import replace
from datetime import date
from typing import Callable, Iterable, Sequence

from .models import Puzzle, PuzzleEquation, PuzzleSymbol
from .utils import stable_hash


HOOKS: Sequence[str] = (
    "Can you solve this brain trap in 7 seconds?",
    "USA + UK challenge: solve before timer ends.",
    "Most people miss one detail. Can you spot it?",
    "Pause now. Solve this before the reveal.",
)

INTERNET_HOOKS: Sequence[str] = (
    "Internet favorite puzzle, short version.",
    "This one fooled thousands online.",
    "Classic viral brain teaser. Try now.",
)

INTELLIGENCE_HOOKS: Sequence[str] = (
    "IQ round: use logic, not calculation.",
    "Pattern and reasoning challenge. Stay sharp.",
    "Think calm, solve clean, reveal in seconds.",
)


def _signature(flower_value: int, cat_value: int, rabbit_value: int) -> str:
    return stable_hash([str(flower_value), str(cat_value), str(rabbit_value)])


def _build_generated_puzzle(seed: int, run_date: str, index: int) -> Puzzle:
    rng = random.Random(seed)

    flower_value = rng.randint(4, 9)
    cat_value = rng.randint(2, 8)
    rabbit_value = rng.randint(1, 6)

    sig = _signature(flower_value, cat_value, rabbit_value)

    equations = [
        PuzzleEquation(text=f"F + F + F = {flower_value * 3}"),
        PuzzleEquation(text=f"C + C + F = {(cat_value * 2) + flower_value}"),
        PuzzleEquation(text=f"R + C + F = {rabbit_value + cat_value + flower_value}"),
    ]

    question = "(F* + C) x R = ?"
    answer = ((flower_value - 1) + cat_value) * rabbit_value

    explanation = [
        f"F = {flower_value}, C = {cat_value}, R = {rabbit_value}",
        "F* means one missing petal, so F* = F - 1",
        f"({flower_value - 1} + {cat_value}) x {rabbit_value} = {answer}",
    ]

    narration = " ".join(
        [
            "Welcome back. Quick logic warm-up.",
            equations[0].text.replace("x", "times") + ".",
            equations[1].text.replace("x", "times") + ".",
            equations[2].text.replace("x", "times") + ".",
            "Now solve the final expression.",
            question.replace("x", "times") + ".",
            f"Correct answer is {answer}.",
            "The trap is the flower with one missing petal.",
        ]
    )

    puzzle_id = f"{run_date.replace('-', '')}_{index:02d}_{sig[:8]}"

    return Puzzle(
        puzzle_id=puzzle_id,
        title="Flower Animal Math Trap",
        hook=rng.choice(HOOKS),
        category="generated",
        source_url="",
        source_note="Original generated puzzle",
        symbols={
            "F": PuzzleSymbol(key="F", label="Flower", value=flower_value),
            "C": PuzzleSymbol(key="C", label="Cat", value=cat_value),
            "R": PuzzleSymbol(key="R", label="Rabbit", value=rabbit_value),
            "F*": PuzzleSymbol(key="F*", label="Flower Missing Petal", value=flower_value - 1),
        },
        equations=equations,
        question=question,
        answer=answer,
        explanation=explanation,
        narration=narration,
        signature=sig,
    )


def _build_internet_bat_ball(run_date: str, index: int) -> Puzzle:
    equations = [
        PuzzleEquation(text="Bat + Ball = 1.10 dollars"),
        PuzzleEquation(text="Bat = Ball + 1.00 dollars"),
        PuzzleEquation(text="Question: Ball price in cents?"),
    ]

    answer = 5
    explanation = [
        "Let ball = x and bat = x + 1.00",
        "x + (x + 1.00) = 1.10 so 2x = 0.10",
        "x = 0.05 dollars, so ball = 5 cents",
    ]

    sig = stable_hash(["internet", "bat-ball", run_date, str(index)])

    narration = " ".join(
        [
            "Classic internet puzzle.",
            "A bat and a ball cost one dollar and ten cents together.",
            "The bat costs one dollar more than the ball.",
            "Pause now and guess the ball price.",
            "Most people say ten cents, but that is incorrect.",
            "Correct answer is five cents.",
        ]
    )

    return Puzzle(
        puzzle_id=f"{run_date.replace('-', '')}_{index:02d}_{sig[:8]}",
        title="Bat And Ball Trap",
        hook=random.Random(int(sig[:12], 16)).choice(INTERNET_HOOKS),
        category="internet",
        source_url="https://en.wikipedia.org/wiki/Cognitive_reflection_test",
        source_note="Inspired by the Cognitive Reflection Test bat-and-ball question",
        symbols={},
        equations=equations,
        question="Ball price in cents = ?",
        answer=answer,
        explanation=explanation,
        narration=narration,
        signature=sig,
    )


def _build_internet_heads_legs(run_date: str, index: int) -> Puzzle:
    equations = [
        PuzzleEquation(text="Chickens + Rabbits = 35 heads"),
        PuzzleEquation(text="2*Chickens + 4*Rabbits = 94 legs"),
        PuzzleEquation(text="Question: How many rabbits?"),
    ]

    answer = 12
    explanation = [
        "Let C be chickens and R be rabbits",
        "C + R = 35 and C + 2R = 47",
        "Subtract equations: R = 12, then C = 23",
    ]

    sig = stable_hash(["internet", "heads-legs", run_date, str(index)])

    narration = " ".join(
        [
            "Another internet favorite.",
            "There are thirty five animals, chickens and rabbits together.",
            "Total legs are ninety four.",
            "How many rabbits are there?",
            "Pause and solve.",
            "Correct answer is twelve rabbits.",
        ]
    )

    return Puzzle(
        puzzle_id=f"{run_date.replace('-', '')}_{index:02d}_{sig[:8]}",
        title="Heads And Legs Puzzle",
        hook=random.Random(int(sig[:12], 16)).choice(INTERNET_HOOKS),
        category="internet",
        source_url="https://www.numbrix.net/problems/chickens-and-rabbits-head-and-feet-puzzle/",
        source_note="Inspired by the classic chickens-and-rabbits heads and legs puzzle",
        symbols={
            "C": PuzzleSymbol(key="C", label="Chicken", value=23),
            "R": PuzzleSymbol(key="R", label="Rabbit", value=12),
        },
        equations=equations,
        question="Number of rabbits = ?",
        answer=answer,
        explanation=explanation,
        narration=narration,
        signature=sig,
    )


def _build_intelligence_link_maze_one(run_date: str, index: int) -> Puzzle:
    sig = stable_hash(["intelligence", "link-maze-one", run_date, str(index)])
    equations = [
        PuzzleEquation(text="Connect same letters: A-A, B-B, C-C."),
        PuzzleEquation(text="Lines cannot cross or overlap."),
        PuzzleEquation(text="Center gate can be used by only one pair."),
        PuzzleEquation(text="Use outside boundary routes only if needed."),
    ]

    return Puzzle(
        puzzle_id=f"{run_date.replace('-', '')}_{index:02d}_{sig[:8]}",
        title="No Crossing Link Maze I",
        hook="High IQ path puzzle. Visualize before drawing.",
        category="intelligence",
        source_url="https://en.wikipedia.org/wiki/Planar_graph",
        source_note="Inspired by no-crossing path and planar connection puzzles",
        symbols={},
        equations=equations,
        question="Minimum outside routes needed? (0, 1, 2, or 3)",
        answer=2,
        explanation=[
            "C is aligned with the center gate, so reserve gate for C.",
            "A and B are swapped across sides, so a single outside route is not enough.",
            "One takes upper outside route and one takes lower outside route, minimum is 2.",
        ],
        narration="No crossing link maze. Connect A to A, B to B, and C to C. Lines cannot cross and center gate is single use. Think carefully. Minimum outside routes required are two.",
        signature=sig,
    )


def _build_intelligence_link_maze_two(run_date: str, index: int) -> Puzzle:
    sig = stable_hash(["intelligence", "link-maze-two", run_date, str(index)])
    equations = [
        PuzzleEquation(text="Connect A-A, B-B, and C-C without crossing."),
        PuzzleEquation(text="The middle gate allows only one pair."),
        PuzzleEquation(text="If A or B uses the gate first, dead-end happens."),
        PuzzleEquation(text="Choose which pair must use center gate first."),
    ]

    return Puzzle(
        puzzle_id=f"{run_date.replace('-', '')}_{index:02d}_{sig[:8]}",
        title="No Crossing Link Maze II",
        hook="Hard visual reasoning: pick the only safe first move.",
        category="intelligence",
        source_url="https://en.wikipedia.org/wiki/Logic_puzzle",
        source_note="Inspired by route-order and deadlock avoidance puzzles",
        symbols={},
        equations=equations,
        question="Which pair must use the center gate first? (1=A, 2=B, 3=C)",
        answer=3,
        explanation=[
            "A and B are opposite-swapped and need outer detours.",
            "If either A or B consumes center gate, the remaining layout forces a crossing.",
            "Only C can safely take center gate first, so answer is option 3.",
        ],
        narration="Hard link maze. Three pairs must be connected without crossing. Center gate is one-time safe passage. If A or B takes it first, puzzle locks. Correct first gate pair is C, option three.",
        signature=sig,
    )


def _build_intelligence_arrangement(run_date: str, index: int) -> Puzzle:
    sig = stable_hash(["intelligence", "arrangement", run_date, str(index)])
    equations = [
        PuzzleEquation(text="Seats 1 to 4 are arranged left to right."),
        PuzzleEquation(text="Cat sits immediately left of Dog."),
        PuzzleEquation(text="Rabbit sits on seat 4."),
        PuzzleEquation(text="Fox sits somewhere left of Cat."),
    ]

    return Puzzle(
        puzzle_id=f"{run_date.replace('-', '')}_{index:02d}_{sig[:8]}",
        title="Animal Seating Logic",
        hook=random.Random(int(sig[:12], 16)).choice(INTELLIGENCE_HOOKS),
        category="intelligence",
        source_url="https://en.wikipedia.org/wiki/Logic_puzzle",
        source_note="Inspired by arrangement and seating logic puzzles",
        symbols={},
        equations=equations,
        question="Dog is on which seat number? (1-4)",
        answer=3,
        explanation=[
            "Rabbit is fixed on seat 4.",
            "Cat must be immediately left of Dog.",
            "Fox must stay left of Cat, so order is Fox-1, Cat-2, Dog-3, Rabbit-4.",
        ],
        narration="Arrangement IQ puzzle. Seats are one to four from left to right. Cat sits immediately left of Dog. Rabbit sits on seat four. Fox is somewhere left of Cat. Dog lands on seat three. Correct option is three.",
        signature=sig,
    )


def _build_intelligence_truth(run_date: str, index: int) -> Puzzle:
    sig = stable_hash(["intelligence", "truth-check", run_date, str(index)])
    equations = [
        PuzzleEquation(text="Exactly one of A and B is telling the truth."),
        PuzzleEquation(text="A says: The code is 7."),
        PuzzleEquation(text="B says: The code is 9."),
        PuzzleEquation(text="The code is odd and greater than 7."),
    ]

    return Puzzle(
        puzzle_id=f"{run_date.replace('-', '')}_{index:02d}_{sig[:8]}",
        title="Truth Check Puzzle",
        hook=random.Random(int(sig[:12], 16)).choice(INTELLIGENCE_HOOKS),
        category="intelligence",
        source_url="https://en.wikipedia.org/wiki/Logical_reasoning",
        source_note="Inspired by truth-testing and constraint logic puzzles",
        symbols={},
        equations=equations,
        question="Which option is the code? (1=7, 2=8, 3=9, 4=11)",
        answer=3,
        explanation=[
            "Odd and greater than 7 leaves only 9 or 11.",
            "A says 7, so A must be false.",
            "Exactly one truth means B is true, so the code is 9 (option 3).",
        ],
        narration="Truth check IQ puzzle. Exactly one of A and B is true. A says the code is seven. B says the code is nine. The code is odd and greater than seven. That removes seven and eight. A is false, B is true, so code is nine. Correct option is three.",
        signature=sig,
    )


def _build_intelligence_odd_one(run_date: str, index: int) -> Puzzle:
    sig = stable_hash(["intelligence", "odd-one-out", run_date, str(index)])
    equations = [
        PuzzleEquation(text="Find the odd one out from these four options:"),
        PuzzleEquation(text="1) Rose"),
        PuzzleEquation(text="2) Tulip"),
        PuzzleEquation(text="3) Dolphin"),
        PuzzleEquation(text="4) Lily"),
    ]

    return Puzzle(
        puzzle_id=f"{run_date.replace('-', '')}_{index:02d}_{sig[:8]}",
        title="Odd One Out IQ",
        hook=random.Random(int(sig[:12], 16)).choice(INTELLIGENCE_HOOKS),
        category="intelligence",
        source_url="https://en.wikipedia.org/wiki/Inductive_reasoning",
        source_note="Inspired by odd-one-out style intelligence tests",
        symbols={},
        equations=equations,
        question="Which option number is different? (1-4)",
        answer=3,
        explanation=[
            "Rose, Tulip, and Lily are flowers.",
            "Dolphin is an animal, not a flower.",
            "So the odd one out is option 3.",
        ],
        narration="Odd one out IQ puzzle. Rose, tulip, dolphin, lily. Three are flowers and one is an animal. Dolphin is different. Correct option is three.",
        signature=sig,
    )


def _build_intelligence_analogy(run_date: str, index: int) -> Puzzle:
    sig = stable_hash(["intelligence", "analogy", run_date, str(index)])
    equations = [
        PuzzleEquation(text="Analogy pattern:"),
        PuzzleEquation(text="Puppy : Dog"),
        PuzzleEquation(text="Kitten : ?"),
        PuzzleEquation(text="Options: 1) Cat 2) Goat 3) Deer 4) Horse"),
    ]

    return Puzzle(
        puzzle_id=f"{run_date.replace('-', '')}_{index:02d}_{sig[:8]}",
        title="Analogy Puzzle",
        hook=random.Random(int(sig[:12], 16)).choice(INTELLIGENCE_HOOKS),
        category="intelligence",
        source_url="https://en.wikipedia.org/wiki/Analogical_reasoning",
        source_note="Inspired by verbal analogy IQ questions",
        symbols={},
        equations=equations,
        question="Best matching option number is? (1-4)",
        answer=1,
        explanation=[
            "Puppy is the young one of a dog.",
            "Kitten is the young one of a cat.",
            "So the correct option is 1.",
        ],
        narration="Analogy IQ puzzle. Puppy relates to dog. Kitten should relate to cat. So the correct answer is option one.",
        signature=sig,
    )


def _build_intelligence_syllogism(run_date: str, index: int) -> Puzzle:
    sig = stable_hash(["intelligence", "syllogism", run_date, str(index)])
    equations = [
        PuzzleEquation(text="All tulips are flowers."),
        PuzzleEquation(text="No flower is metal."),
        PuzzleEquation(text="Pick the statement that must be true."),
        PuzzleEquation(text="1) Some metals are tulips 2) No tulip is metal 3) All metals are flowers 4) Some flowers are metal"),
    ]

    return Puzzle(
        puzzle_id=f"{run_date.replace('-', '')}_{index:02d}_{sig[:8]}",
        title="Syllogism Logic",
        hook=random.Random(int(sig[:12], 16)).choice(INTELLIGENCE_HOOKS),
        category="intelligence",
        source_url="https://en.wikipedia.org/wiki/Syllogism",
        source_note="Inspired by classical syllogism reasoning tasks",
        symbols={},
        equations=equations,
        question="Which option must be true? (1-4)",
        answer=2,
        explanation=[
            "If all tulips are flowers, and no flower is metal, tulips cannot be metal.",
            "Only option 2 is always true under these rules.",
            "Therefore answer is option 2.",
        ],
        narration="Syllogism puzzle. All tulips are flowers and no flower is metal. That means no tulip can be metal. Correct option is two.",
        signature=sig,
    )


def _build_intelligence_direction(run_date: str, index: int) -> Puzzle:
    sig = stable_hash(["intelligence", "direction", run_date, str(index)])
    equations = [
        PuzzleEquation(text="Start facing North."),
        PuzzleEquation(text="Turn right, then left, then left."),
        PuzzleEquation(text="Options: 1) North 2) South 3) East 4) West"),
    ]

    return Puzzle(
        puzzle_id=f"{run_date.replace('-', '')}_{index:02d}_{sig[:8]}",
        title="Direction IQ",
        hook=random.Random(int(sig[:12], 16)).choice(INTELLIGENCE_HOOKS),
        category="intelligence",
        source_url="https://en.wikipedia.org/wiki/Spatial_ability",
        source_note="Inspired by direction-sense intelligence questions",
        symbols={},
        equations=equations,
        question="Final direction option number? (1-4)",
        answer=4,
        explanation=[
            "North -> right gives East.",
            "East -> left gives North.",
            "North -> left gives West, so option 4.",
        ],
        narration="Direction puzzle. Start north, turn right, then left, then left again. Final direction becomes west. Correct option is four.",
        signature=sig,
    )


def _build_intelligence_conditional(run_date: str, index: int) -> Puzzle:
    sig = stable_hash(["intelligence", "conditional", run_date, str(index)])
    equations = [
        PuzzleEquation(text="If Rose box has the key, Lily box is empty."),
        PuzzleEquation(text="Lily box is not empty."),
        PuzzleEquation(text="Tulip box is empty."),
        PuzzleEquation(text="Exactly one box contains the key."),
    ]

    return Puzzle(
        puzzle_id=f"{run_date.replace('-', '')}_{index:02d}_{sig[:8]}",
        title="Conditional Logic",
        hook=random.Random(int(sig[:12], 16)).choice(INTELLIGENCE_HOOKS),
        category="intelligence",
        source_url="https://en.wikipedia.org/wiki/Conditional_statement",
        source_note="Inspired by conditional and elimination logic puzzles",
        symbols={},
        equations=equations,
        question="Which box has the key? (1=Rose, 2=Lily, 3=Tulip, 4=None)",
        answer=2,
        explanation=[
            "Rose cannot have key because Lily is not empty.",
            "Tulip is explicitly empty.",
            "Only Lily can hold the key, so option 2.",
        ],
        narration="Conditional logic puzzle. If rose has the key then lily must be empty. But lily is not empty, and tulip is empty too. So the key must be in lily. Correct option is two.",
        signature=sig,
    )


def _build_intelligence_rotation(run_date: str, index: int) -> Puzzle:
    sig = stable_hash(["intelligence", "rotation-pattern", run_date, str(index)])
    equations = [
        PuzzleEquation(text="Arrow pattern: Up, Right, Down, Left, Up, ?"),
        PuzzleEquation(text="Each step rotates 90 degrees clockwise."),
        PuzzleEquation(text="Options: 1) Up 2) Right 3) Down 4) Left"),
    ]

    return Puzzle(
        puzzle_id=f"{run_date.replace('-', '')}_{index:02d}_{sig[:8]}",
        title="Rotation Pattern IQ",
        hook=random.Random(int(sig[:12], 16)).choice(INTELLIGENCE_HOOKS),
        category="intelligence",
        source_url="https://en.wikipedia.org/wiki/Pattern_recognition_(psychology)",
        source_note="Inspired by non-verbal pattern rotation tests",
        symbols={},
        equations=equations,
        question="Next direction option number? (1-4)",
        answer=2,
        explanation=[
            "The direction rotates clockwise each step.",
            "After Up comes Right, then Down, then Left, then Up again.",
            "So the next is Right, option 2.",
        ],
        narration="Rotation IQ puzzle. The arrows move in a clockwise cycle: up, right, down, left, and repeat. After up, the next is right. Correct option is two.",
        signature=sig,
    )


def _build_internet_puzzle(run_date: str, index: int, variant_offset: int = 0) -> Puzzle:
    templates: Sequence[Callable[[str, int], Puzzle]] = (
        _build_internet_bat_ball,
        _build_internet_heads_legs,
    )
    builder = templates[((index - 1) + variant_offset) % len(templates)]
    return builder(run_date, index)


def _build_link_maze_puzzle(run_date: str, index: int, variant_offset: int = 0) -> Puzzle:
    templates: Sequence[Callable[[str, int], Puzzle]] = (
        _build_intelligence_link_maze_one,
        _build_intelligence_link_maze_two,
    )
    builder = templates[((index - 1) + variant_offset) % len(templates)]
    return builder(run_date, index)


def _build_intelligence_puzzle(run_date: str, index: int, variant_offset: int = 0) -> Puzzle:
    templates: Sequence[Callable[[str, int], Puzzle]] = (
        _build_intelligence_link_maze_one,
        _build_intelligence_link_maze_two,
        _build_intelligence_arrangement,
        _build_intelligence_truth,
        _build_intelligence_odd_one,
        _build_intelligence_analogy,
        _build_intelligence_syllogism,
        _build_intelligence_direction,
        _build_intelligence_conditional,
        _build_intelligence_rotation,
    )
    builder = templates[((index - 1) + variant_offset) % len(templates)]
    return builder(run_date, index)


def _with_salted_signature(puzzle: Puzzle, date_key: str, index: int, salt_index: int) -> Puzzle:
    salted_sig = stable_hash([puzzle.signature, date_key, str(index), "salt", str(salt_index)])
    return replace(
        puzzle,
        puzzle_id=f"{date_key.replace('-', '')}_{index:02d}_{salted_sig[:8]}",
        signature=salted_sig,
    )


def _next_unique_from_templates(
    *,
    existing: set[str],
    template_count: int,
    date_key: str,
    index: int,
    builder: Callable[[str, int, int], Puzzle],
) -> Puzzle:
    for attempt in range(500):
        puzzle = builder(date_key, index, attempt)

        if attempt < template_count:
            candidate = puzzle
        else:
            # After all base templates are used, keep generating unique IDs.
            candidate = _with_salted_signature(
                puzzle=puzzle,
                date_key=date_key,
                index=index,
                salt_index=attempt + 1,
            )

        if candidate.signature not in existing:
            return candidate

    raise RuntimeError("Unable to generate a unique puzzle variant after 500 attempts.")


def generate_unique_puzzle(
    run_date: date,
    index: int,
    recent_signatures: Iterable[str],
    mode: str = "generated",
) -> Puzzle:
    existing = set(recent_signatures)
    date_key = run_date.isoformat()

    if mode == "internet":
        return _next_unique_from_templates(
            existing=existing,
            template_count=2,
            date_key=date_key,
            index=index,
            builder=_build_internet_puzzle,
        )

    if mode == "linkmaze":
        return _next_unique_from_templates(
            existing=existing,
            template_count=2,
            date_key=date_key,
            index=index,
            builder=_build_link_maze_puzzle,
        )

    if mode == "intelligence":
        return _next_unique_from_templates(
            existing=existing,
            template_count=10,
            date_key=date_key,
            index=index,
            builder=_build_intelligence_puzzle,
        )

    for attempt in range(500):
        seed_parts = [date_key, str(index), str(attempt)]
        seed = int(stable_hash(seed_parts)[:12], 16)
        puzzle = _build_generated_puzzle(seed=seed, run_date=date_key, index=index)
        if puzzle.signature not in existing:
            return puzzle

    raise RuntimeError("Unable to generate a unique puzzle after 500 attempts.")
