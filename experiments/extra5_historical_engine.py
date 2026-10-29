#!/usr/bin/env python3
"""Research implementation of the historically *published* eLottery RNG building blocks.

NO PRODUCTION ATTRIBUTION. Based on Bikos et al. (2023), Cryptography 7(4):54,
sections 3.2 and 5.3. A 2001-2002 designer CV also names CAST-128. The source
papers do not identify present-day keys, seeds, profiles, mixer block sizes,
bit order, per-draw reseeding, switching instructions or the 5/35 sampler.

Python 3.10+, optional 'cryptography' dependency only for CFB stream sources.
Not suitable for real security, gambling predictions or hardware RNG validation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from typing import Protocol


class BitSource(Protocol):
    def bit(self) -> int: ...


def _valid_bit(value: int) -> bool:
    return type(value) is int and value in (0, 1)


class ReplayBits:
    """Finite known input for tests and documentary reference vectors."""
    def __init__(self, bits: list[int] | tuple[int, ...]):
        if not all(_valid_bit(v) for v in bits):
            raise ValueError("replay input must contain only literal 0/1 integers")
        self._bits = tuple(bits)
        self._offset = 0

    def bit(self) -> int:
        if self._offset == len(self._bits):
            raise EOFError("not enough supplied bits")
        v = self._bits[self._offset]
        self._offset += 1
        return v


def _validate_modulus(p: int, q: int, *, blum: bool = False) -> int:
    if not all(type(v) is int and v > 2 for v in (p, q)) or p == q:
        raise ValueError("p and q must be distinct positive odd primes")
    if p % 2 == 0 or q % 2 == 0:
        raise ValueError("p and q must be odd")
    if blum and (p % 4 != 3 or q % 4 != 3):
        raise ValueError("BBS requires Blum primes p=q=3 modulo 4 (each separately)")
    # This is a research input sanity check, not a primality proof for large keys.
    # In the reference demo small primes are validated deterministically by trial division.
    if max(p, q) <= 1_000_000:
        for v in (p, q):
            if any(v % k == 0 for k in range(3, math.isqrt(v) + 1, 2)):
                raise ValueError("composite modulus factor")
    return p * q


class BBS:
    """x0 = seed^2 mod N; xi+1 = xi^2 mod N; emit least significant bit."""
    def __init__(self, p: int, q: int, seed: int):
        self.modulus = _validate_modulus(p, q, blum=True)
        if type(seed) is not int or not 1 < seed < self.modulus or math.gcd(seed, self.modulus) != 1:
            raise ValueError("seed must be a unit in 2..N-1")
        self.state = pow(seed, 2, self.modulus)

    def bit(self) -> int:
        self.state = pow(self.state, 2, self.modulus)
        return self.state & 1


class RSAParity:
    """Model of RSA/Rabin parity generator x <- x^e mod pq; emit LSB."""
    def __init__(self, p: int, q: int, exponent: int, seed: int):
        self.modulus = _validate_modulus(p, q)
        phi = (p - 1) * (q - 1)
        if type(exponent) is not int or exponent <= 1 or math.gcd(exponent, phi) != 1:
            raise ValueError("exponent must be > 1 and relatively prime to phi(N)")
        if type(seed) is not int or not 1 < seed < self.modulus or math.gcd(seed, self.modulus) != 1:
            raise ValueError("seed must be a unit in 2..N-1")
        self.state, self.exponent = seed, exponent

    def bit(self) -> int:
        self.state = pow(self.state, self.exponent, self.modulus)
        return self.state & 1


class CFBZeroBits:
    """Cipherfeedback stream from encrypting zeros, MSB-first bytes.

    Assumptions: full-block CFB (CFB64/CFB128), continuous state, MSB-first.
    Neither CFB segment size nor bit order is specified in the historical paper.
    'des' uses TripleDES with K1=K2=K3, mathematically equivalent to DES;
    'cast128' uses CAST5 as the alternative historically reported cipher.
    """
    def __init__(self, cipher: str, key: bytes, iv: bytes):
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.decrepit.ciphers.algorithms import CAST5, TripleDES
        if cipher == "aes192":
            if len(key) != 24:
                raise ValueError("AES-192 requires a 24-byte key")
            algorithm = algorithms.AES(key)
        elif cipher == "des":
            if len(key) != 8:
                raise ValueError("DES compatibility requires an 8-byte key")
            algorithm = TripleDES(key * 3)
        elif cipher == "cast128":
            if not 5 <= len(key) <= 16:
                raise ValueError("CAST-128 keys must be 5..16 bytes")
            algorithm = CAST5(key)
        else:
            raise ValueError("supported cipher profiles: aes192, des, cast128")
        if len(iv) != algorithm.block_size // 8:
            raise ValueError("IV length must equal cipher block size")
        self.encryptor = Cipher(algorithm, modes.CFB(iv)).encryptor()
        self._value, self._remaining = 0, 0

    def bit(self) -> int:
        if self._remaining == 0:
            self._value = self.encryptor.update(b"\x00")[0]
            self._remaining = 8
        self._remaining -= 1
        return (self._value >> self._remaining) & 1


def mixer_m(x: list[int], y: list[int]) -> list[int]:
    """Exact bit algorithm M in Bikos et al. (2023) §5.3.5."""
    if len(x) < 2 or len(y) != len(x) or not all(_valid_bit(i) for i in x + y):
        raise ValueError("M requires two equally long binary sequences, at least two bits")
    registers = [x[0], x[1]]
    out = []
    for j in range(2, len(x)):
        i = y[j]
        out.append(registers[i])
        registers[i] = x[j]
    i = y[0]
    out.append(registers[i])
    registers[i] = x[0]
    out.append(registers[y[1]])
    return out


def mixer_b(x: list[int]) -> list[int]:
    """Exact bit algorithm B in Bikos et al. (2023) §5.3.5."""
    if len(x) < 2 or not all(_valid_bit(i) for i in x):
        raise ValueError("B requires a binary sequence of length >= 2")
    registers = [x[0], x[1]]
    out = []
    for j in range(2, len(x)):
        i = x[j]
        out.append(registers[i])
        registers[i] = x[j]
    i = x[0]
    out.append(registers[i])
    registers[i] = x[0]
    out.append(registers[x[1]])
    return out


def xor_physical_sources(*inputs: bytes) -> bytes:
    """Hypothetical entropy-source XOR; NOT a physical entropy conditioner.

    Length must match. Does not check entropy and must not be used as secure KDF.
    """
    if not inputs or not all(len(v) == len(inputs[0]) for v in inputs):
        raise ValueError("physical-source samples must have matching lengths")
    return bytes(_xor_column(column) for column in zip(*inputs))


def _xor_column(values: tuple[int, ...]) -> int:
    acc = 0
    for v in values:
        acc ^= v
    return acc


def naor_reingold_eval(p: int, q: int, g: int, factors: list[int], x: list[int]) -> int:
    """Publication's f_a(x) = g^(a0 * prod_{i:x_i=1} ai) mod p.

    Inputs use documented mathematical notation: factors = [a0, a1,...,an].
    This is a toy algebraic evaluation, NOT a deployment seed-recovery procedure.
    """
    if len(factors) != len(x) + 1 or not all(_valid_bit(v) for v in x):
        raise ValueError("require n input bits and n+1 key exponents")
    if not (p > 2 and q > 1 and (p - 1) % q == 0 and 1 < g < p and pow(g, q, p) == 1):
        raise ValueError("invalid declared subgroup")
    if not all(type(a) is int and 1 <= a < q for a in factors):
        raise ValueError("all a_i must be in [1,q-1]")
    exponent = factors[0]
    for bit_value, a in zip(x, factors[1:]):
        if bit_value:
            exponent = (exponent * a) % q
    return pow(g, exponent, p)


@dataclass(frozen=True)
class Route:
    """Documented family of combining methods, with assumed buffer semantics."""
    operation: str  # single, b, m, xor
    names: tuple[str, ...]

    def __post_init__(self):
        valid_counts = {"single": 1, "b": 1, "m": 2, "xor": None}
        if self.operation not in valid_counts:
            raise ValueError("route must be single/b/m/xor")
        needed = valid_counts[self.operation]
        if needed is not None and len(self.names) != needed:
            raise ValueError("invalid source count for operation")
        if self.operation == "xor" and not 2 <= len(self.names) <= 4:
            raise ValueError("xor route takes 2..4 named generators")
        if len(self.names) != len(set(self.names)) or not all(isinstance(v, str) and v for v in self.names):
            raise ValueError("names must be distinct, nonempty strings")


class RoutedBits:
    """User-controlled combination of underlying generator streams.

    IMPORTANT: mixer block width, alignment, and route switching rules are
    hypotheses, not disclosed historical parameters.
    """
    def __init__(self, sources: dict[str, BitSource], route: Route, block_bits: int = 256):
        if block_bits < 2 or block_bits % 8:
            raise ValueError("block_bits must be a byte-aligned integer >= 8")
        self.sources = dict(sources)
        self.block_bits = block_bits
        self.route = route
        self._buffer: list[int] = []
        self._index = 0
        self.configure(route)

    def configure(self, route: Route):
        if any(name not in self.sources for name in route.names):
            raise ValueError("route uses an unavailable generator")
        self.route = route
        self._buffer = []
        self._index = 0

    def _refill(self):
        n = self.block_bits
        inputs = [[self.sources[name].bit() for _ in range(n)] for name in self.route.names]
        if self.route.operation == "single":
            result = inputs[0]
        elif self.route.operation == "b":
            result = mixer_b(inputs[0])
        elif self.route.operation == "m":
            result = mixer_m(inputs[0], inputs[1])
        else:
            result = [_xor_column(v) for v in zip(*inputs)]
        self._buffer, self._index = result, 0

    def bit(self) -> int:
        if self._index >= len(self._buffer):
            self._refill()
        v = self._buffer[self._index]
        self._index += 1
        return v


def bits_below(source: BitSource, limit: int) -> int:
    """Unbiased rejection for an ideal unbiased bit source; assumption, not source cited."""
    if type(limit) is not int or limit <= 0:
        raise ValueError("bound must be positive integer")
    if limit == 1:
        return 0
    width = (limit - 1).bit_length()
    while True:
        value = 0
        for _ in range(width):
            b = source.bit()
            if not _valid_bit(b):
                raise ValueError("bit source emitted nonbit")
            value = (value << 1) | b
        if value < limit:
            return value


def sample_five_of_thirty_five(source: BitSource, *, sort_output: bool = True) -> tuple[int, ...]:
    """Explicitly HYPOTHETICAL unbiased range conversion: sequential removal.

    To avoid implicit sorting hiding generator order, pass sort_output=False.
    """
    remaining = list(range(1, 36))
    selected = [remaining.pop(bits_below(source, len(remaining))) for _ in range(5)]
    return tuple(sorted(selected) if sort_output else selected)


def derive_demo_bytes(label: str, n: int) -> bytes:
    """PUBLIC, DETERMINISTIC illustrative material. Never treat this as secret!"""
    out = b""
    counter = 0
    while len(out) < n:
        out += hashlib.sha256(b"EXTRA5-EDUCATIONAL-NOT-OPERATOR-v1/" + label.encode() + counter.to_bytes(4, 'big')).digest()
        counter += 1
    return out[:n]


def demo_sources() -> dict[str, BitSource]:
    """Tiny BBS/RSA parameters are deliberately insecure and NOT real keys."""
    return {
        "bbs": BBS(383, 503, 107),
        "rsa": RSAParity(397, 401, 17, 37),
        "des": CFBZeroBits("des", derive_demo_bytes("des/key", 8), derive_demo_bytes("des/iv", 8)),
        "aes": CFBZeroBits("aes192", derive_demo_bytes("aes/key", 24), derive_demo_bytes("aes/iv", 16)),
        "cast": CFBZeroBits("cast128", derive_demo_bytes("cast/key", 16), derive_demo_bytes("cast/iv", 8)),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--operation', choices=['single', 'b', 'm', 'xor'], default='m')
    parser.add_argument('--names', nargs='+', default=['bbs', 'aes'])
    parser.add_argument('--draws', type=int, default=3)
    parser.add_argument('--block-bits', type=int, default=256)
    args = parser.parse_args()
    if not 1 <= args.draws <= 1000:
        parser.error('draw count must be 1..1000')
    sources = demo_sources()
    engine = RoutedBits(sources, Route(args.operation, tuple(args.names)), block_bits=args.block_bits)
    draws = [sample_five_of_thirty_five(engine) for _ in range(args.draws)]
    print(json.dumps({"scope": "illustrative historical algorithm-family reconstruction",
                      "deployment_identified": False, "operator_seed_known": False,
                      "sampler": "assumed unbiased sequential removal",
                      "route": {"operation": args.operation, "sources": args.names},
                      "draws": draws}, indent=2))


if __name__ == '__main__':
    main()
