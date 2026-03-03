from __future__ import annotations

import random
from datetime import date
from typing import Iterable, Sequence

from .models import Puzzle, PuzzleEquation, PuzzleSymbol
from .utils import stable_hash


HOOKS: Sequence[str] = (
    "Can you solve this brain trap in 7 seconds?",
    "USA + UK challenge: solve before timer ends.",
    "Most people miss one detail. Can you spot it?",
    "Pause now. Solve this before the reveal.",
)


def _signature(flower_value: int, cat_value: int, rabbit_value: int) -> str:
    return stable_hash([str(flower_value), str(cat_value), str(rabbit_value)])


def _build_puzzle(seed: int, run_date: str, index: int) -> Puzzle:
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
            "Solve this puzzle.",
            equations[0].text.replace("x", "times"),
            equations[1].text.replace("x", "times"),
            equations[2].text.replace("x", "times"),
            "Now solve.",
            question.replace("x", "times"),
            f"Answer is {answer}.",
            explanation[1],
        ]
    )

    puzzle_id = f"{run_date.replace('-', '')}_{index:02d}_{sig[:8]}"

    return Puzzle(
        puzzle_id=puzzle_id,
        title="Flower Animal Math Trap",
        hook=rng.choice(HOOKS),
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


def generate_unique_puzzle(run_date: date, index: int, recent_signatures: Iterable[str]) -> Puzzle:
    existing = set(recent_signatures)
    date_key = run_date.isoformat()

    for attempt in range(500):
        seed_parts = [date_key, str(index), str(attempt)]
        seed = int(stable_hash(seed_parts)[:12], 16)
        puzzle = _build_puzzle(seed=seed, run_date=date_key, index=index)
        if puzzle.signature not in existing:
            return puzzle

    raise RuntimeError("Unable to generate a unique puzzle after 500 attempts.")
