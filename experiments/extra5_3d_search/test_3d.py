"""Independent structural verification and regression tests for the 3D research archive."""
import csv, hashlib, json, math, unittest
from pathlib import Path
R=Path(__file__).resolve().parent

class Test3D(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    with (R/'train_labeled.csv').open() as f: cls.tr=list(csv.DictReader(f))
    with (R/'sealed/future_labels.csv').open() as f: cls.ev=list(csv.DictReader(f))
    with (R/'FROZEN_JOINT3D_future.csv').open() as f: cls.frozen=list(csv.DictReader(f))
  def test_source_sha(self):
    expected='61fc2a3a57656a8188f7defc422ea5efbb1a33756455a41b97891cf0004c8307'
    self.assertEqual(hashlib.sha256((R/'extra5_2022_2026_authoritative.csv').read_bytes()).hexdigest(),expected)
  def test_split_and_sequence(self):
    self.assertEqual((len(self.tr),len(self.ev)),(2192,1334))
    self.assertEqual([int(r['draw_id']) for r in self.tr+self.ev],list(range(10832,14358)))
  def test_valid_draws(self):
    for r in self.tr+self.ev:
      actual=[int(r['n'+str(i)]) for i in range(1,6)]
      ordered=[int(r['s'+str(i)]) for i in range(1,6)]
      self.assertEqual(sorted(actual),ordered)
      self.assertEqual(len(set(actual)),5)
      self.assertTrue(all(1<=x<=35 for x in actual))
  def test_permutations_all_120(self):
    from prepare import p_rank,p_unrank
    for rank in range(120):self.assertEqual(p_rank(p_unrank(rank)),rank)
    self.assertEqual(len({int(r['perm_rank']) for r in self.tr+self.ev}),120)
  def test_combinadic_rank(self):
    from oracle_joint import fromrank
    # Independent rank recovery by combinatorial counting per sorted tuple.
    for r in self.tr+self.ev:
      s=[int(r['s'+str(i)]) for i in range(1,6)]
      rank=0;low=1
      for j,v in enumerate(s):
        for t in range(low,v):
          if 35-t>=4-j:rank+=math.comb(35-t,4-j)
        low=v+1
      self.assertEqual(rank,int(r['set_rank']))
      self.assertEqual(fromrank(rank),s)
  def test_future_order_labels_excluded(self):
    with (R/'future_features_only.csv').open() as f: header=next(csv.reader(f))
    for key in ('perm_rank','perm_parity','n1','n2','n3','n4','n5'):
      self.assertNotIn(key,header)
  def test_future_predictions_count_and_valid(self):
    self.assertEqual(len(self.frozen),4002)
    from collections import Counter
    self.assertEqual(set(Counter(r['objective'] for r in self.frozen).values()),{1334})
    for r in self.frozen:
      vals=[int(r['n'+str(i)]) for i in range(1,6)]
      self.assertEqual(len(set(vals)),5)
      self.assertTrue(0<=int(r['pred_perm_rank'])<120)
  def test_independent_replay(self):
    from oracle_joint import main
    main()
    self.assertEqual(json.loads((R/'independent_oracle.json').read_text())['mismatches'],0)
  def test_affine_evaluation(self):
    eval=json.loads((R/'evaluation.json').read_text())
    self.assertEqual(len(eval['results']),6)
    self.assertEqual(sum(1 for v in eval['results'] if v['combined_exact_permutation']>11),3)
    self.assertEqual(max(v['combined_exact_permutation'] for v in eval['results']),14)
  def test_joint_evaluation(self):
    x=json.loads((R/'joint_evaluation.json').read_text())
    self.assertEqual([r['combined_four_plus'] for r in x['results']],[2,2,1])
    self.assertEqual(sum(r['combined_joint_four_plus_correct_perm'] for r in x['results']),0)
    self.assertEqual(sum(sum(y['five_exact'] for y in r['yearly']) for r in x['results']),0)
  def test_null_runs(self):
    with (R/'null_48_partial.csv').open() as f: a=list(csv.DictReader(f))
    self.assertGreaterEqual(len(a),40)
    vals=[int(r['max_train_matches']) for r in a]
    self.assertAlmostEqual((1+sum(v>=45 for v in vals))/(len(vals)+1),0.4897959183673469)
  def test_interaction_revised(self):
    x=json.loads((R/'FROZEN_INTERACTION3D.json').read_text())
    self.assertEqual(x['hypotheses'],768)
    self.assertEqual(x['maxT_null_replicates'],1000)
    self.assertAlmostEqual(x['maxT_p'],518/1001)
    e=json.loads((R/'interaction_evaluation.json').read_text())
    self.assertFalse(e['direction_replicated'])
  def test_future_seed_uses_prior_outputs_only(self):
    source=(R/'joint_generator3d.cpp').read_text()
    src=source[source.index('static U seed('):source.index('static U setgen(')]
    self.assertNotIn('r.curset',src)
    self.assertNotIn('r.truth',src)
    self.assertNotIn('r.permr',src)
  def test_full_library_oracle(self):
    o=json.loads((R/'full_library_oracle.json').read_text())
    self.assertEqual(o['cases'],40320)
    self.assertEqual(o['mismatches'],0)
  def test_invalidated_parser_preserved(self):
    invalid=R/'invalidated_parser_run'
    self.assertTrue((invalid/'FROZEN_JOINT3D_models.csv').exists())
    old=(invalid/'FROZEN_JOINT3D_models.csv').read_bytes()
    new=(R/'FROZEN_JOINT3D_models.csv').read_bytes()
    self.assertNotEqual(old,new)

if __name__=='__main__':unittest.main()
