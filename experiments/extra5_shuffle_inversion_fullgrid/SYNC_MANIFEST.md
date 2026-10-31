# Full 83-file laboratory synchronized

The original 5,034,451-byte ZIP is stored **losslessly** as 21 numbered Base64 parts in `archive_parts/` because the connector rejected a single large blob.

Run `bash assemble_archive.sh` here to reconstruct, verify and test the original `EXTRA5_ShuffleInvariant_Exact_Inversion_2026_10_30.zip`.

Original archive SHA-256: `c3f02f8c96fe59c34b61e521bf3613a68d531aecb5e02c8dddef726323b37712`.

The archive contains **83 original files** (full results, data, synthetic fixtures, solver instances, code and logs). `MANIFEST.json` lists the individual original file hashes and sizes. Major C++/Python solvers and tests are also directly browsable here.

Research limitations: The production EXTRA 5 RNG has not been recovered; constrained models were ruled out only under stated assumptions, and unresolved/timeout cases remain unresolved. Previous prediction locks and CI are unchanged.
