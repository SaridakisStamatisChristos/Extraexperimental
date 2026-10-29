#!/usr/bin/env python3
"""Two consecutive user-supplied EXTRA 5 draws, no target #14251 lookup.

Historical-family results rely on the *completed earlier* seed search archive;
this script independently replays each first-draw matching seed. Affine rank
transition is a toy two-draw interpolation, NOT the lottery RNG or secret seed.
"""
import json
import math
from pathlib import Path
from extra5_one_draw_seed_fit import rank_5of35, unrank_5of35
from extra5_multifamily_compact import stream, decode

FIRST = (2, 4, 30, 32, 35)
SECOND = (2, 5, 9, 30, 33)
N = math.comb(35, 5)


def affine_fit(a):
    if type(a) is not int or a < 1:
        raise ValueError('multiplier must be a positive integer')
    r1, r2 = rank_5of35(FIRST), rank_5of35(SECOND)
    c = (r2 - a * r1) % N
    assert (a * r1 + c) % N == r2
    r3 = (a * r2 + c) % N
    return {'a': a, 'c': c, 'first_rank': r1, 'second_rank': r2,
            'next_rank': r3, 'next_numbers': list(unrank_5of35(r3))}


def evaluate(archive):
    if archive['total_attempted'] != 1640000 or archive['total_first_draw_exact_fits'] != 5:
        raise ValueError('unexpected historical search archive')
    fits = [x for f in archive['families'] for x in f['fits']]
    if len(fits) != 5:
        raise ValueError('incomplete first-ticket match list')
    checked = []
    for candidate in fits:
        raw = stream(candidate['family'], candidate['seed_index'], 128)
        observed1, pos = decode(raw)
        observed2, _ = decode(raw, pos)
        if observed1 != FIRST or list(observed2) != candidate['hidden_next_prediction']:
            raise AssertionError('stored first-ticket fit / continuation fails replay')
        checked.append({'family': candidate['family'], 'seed': candidate['seed_index'],
                        'first': list(observed1), 'second': list(observed2),
                        'second_hits': len(set(observed2) & set(SECOND)),
                        'double_exact': observed2 == SECOND})
    return {'training':[{'draw_id': 14249, 'numbers': list(FIRST)},
                        {'draw_id': 14250, 'numbers': list(SECOND)}],
            'unseen_draw_id':14251,'unseen_result_not_consulted':True,
            'previous_seed_hypotheses_tested':archive['total_attempted'],
            'exact_first_draw_seed_candidates':len(checked),
            'exact_both_draws':sum(x['double_exact'] for x in checked),
            'replayed_seed_candidates':checked,
            'ideal_uniform_pair_probability':1/(N*N),
            'ideal_uniform_expected_pair_hits':archive['total_attempted']/(N*N),
            'illustrative_affine_rank_fit':[affine_fit(a) for a in (1,3,5)],
            'locked_primary_choice':'a=1; c=(r2-r1) mod N; predict unrank((r2+c) mod N)',
            'warning':'Affine generator is an exact two-observation interpolation, not actual Allwyn software. Production seed, reseed behavior and mapping unknown.'}


def main():
    archive=json.loads(Path(__file__).with_name('extra5_multifamily_blind_14250.json').read_text())
    report=evaluate(archive)
    output=Path(__file__).with_name('extra5_two_draw_replay_results.json')
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'both_exact':report['exact_both_draws'],
                      'candidate_count':report['exact_first_draw_seed_candidates'],
                      'toy_third_draw_prediction':report['illustrative_affine_rank_fit'][0]['next_numbers']}))


if __name__ == '__main__':
    main()
