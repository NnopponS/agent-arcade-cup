# Hosted CPU decision benchmark

Manual candidate, not a release or a tournament. Install the adjacent
`kev-model-smoke.workflow.yml` as `.github/workflows/kev-model-smoke.yml`.
For a private repo use included GitHub Actions time only: verify 20 remaining
standard Linux minutes and that paid overage is disabled before dispatch.
Otherwise do not run. No paid/larger runner, hosted inference service, secret,
or non-synthetic match data is required.

| Entry | CPU runtime | File size (approx.) | Source |
| --- | --- | ---: | --- |
| Julia-1 Q8 | llama.cpp SystemOne | 168 MB | [Model file](https://huggingface.co/ggml-org/Julia-1-GGUF/blob/main/Julia-1-Q8_0.gguf), [original release](https://huggingface.co/SupersonicLabs/Julia-1) |
| Laya Q8 | llama.cpp SystemOne | 449 MB | [Model file](https://huggingface.co/ggml-org/Laya-GGUF/blob/main/Laya-Q8_0.gguf), [original project](https://github.com/NandhaKishorM/laya) |
| Kev 0.8B Q8 | llama.cpp SystemOne | 812 MB | [Converted releases](https://huggingface.co/ggml-org/Kev-0.8B-GGUF/tree/main), [original model card](https://huggingface.co/jaredpalmer/kev-0.8b) |
| Kev 4B Q4 | llama.cpp SystemOne | 3.03 GB | [Converted release](https://huggingface.co/ggml-org/Kev-4B-GGUF/blob/main/Kev-4B-Q4_K_M.gguf), [original model card](https://huggingface.co/jaredpalmer/kev-4b) |

The llama.cpp binary and all model files are SHA-256 checked, with fixed
maximum download sizes. See the [pinned CPU release](https://github.com/ggml-org/llama.cpp/releases/expanded_assets/b11429)
and the [native decision endpoint](https://github.com/ggml-org/llama.cpp/pull/29818).
Both Kev entries are quantized, so compare their measured tradeoffs on this
runner, not just parameter counts or the upstream reference precision. The
[Kev 4B converter's source revision](https://huggingface.co/ggml-org/Kev-4B-GGUF/blob/main/.src_sha)
is an [upstream model card-only commit](https://huggingface.co/jaredpalmer/kev-4b/commit/6cfce5c2fa4b4bd64026336ab649c5ca78857d52)
on top of the released v1.0 weights. The 4B reference PyTorch backbone alone
has 9.32 GB of stored files ([Qwen](https://huggingface.co/Qwen/Qwen3.5-4B-Base/tree/main));
this suite does not imply that the BF16 reference can fit here. The Q4 entry
gates on 5 GiB available RAM and at least ~4.2 GB free disk as a preliminary
operating envelope, not an assurance that it'll fit.

Everything runs sequentially using a localhost server and the same scenarios,
prompts, and option-order schedule as the local benchmark. The first
model call, cold startup, and external download are tracked separately from
warmed request timings. Each prompt variant receives 28 warm requests (14
test states × two permutations); these are not 28 independent test states.
The hand-label agreement scores are descriptive. A seeded sweep applies
relative temperature rescaling to already-calibrated probability vectors
and tests abstention by probability margin. It neither calls the models again
nor modifies their installed calibration.

To start on an appropriately provisioned Linux x64 CPU:

```sh
python3 kev-bench/hosted/benchmark.py --workdir /tmp/arcade-kev-smoke \
   --output /tmp/arcade-kev-results.json --model julia-1-q8
```

Remove `--model` for the four-model suite; repeat that flag to select multiple
models. Treat any failure/skip as unknown performance and no benchmark rank.
