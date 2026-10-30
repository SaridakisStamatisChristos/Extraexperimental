#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
c++ -std=c++17 -O3 -Wall -Wextra -Werror unordered_attack.cpp -o unordered_attack
python3 prepare_unordered.py >/dev/null
python3 -W error::ResourceWarning -m unittest -v test_reconstruction.py
if [[ "${1:-}" == "--full" ]];then
  python3 sweep_grid.py --max-shift 12 --a-min 1 --a-max 2 --strides 5 6 7 8 --jobs 8
  python3 sweep_grid.py --max-shift 12 --a-min 3 --a-max 4 --strides 5 6 7 8 --jobs 8
  python3 sweep_grid.py --max-shift 12 --a-min 5 --a-max 6 --strides 5 6 7 8 --jobs 8
  python3 sweep_grid.py --max-shift 12 --a-min 7 --a-max 8 --strides 5 6 7 8 --jobs 8
  python3 sweep_grid.py --max-shift 12 --a-min 9 --a-max 10 --strides 5 6 7 8 --jobs 8
  python3 sweep_grid.py --max-shift 12 --a-min 11 --a-max 12 --strides 5 6 7 8 --jobs 8
  python3 sweep_star.py
fi
