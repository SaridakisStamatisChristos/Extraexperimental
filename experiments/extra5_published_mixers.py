#!/usr/bin/env python3
"""Literal reconstruction of Bikos et al. (2023), Cryptography 7(4):54, §5.3.5.

This reproduces only the PUBLISHED bit-mixing pseudocode. It does not recreate
current Allwyn/OPAP software, seeds, number sampling, or generator settings.
"""
import itertools
import json
from pathlib import Path


def validate(x, y=None):
    if len(x) < 2 or any(v not in (0, 1) for v in x):
        raise ValueError("X must contain at least two bits")
    if y is not None and (len(y) != len(x) or any(v not in (0, 1) for v in y)):
        raise ValueError("Y must be equally long and binary")


def mixer_m(x, y):
    """Exact order and wrap steps printed in §5.3.5."""
    validate(x, y)
    v = [x[0], x[1]]
    out = []
    for j in range(2, len(x)):
        i = y[j]
        out.append(v[i])
        v[i] = x[j]
    i = y[0]
    out.append(v[i])
    v[i] = x[0]
    i = y[1]
    out.append(v[i])
    return out


def mixer_b(x):
    """Exact order and wrap steps printed in §5.3.5."""
    validate(x)
    v = [x[0], x[1]]
    out = []
    for j in range(2, len(x)):
        i = x[j]
        out.append(v[i])
        v[i] = x[j]
    i = x[0]
    out.append(v[i])
    v[i] = x[0]
    i = x[1]
    out.append(v[i])
    return out


def run_exhaustive():
    total = 0
    maximum_body_errors = 0
    max_cyclic_errors = 0
    b_errors_by_length = {}
    for n in range(2, 15):
        errors = 0
        for seq in itertools.product((0, 1), repeat=n):
            total += 1
            x = list(seq)
            result = mixer_b(x)
            assert len(result) == n
            body = sum(result[j - 2] != x[j] for j in range(2, n))
            cyclic = sum(a != b for a, b in zip(result, x[2:] + x[:2]))
            maximum_body_errors = max(maximum_body_errors, body)
            max_cyclic_errors = max(max_cyclic_errors, cyclic)
            assert body <= 2, (x, result)
            # After its first main-loop appearance, symbol i fixes V[i]=i.
            already_seen = set()
            for j in range(2, n):
                if x[j] in already_seen:
                    assert result[j - 2] == x[j]
                already_seen.add(x[j])
            errors += body
        b_errors_by_length[n] = errors

    # Exhaustive M test with all pairs of binary strings through length seven.
    m_pairs = 0
    first_not_a_permutation = None
    for n in range(2, 8):
        for xt in itertools.product((0, 1), repeat=n):
            x = list(xt)
            for yt in itertools.product((0, 1), repeat=n):
                y = list(yt)
                result = mixer_m(x, y)
                m_pairs += 1
                assert len(result) == n
                assert set(result).issubset(set(x))
                if sum(result) != sum(x) and first_not_a_permutation is None:
                    first_not_a_permutation = {"X": "".join(map(str, x)),
                                               "Y": "".join(map(str, y)),
                                               "output": "".join(map(str, result))}
    assert first_not_a_permutation == {"X": "001", "Y": "001", "output": "000"}
    return {
        "source": "Bikos et al. (2023), §5.3.5, DOI 10.3390/cryptography7040054",
        "scope": "literal published bit-level mixers, not verified deployed software",
        "B_inputs_exhaustively_checked": total,
        "B_lengths_tested": [2, 14],
        "B_main_loop_max_mismatches_to_shifted_X": maximum_body_errors,
        "B_entire_output_max_mismatches_to_cyclic_shift_X": max_cyclic_errors,
        "B_mismatch_count_by_length": b_errors_by_length,
        "M_pair_inputs_checked": m_pairs,
        "M_not_a_permutation_counterexample": first_not_a_permutation,
        "current_2026_rng_identified": False
    }


if __name__ == "__main__":
    result = run_exhaustive()
    path = Path(__file__).with_name("extra5_published_mixers_results.json")
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
