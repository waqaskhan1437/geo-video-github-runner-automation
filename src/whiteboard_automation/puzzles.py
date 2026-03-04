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
    "Intelligence round: focus on logic, not speed.",
    "Advanced IQ puzzle. One clean pattern unlocks it.",
    "Edge challenge: only careful thinkers solve this fast.",
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


def _build_intelligence_sequence(run_date: str, index: int) -> Puzzle:
    sig = stable_hash(["intelligence", "sequence", run_date, str(index)])
    equations = [
        PuzzleEquation(text="2, 6, 12, 20, 30, ?"),
        PuzzleEquation(text="Differences are +4, +6, +8, +10"),
        PuzzleEquation(text="Next difference should be +12"),
    ]

    return Puzzle(
        puzzle_id=f"{run_date.replace('-', '')}_{index:02d}_{sig[:8]}",
        title="Pattern Sequence IQ",
        hook=random.Random(int(sig[:12], 16)).choice(INTELLIGENCE_HOOKS),
        category="intelligence",
        source_url="https://en.wikipedia.org/wiki/Number_sequence",
        source_note="Inspired by classic number pattern intelligence tests",
        symbols={},
        equations=equations,
        question="What is the missing number?",
        answer=42,
        explanation=[
            "Each step adds the next even number in sequence",
            "+4, +6, +8, +10 then +12",
            "30 + 12 = 42",
        ],
        narration="Find the sequence rule. Two, six, twelve, twenty, thirty, question mark. The jumps are plus four, plus six, plus eight, plus ten. Next jump is plus twelve. Final answer is forty two.",
        signature=sig,
    )


def _build_intelligence_age(run_date: str, index: int) -> Puzzle:
    sig = stable_hash(["intelligence", "age-ratio", run_date, str(index)])
    equations = [
        PuzzleEquation(text="Father is 3 times son's age"),
        PuzzleEquation(text="After 12 years father is 2 times son"),
        PuzzleEquation(text="Find son's current age"),
    ]

    return Puzzle(
        puzzle_id=f"{run_date.replace('-', '')}_{index:02d}_{sig[:8]}",
        title="Age Ratio Logic",
        hook=random.Random(int(sig[:12], 16)).choice(INTELLIGENCE_HOOKS),
        category="intelligence",
        source_url="https://brilliant.org/wiki/age-problems/",
        source_note="Inspired by age-ratio algebra intelligence questions",
        symbols={},
        equations=equations,
        question="Son age right now = ?",
        answer=12,
        explanation=[
            "Let son = x and father = 3x",
            "After 12 years: 3x + 12 = 2(x + 12)",
            "x = 12",
        ],
        narration="Logic age puzzle. Father is three times the son's age. After twelve years, father becomes two times the son. Solve for son's present age. The answer is twelve.",
        signature=sig,
    )


def _build_intelligence_digit(run_date: str, index: int) -> Puzzle:
    sig = stable_hash(["intelligence", "digit-logic", run_date, str(index)])
    equations = [
        PuzzleEquation(text="A 3-digit number has digit sum 12"),
        PuzzleEquation(text="Hundreds digit = 2 times tens digit"),
        PuzzleEquation(text="Ones digit = hundreds digit - 3"),
    ]

    return Puzzle(
        puzzle_id=f"{run_date.replace('-', '')}_{index:02d}_{sig[:8]}",
        title="Digit Constraint Puzzle",
        hook=random.Random(int(sig[:12], 16)).choice(INTELLIGENCE_HOOKS),
        category="intelligence",
        source_url="https://www.math-only-math.com/problems-on-numbers.html",
        source_note="Inspired by digit-constraint intelligence questions",
        symbols={},
        equations=equations,
        question="What is the number?",
        answer=633,
        explanation=[
            "Let tens digit be t, then hundreds = 2t and ones = 2t - 3",
            "Sum: 2t + t + (2t - 3) = 12 => 5t = 15 => t = 3",
            "Number is 633",
        ],
        narration="Digit intelligence puzzle. The sum of digits is twelve. Hundreds digit is twice the tens digit. Ones digit is three less than the hundreds digit. Correct number is six hundred thirty three.",
        signature=sig,
    )


def _build_internet_puzzle(run_date: str, index: int) -> Puzzle:
    templates: Sequence[Callable[[str, int], Puzzle]] = (
        _build_internet_bat_ball,
        _build_internet_heads_legs,
    )
    builder = templates[(index - 1) % len(templates)]
    return builder(run_date, index)


def _build_intelligence_puzzle(run_date: str, index: int) -> Puzzle:
    templates: Sequence[Callable[[str, int], Puzzle]] = (
        _build_intelligence_sequence,
        _build_intelligence_age,
        _build_intelligence_digit,
    )
    builder = templates[(index - 1) % len(templates)]
    return builder(run_date, index)


def _with_salted_signature(puzzle: Puzzle, date_key: str, index: int) -> Puzzle:
    salted_sig = stable_hash([puzzle.signature, date_key, str(index), "salt"])
    return replace(
        puzzle,
        puzzle_id=f"{date_key.replace('-', '')}_{index:02d}_{salted_sig[:8]}",
        signature=salted_sig,
    )


def generate_unique_puzzle(
    run_date: date,
    index: int,
    recent_signatures: Iterable[str],
    mode: str = "generated",
) -> Puzzle:
    existing = set(recent_signatures)
    date_key = run_date.isoformat()

    if mode == "internet":
        puzzle = _build_internet_puzzle(run_date=date_key, index=index)
        if puzzle.signature in existing:
            puzzle = _with_salted_signature(puzzle=puzzle, date_key=date_key, index=index)
        return puzzle

    if mode == "intelligence":
        puzzle = _build_intelligence_puzzle(run_date=date_key, index=index)
        if puzzle.signature in existing:
            puzzle = _with_salted_signature(puzzle=puzzle, date_key=date_key, index=index)
        return puzzle

    for attempt in range(500):
        seed_parts = [date_key, str(index), str(attempt)]
        seed = int(stable_hash(seed_parts)[:12], 16)
        puzzle = _build_generated_puzzle(seed=seed, run_date=date_key, index=index)
        if puzzle.signature not in existing:
            return puzzle

    raise RuntimeError("Unable to generate a unique puzzle after 500 attempts.")
