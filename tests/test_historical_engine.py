"""Local verification of published algorithm components and explicitly assumed wiring.

Run: python -m unittest discover -s tests -v
"""
import itertools
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'experiments'))
from extra5_historical_engine import (
    BBS, RSAParity, ReplayBits, CFBZeroBits, Route, RoutedBits,
    bits_below, mixer_b, mixer_m, naor_reingold_eval,
    xor_physical_sources, sample_five_of_thirty_five,
    derive_demo_bytes, demo_sources,
)
from extra5_published_mixers import mixer_m as original_m, mixer_b as original_b


def binary(value, width):
    return [(value >> bit) & 1 for bit in reversed(range(width))]


class TestDocumentedPrimitives(unittest.TestCase):
    def test_original_m_and_b_exhaustive(self):
        for n in range(2, 8):
            for seq in itertools.product((0, 1), repeat=n):
                x = list(seq)
                self.assertEqual(mixer_b(x), list(original_b(x)))
                for second in itertools.product((0, 1), repeat=n):
                    y = list(second)
                    self.assertEqual(mixer_m(x, y), list(original_m(x, y)))

    def test_m_is_not_always_bit_permutation(self):
        self.assertEqual(mixer_m([0, 0, 1], [0, 0, 1]), [0, 0, 0])

    def test_bbs_modular_squaring(self):
        p, q, seed = 383, 503, 107
        x = (seed * seed) % (p * q)
        source = BBS(p, q, seed)
        for _ in range(512):
            x = pow(x, 2, p*q)
            self.assertEqual(source.bit(), x & 1)

    def test_rsa_modular_exponent(self):
        p, q, exponent, seed = 397, 401, 17, 37
        x = seed
        source = RSAParity(p, q, exponent, seed)
        for _ in range(256):
            x = pow(x, exponent, p*q)
            self.assertEqual(source.bit(), x & 1)

    def test_invalid_number_theory_inputs(self):
        with self.assertRaises(ValueError): BBS(13, 19, 7)
        with self.assertRaises(ValueError): BBS(7, 7, 5)
        with self.assertRaises(ValueError): BBS(15, 19, 7)
        with self.assertRaises(ValueError): BBS(383, 503, 383)
        with self.assertRaises(ValueError): RSAParity(397, 401, 5, 37)
        with self.assertRaises(ValueError): RSAParity(397, 401, 17, 397)

    def test_cfb_reference_by_cipher(self):
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.decrepit.ciphers.algorithms import TripleDES, CAST5
        cases = [
            ('aes192', algorithms.AES(bytes(range(24))), bytes(range(16))),
            ('des', TripleDES(bytes(range(8))*3), bytes(range(8,16))),
            ('cast128', CAST5(bytes(range(16))), bytes(range(8))),
        ]
        for name, algorithm, iv in cases:
            key = algorithm.key[:24] if name == 'aes192' else (bytes(range(8)) if name == 'des' else bytes(range(16)))
            source = CFBZeroBits(name, key, iv)
            observed = bytes(sum(source.bit() << (7 - j) for j in range(8)) for _ in range(60))
            expected = Cipher(algorithm, modes.CFB(iv)).encryptor().update(b'\0' * 60)
            self.assertEqual(observed, expected, name)

    def test_cipher_inputs(self):
        with self.assertRaises(ValueError): CFBZeroBits('aes192', b'k'*16, b'i'*16)
        with self.assertRaises(ValueError): CFBZeroBits('aes192', b'k'*24, b'i'*8)
        with self.assertRaises(ValueError): CFBZeroBits('des', b'k'*7, b'i'*8)
        with self.assertRaises(ValueError): CFBZeroBits('other', b'k'*8, b'i'*8)

    def test_naor_reingold_algebra(self):
        p, q, g = 23, 11, 2
        self.assertEqual(naor_reingold_eval(p, q, g, [3, 2, 5], [1, 0]), pow(2, 6, 23))
        self.assertEqual(naor_reingold_eval(p, q, g, [3, 2, 5], [0, 1]), pow(2, 15 % 11, 23))
        with self.assertRaises(ValueError): naor_reingold_eval(p, q, 5, [3,2,5], [1,0])

    def test_xor_sources(self):
        self.assertEqual(xor_physical_sources(bytes([255, 0]), bytes([85, 1]), bytes([15, 4])), bytes([165, 5]))
        with self.assertRaises(ValueError): xor_physical_sources(b'a', b'ab')

    def test_bad_mixer_input(self):
        with self.assertRaises(ValueError): mixer_m([0,1], [1])
        with self.assertRaises(ValueError): mixer_b([1])
        with self.assertRaises(ValueError): ReplayBits([0,2])


class TestArchitectureHypotheses(unittest.TestCase):
    def test_routes(self):
        testx=[0,1,1,0,1,0,1,0];testy=[1,0,1,1,0,1,1,0]
        outcomes = {'single':testx, 'b':mixer_b(testx),'m':mixer_m(testx,testy),
                    'xor':[x^y for x,y in zip(testx,testy)]}
        for mode,names in [('single',('x',)),('b',('x',)),('m',('x','y')),('xor',('x','y'))]:
            engine=RoutedBits({'x':ReplayBits(testx),'y':ReplayBits(testy)}, Route(mode,names),block_bits=8)
            self.assertEqual([engine.bit() for _ in range(8)],outcomes[mode],mode)

    def test_switch_drops_remaining_buffer(self):
        e=RoutedBits({'x':ReplayBits([0]*8+[1]*8),'y':ReplayBits([1]*8)},Route('single',('x',)),block_bits=8)
        self.assertEqual(e.bit(),0)
        e.configure(Route('single',('y',)))
        self.assertEqual([e.bit() for _ in range(8)],[1]*8)

    def test_rejection_sampler(self):
        stream=ReplayBits([1]*6 + binary(1,6))
        self.assertEqual(bits_below(stream,35),1)
        self.assertEqual(bits_below(ReplayBits([0]*6),35),0)
        with self.assertRaises(ValueError): bits_below(stream,0)

    def test_complete_ticket_with_explicit_ranks(self):
        width_stream = [0]*((35-1).bit_length()+(34-1).bit_length()+(33-1).bit_length()+(32-1).bit_length()+(31-1).bit_length())
        self.assertEqual(sample_five_of_thirty_five(ReplayBits(width_stream),sort_output=False),(1,2,3,4,5))
        self.assertEqual(len(width_stream),28)

    def test_deterministic_full_routes(self):
        profiles=[Route('single',('bbs',)),Route('b',('rsa',)),Route('m',('bbs','aes')),
                  Route('xor',('rsa','des','aes')),Route('xor',('bbs','rsa','des','aes')),
                  Route('single',('cast',))]
        for profile in profiles:
            a=RoutedBits(demo_sources(),profile)
            b=RoutedBits(demo_sources(),profile)
            seq1=[sample_five_of_thirty_five(a) for _ in range(5)]
            seq2=[sample_five_of_thirty_five(b) for _ in range(5)]
            self.assertEqual(seq1,seq2,profile)
            self.assertTrue(all(len(x)==len(set(x))==5 and 1<=min(x)<=max(x)<=35 for x in seq1))

    def test_invalid_routes(self):
        with self.assertRaises(ValueError): Route('m', ('bbs',))
        with self.assertRaises(ValueError): Route('xor', ('bbs',))
        with self.assertRaises(ValueError): Route('xor', ('bbs','bbs'))
        with self.assertRaises(ValueError): RoutedBits(demo_sources(),Route('single',('missing',)))

    def test_demo_seed_domain(self):
        self.assertEqual(derive_demo_bytes('example', 32),derive_demo_bytes('example', 32))
        self.assertNotEqual(derive_demo_bytes('example', 32),derive_demo_bytes('other', 32))


if __name__ == '__main__':
    unittest.main()
