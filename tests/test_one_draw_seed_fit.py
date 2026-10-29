import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments'))
from extra5_one_draw_seed_fit import *

class FitTests(unittest.TestCase):
    def test_rank_roundtrip_known(self):
        self.assertEqual(unrank_5of35(rank_5of35(TRAIN)),TRAIN)
    def test_rank_all(self):
        self.assertEqual(len({unrank_5of35(i) for i in range(COMBINATIONS)}),COMBINATIONS)
    def test_bounds(self):
        self.assertRaises(ValueError,unrank_5of35,-1)
        self.assertRaises(ValueError,unrank_5of35,COMBINATIONS)
    def test_determinism(self):
        self.assertEqual(tickets_for_seed(123),tickets_for_seed(123))
    def test_consecutive_stream(self):
        key,iv=seed_to_key_iv(321)
        from cryptography.hazmat.primitives.ciphers import Cipher,algorithms,modes
        raw=Cipher(algorithms.AES(key),modes.CFB(iv)).encryptor().update(bytes(128))
        t1,pos=decode_ticket(raw,0)
        t2,pos=decode_ticket(raw,pos)
        self.assertEqual(tickets_for_seed(321),(t1,t2))
    def test_independent_crypto_reference(self):
        from cryptography.hazmat.primitives.ciphers import Cipher,algorithms,modes
        k,iv=seed_to_key_iv(1)
        a=Cipher(algorithms.AES(k),modes.CFB(iv)).encryptor().update(bytes(32))
        b=Cipher(algorithms.AES(k),modes.CFB(iv)).encryptor()
        self.assertEqual(a,b.update(bytes(16))+b.update(bytes(16)))
    def test_rejection_edge(self):
        first=LIMIT.to_bytes(3,'big')
        second=(COMBINATIONS-1).to_bytes(3,'big')
        ticket,pos=decode_ticket(first+second,0)
        self.assertEqual(pos,6)
        self.assertEqual(ticket,unrank_5of35(COMBINATIONS-1))
    def test_seed_invalid(self):
        self.assertRaises(ValueError,seed_to_key_iv,-1)
        self.assertRaises(ValueError,seed_to_key_iv,2**64)
if __name__=='__main__':unittest.main()
