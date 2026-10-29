#!/usr/bin/env python3
"""Historical eLottery seed/switch/sample research pipeline, not Allwyn software.

Bikos et al. (2023), Cryptography 7(4):54, §§5.2–5.3 describes XOR of
physical entropy, coupon-file binding, Naor–Reingold, four PRNG families,
optional routes (single/B/M/XOR) and verification. Everything in this module
which maps paper components into byte encodings, keys/IVs, route timing,
block sizes, sampling, or commitment serialization is an EXPLICIT ASSUMPTION.

Public, tiny and insecure demonstration parameters; no production keys,
entropy, seeds or actual lottery implementation are known.
"""
from __future__ import annotations
import argparse
import hashlib
import itertools
import json
import math
from dataclasses import dataclass

from extra5_historical_engine import (
    BBS, RSAParity, CFBZeroBits, Route, RoutedBits, bits_below,
    naor_reingold_eval, sample_five_of_thirty_five, xor_physical_sources
)

DOMAIN = b"EXTRA5-ACADEMIC-DEMO-NOT-DEPLOYED-v1\x00"
NAMES = ("bbs", "rsa", "des", "aes")
SAMPLERS = ("sequential", "combination_rank", "distinct_rejection")


def allowed_routes() -> tuple[Route, ...]:
    """31 profiles: 4 single, 4 B, 12 ordered M, 11 XOR groups."""
    return tuple(
        [Route("single", (n,)) for n in NAMES] +
        [Route("b", (n,)) for n in NAMES] +
        [Route("m", p) for p in itertools.permutations(NAMES, 2)] +
        [Route("xor", c) for k in (2, 3, 4)
         for c in itertools.combinations(NAMES, k)]
    )


@dataclass(frozen=True)
class NRKey:
    p: int
    q: int
    g: int
    factors: tuple[int, ...]

    def __post_init__(self):
        if (self.p < 3 or self.q < 3 or (self.p-1) % self.q
                or not 1 < self.g < self.p
                or pow(self.g, self.q, self.p) != 1):
            raise ValueError("invalid declared subgroup")
        if not self.factors or any(type(a) is not int or not 1 <= a < self.q
                                   for a in self.factors):
            raise ValueError("invalid NR factors")

    def evaluate(self, seed: bytes) -> bytes:
        if len(self.factors) != len(seed)*8 + 1:
            raise ValueError("factor count must match all seed bits")
        bits = [(byte >> shift) & 1 for byte in seed
                for shift in range(7, -1, -1)]
        value = naor_reingold_eval(self.p, self.q, self.g,
                                   list(self.factors), bits)
        return value.to_bytes((self.p.bit_length()+7)//8, "big")


def demo_nr_key(length: int = 32) -> NRKey:
    """Public deterministic *toy* NR key (p=23, q=11); no security."""
    if not 1 <= length <= 256:
        raise ValueError("invalid test length")
    count = length*8 + 1
    factors = tuple(1 + b % 10 for b in hashlib.shake_256(
        DOMAIN + b"NR-FACTORS").digest(count))
    return NRKey(23, 11, 2, factors)


def coupon_hash(payload: bytes) -> bytes:
    """SHA256 and canonical coupon bytes are NOT specified in paper."""
    if type(payload) is not bytes:
        raise TypeError("coupon payload must be bytes")
    return hashlib.sha256(payload).digest()


@dataclass(frozen=True)
class SeedInput:
    physical: tuple[bytes, ...] = ()
    prior_state: bytes | None = None

    def merged(self) -> bytes:
        if bool(self.physical) == (self.prior_state is not None):
            raise ValueError("choose fresh entropy OR prior state")
        values = self.physical if self.physical else (self.prior_state,)
        if any(type(x) is not bytes or len(x) != 32 for x in values):
            raise ValueError("demonstration requires 32-byte samples")
        return xor_physical_sources(*values)


@dataclass(frozen=True)
class SeedTrace:
    mixed: bytes
    nr: bytes
    master: bytes


def seed_pipeline(draw_id: int, coupons: bytes, inputs: SeedInput,
                  key: NRKey) -> SeedTrace:
    if type(draw_id) is not int or draw_id < 0 or draw_id >= 2**64:
        raise ValueError("invalid draw ID")
    mixed = xor_physical_sources(inputs.merged(), coupon_hash(coupons))
    nr = key.evaluate(mixed)
    # SHAKE256 expansion is an ILLUSTRATIVE assumption, not a paper KDF.
    master = hashlib.shake_256(DOMAIN + b"MASTER" + draw_id.to_bytes(8,"big")
                                + nr + mixed).digest(64)
    return SeedTrace(mixed, nr, master)


def expand(master: bytes, tag: str, size: int) -> bytes:
    if not master or not tag or not 1 <= size <= 1024:
        raise ValueError("bad expansion parameters")
    tag_bytes = tag.encode("ascii")
    return hashlib.shake_256(DOMAIN + b"EXPAND" + len(tag_bytes).to_bytes(2,"big")
                              + tag_bytes + master).digest(size)


def unit_seed(master: bytes, tag: str, modulus: int) -> int:
    """Tiny illustrative BBS/RSA initialization; not unbiased/secure."""
    for attempt in range(100):
        value = 2 + int.from_bytes(expand(master, tag+str(attempt), 32),
                                   "big") % (modulus-3)
        if math.gcd(value, modulus) == 1:
            return value
    raise RuntimeError("unit seed not found")


def instantiate(master: bytes):
    """Per-draw reset is a hypothesis; real system may continue state."""
    return {
        "bbs": BBS(383, 503, unit_seed(master, "bbs", 383*503)),
        "rsa": RSAParity(397, 401, 17,
                         unit_seed(master, "rsa", 397*401)),
        "des": CFBZeroBits("des", expand(master,"des/key",8),
                          expand(master,"des/iv",8)),
        "aes": CFBZeroBits("aes192",expand(master,"aes/key",24),
                          expand(master,"aes/iv",16)),
    }


def unrank_five(rank: int) -> tuple[int, ...]:
    """Exact bijection [0, C(35,5)) -> lexicographic 5-subsets."""
    if type(rank) is not int or not 0 <= rank < math.comb(35,5):
        raise ValueError("rank out of range")
    output = []
    start, left = 1, 5
    while left:
        for v in range(start, 36):
            count = (math.comb(35-v, left-1)
                     if 35-v >= left-1 else 0)
            if rank < count:
                output.append(v)
                start, left = v+1, left-1
                break
            rank -= count
        else:
            raise AssertionError("combinadic unranking failure")
    return tuple(output)


def sample_ticket(bits, sampler: str) -> tuple[int, ...]:
    """Three *alternative hypotheses*, not recovered lottery mapping."""
    if sampler == "sequential":
        return sample_five_of_thirty_five(bits)
    if sampler == "combination_rank":
        return unrank_five(bits_below(bits,math.comb(35,5)))
    if sampler == "distinct_rejection":
        chosen = set()
        while len(chosen) < 5:
            chosen.add(1 + bits_below(bits,35))
        return tuple(sorted(chosen))
    raise ValueError("unrecognized sampler")


@dataclass(frozen=True)
class DrawSpec:
    draw_id: int
    coupons: bytes
    seeds: SeedInput
    route: Route
    sampler: str = "combination_rank"
    block_bits: int = 256

    def __post_init__(self):
        if self.route not in allowed_routes():
            raise ValueError("not a four-generator documented route")
        if self.sampler not in SAMPLERS or type(self.block_bits) is not int:
            raise ValueError("invalid sampler/bit block")
        if self.block_bits < 8 or self.block_bits % 8:
            raise ValueError("invalid mixer block width")


@dataclass(frozen=True)
class Receipt:
    draw_id: int
    coupon_sha256: str
    route: Route
    sampler: str
    block_bits: int
    numbers: tuple[int, ...]
    seed_checksum: str
    receipt_sha256: str


def draw(spec: DrawSpec, key: NRKey) -> Receipt:
    state = seed_pipeline(spec.draw_id, spec.coupons, spec.seeds, key)
    stream = RoutedBits(instantiate(state.master),
                        spec.route,block_bits=spec.block_bits)
    numbers = sample_ticket(stream,spec.sampler)
    # Not a secure bit-commitment/signature or operator audit record.
    seedcheck = hashlib.sha256(DOMAIN+b"SEED"+state.master).hexdigest()
    obj = dict(draw_id=spec.draw_id, coupons=coupon_hash(spec.coupons).hex(),
               route=[spec.route.operation, *spec.route.names],sampler=spec.sampler,
               block_bits=spec.block_bits,numbers=numbers,seed_checksum=seedcheck)
    receipt_hash = hashlib.sha256(DOMAIN+b"RECEIPT"+
        json.dumps(obj,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return Receipt(spec.draw_id,obj["coupons"],spec.route,spec.sampler,
                   spec.block_bits,numbers,seedcheck,receipt_hash)


def verify(spec: DrawSpec, key: NRKey, receipt: Receipt) -> bool:
    """Reproduce from FULL provided seed inputs, not public draw results."""
    if not isinstance(receipt,Receipt):
        return False
    try:
        return draw(spec,key) == receipt
    except (ValueError,TypeError,OverflowError,RuntimeError):
        return False


def demo_spec(draw_id: int, route: Route | None = None,
              sampler: str = "combination_rank") -> DrawSpec:
    root = hashlib.sha256(DOMAIN+b"FIXTURE"+
                          draw_id.to_bytes(8,"big")).digest()
    return DrawSpec(draw_id,b"PUBLIC-FAKE-COUPONS/"+str(draw_id).encode(),
                    SeedInput(physical=(root,hashlib.sha256(root).digest())),
                    route or Route("m",("bbs","des")),sampler)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--draws",type=int,default=3)
    ap.add_argument("--sampler",choices=SAMPLERS,default="combination_rank")
    args=ap.parse_args()
    if not 1 <= args.draws <= 100: ap.error("draws must be 1..100")
    routes=(Route("m",("bbs","des")),Route("b",("rsa",)),
            Route("xor",("bbs","rsa","des","aes")))
    key=demo_nr_key()
    output=[]
    for i in range(args.draws):
        spec=demo_spec(10000+i,routes[i%3],args.sampler)
        receipt=draw(spec,key)
        output.append(dict(draw_id=receipt.draw_id,numbers=receipt.numbers,
                           route=receipt.route.operation,verified=verify(spec,key,receipt)))
    print(json.dumps({"description":"FAKE FIXTURE ONLY, NOT ALLWYN ALGORITHM",
                      "routes":len(allowed_routes()),"draws":output},indent=2))

if __name__=="__main__":
    main()
