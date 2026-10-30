#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# Preserve recorded lock hashes; re-runs must be deterministic or fail.
sha256sum FROZEN_AFFINE3D_models.csv FROZEN_AFFINE3D_future.csv FROZEN_JOINT3D_models.csv FROZEN_JOINT3D_future.csv FROZEN_INTERACTION3D.json > /tmp/extra5_3d_locks_$$.sha
trap 'rm -f /tmp/extra5_3d_locks_$$.sha' EXIT
python prepare.py
g++ -std=c++17 -O3 -march=native affine3d.cpp -o affine3d
./affine3d .
g++ -std=c++17 -O3 -march=native joint_generator3d.cpp -o joint_generator3d
./joint_generator3d . fit
./joint_generator3d . forecast
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python interaction3d.py fit
sha256sum -c /tmp/extra5_3d_locks_$$.sha
python oracle_joint.py
python evaluate.py
python evaluate_joint.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python interaction3d.py evaluate
g++ -std=c++17 -O3 -march=native joint_smoke.cpp -o joint_smoke
./joint_smoke . > all_20160_config_smoke.csv
python smoke_verify.py
python -m unittest -v test_3d.py
printf '\nNOTE: preserved interrupted 48-run affine null calibration is not reexecuted by default.\n'
