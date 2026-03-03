from __future__ import annotations

import random
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
            "Alright, quick puzzle round.",
            "Use the three clues carefully.",
            equations[0].text.replace("x", "times") + ".",
            equations[1].text.replace("x", "times") + ".",
            equations[2].text.replace("x", "times") + ".",
            "Now pause and solve the final line.",
            question.replace("x", "times") + ".",
            f"Correct answer is {answer}.",
            "The trick is the flower with one missing petal.",
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
        "x + (x + 1.00) = 1.10 -> 2x = 0.10",
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
            "Because two times ball plus one dollar equals one point one zero.",
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
        "C + R = 35 and C + 2R = 47 after dividing legs by 2",
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
            "Then chickens become twenty three.",
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


def _build_internet_puzzle(run_date: str, index: int) -> Puzzle:
    templates: Sequence[Callable[[str, int], Puzzle]] = (
        _build_internet_bat_ball,
        _build_internet_heads_legs,
    )
    builder = templates[(index - 1) % len(templates)]
    return builder(run_date, index)


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
            # Keep internet template style but avoid signature collision in history.
            salted_sig = stable_hash([puzzle.signature, date_key, str(index), "salt"])
            puzzle = Puzzle(
                puzzle_id=f"{date_key.replace('-', '')}_{index:02d}_{salted_sig[:8]}",
                title=puzzle.title,
                hook=puzzle.hook,
                category=puzzle.category,
                source_url=puzzle.source_url,
                source_note=puzzle.source_note,
                symbols=puzzle.symbols,
                equations=puzzle.equations,
                question=puzzle.question,
                answer=puzzle.answer,
                explanation=puzzle.explanation,
                narration=puzzle.narration,
                signature=salted_sig,
            )
        return puzzle

    for attempt in range(500):
        seed_parts = [date_key, str(index), str(attempt)]
        seed = int(stable_hash(seed_parts)[:12], 16)
        puzzle = _build_generated_puzzle(seed=seed, run_date=date_key, index=index)
        if puzzle.signature not in existing:
            return puzzle

    raise RuntimeError("Unable to generate a unique puzzle after 500 attempts.")
