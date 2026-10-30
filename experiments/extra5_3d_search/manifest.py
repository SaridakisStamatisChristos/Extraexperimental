"""Generate portable SHA-256 evidence manifest for all archived research files."""
import hashlib,json,platform,sys
from pathlib import Path
root=Path(__file__).resolve().parent
included=['README.md','REPORT.md','prepare.py','affine3d.cpp','null3d.cpp',
'joint_generator3d.cpp','joint_smoke.cpp','interaction3d.py','oracle_joint.py',
'smoke_verify.py','evaluate.py','evaluate_joint.py','test_3d.py','reproduce.sh',
'extra5_2022_2026_authoritative.csv','source_manifest.json','train_labeled.csv','future_features_only.csv',
'sealed/future_labels.csv','FROZEN_AFFINE3D_models.csv','FROZEN_AFFINE3D_future.csv',
'FROZEN_JOINT3D_models.csv','FROZEN_JOINT3D_future.csv','FROZEN_INTERACTION3D.json',
'evaluation.json','joint_evaluation.json','interaction_evaluation.json',
'null_48_partial.csv','all_20160_config_smoke.csv','full_library_oracle.json',
'independent_oracle.json','reproduce_stdout.log','reproduce_stderr.log',
'invalidated_parser_run/FROZEN_JOINT3D_models.csv',
'invalidated_parser_run/FROZEN_JOINT3D_future.csv',
'invalidated_parser_run/joint_evaluation.json',
'invalidated_parser_run/independent_oracle.json','manifest.py']
manifest={'experiment':'EXTRA5 three-dimensional set x permutation x time',
 'file_count':len(included),'python_version':sys.version,'platform':platform.platform(),
 'n_draws':3526,'train':2192,'heldout':1334,
 'affine_parameter_configs':10368000,'joint_prng_parameter_configs':20160,
 'nonlinear_interactions':768,'full_search_affine_null_reps_completed':48,
 'full_search_affine_null_reps_planned':80,
 'nonlinear_maxT_null_reps':1000,'oracle_fixture_comparisons':40320,
 'regression_tests_passed':15,'claim':'No deployed RNG or predictive advantage identified',
 'files':[]}
for name in included:
  b=(root/name).read_bytes()
  manifest['files'].append({'path':name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
(root/'EVIDENCE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Wrote manifest',len(included),'files')
