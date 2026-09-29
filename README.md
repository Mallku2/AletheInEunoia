# The Alethe Calculus in Eunoia

This repository contains a work-in-progress implementation of the Alethe calculus in Eunoia.

See `docs/introduction.md` for an overview of the differences between the standalone Alethe syntax, and Alethe in Eunoia.

See the `examples/` folder for example proofs in both formats.

Finally, the `signature/` folder contains Eunoia signature files for Alethe.

## Benchmark existing certificates

### Commands

```sh
python3 benchmark.py --help

python3 benchmark.py ../Benchmarks/QF_UF \
  --problem-root ../cvc5/sample/QF_UF \
  --rare-profile qf-uf \
  --elaborate --keep-going --output /tmp/eunoia-qfuf-all

python3 benchmark.py ../Benchmarks/QF_UF \
  --problem-root ../cvc5/sample/QF_UF \
  --rare-profile qf-uf \
  --elaborate --sample 100 --seed 20260929 --workers 10 \
  --output /tmp/eunoia-qfuf
```

### Outputs

| File under `--output` | Contents |
| --- | --- |
| `results.json` | Selection, verdicts, timings, commands, first failure |
| `rules.rare` | RARE rules used (default source: repository `big.rare`) |
| `cases/*/proof.eo` | Translated Eunoia proof |
| `cases/*/translate.log` | Carcara translation diagnostics |
| `cases/*/ethos.log` | Ethos verdict and statistics |
| `cases/*/result.json` | Per-case result |
| `cases/*/elaborate.stdout`, `elaborate.log` | Raw elaboration output, with `--elaborate` |
| `cases/*/elaborated.alethe` | Elaborated certificate, with `--elaborate` |
