"""Exact fourth-index/second-parity redundancy for unordered modulo sampling."""
import itertools
import random
import unittest
from inverse_linear import fourth_domain


def joint_domain(nums):
    out=set()
    for perm in itertools.permutations(nums):
        available=list(range(1,36))
        indices=[]
        for value in perm:
            i=available.index(value)
            indices.append(i)
            available.pop(i)
        out.add((indices[1]&1,indices[3]))
    return out


class ParityRedundancyTests(unittest.TestCase):
    def test_joint_domain_is_full_cartesian_product(self):
        rng=random.Random(20261031)
        controls=[(1,2,3,4,5),(31,32,33,34,35),(1,4,9,16,35)]
        controls.extend(tuple(sorted(rng.sample(range(1,36),5))) for _ in range(200))
        for nums in controls:
            fourth=fourth_domain(nums)
            self.assertEqual(joint_domain(nums),{(p,i) for p in (0,1) for i in fourth})

if __name__=='__main__':unittest.main(verbosity=2)
