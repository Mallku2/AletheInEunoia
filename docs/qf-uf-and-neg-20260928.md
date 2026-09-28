# Computed `and_neg` and QF_UF rerun — 2026-09-28

## Implementation

[`signature/rules/alethe.eo`](../signature/rules/alethe.eo) now computes the
complete `and_neg` clause from an explicit conjunction argument:

```text
(and p q r) → (@cl (and p q r) (not p) (not q) (not r))
```

`$negate_conjuncts` traverses the conjunction's operand spine, using a `:list`
tail and stopping at `(eo::nil and Bool)`. It preserves order, duplicates,
nested conjunctions, and explicit `true` operands. The structural terminator
does not contribute an extra `(not true)` literal. Ethos compares the computed
clause with the supplied step conclusion; the rule has no checking program
in `:requires`.

Carcara's `src/translation/eunoia/alethe_2_eunoia.rs` supplies the already
translated first clause literal as the Eunoia argument. Source Alethe steps
continue to have no explicit arguments. The paired Carcara regression test is
`tests/test_eunoia_and_neg.rs`.

## Focused validation

| Check | Result |
| --- | ---: |
| Direct Eunoia proof steps | 9/9 accepted |
| Helper assertions | 5/5 passed |
| Valid Carcara → Ethos cases | 9/9 accepted |
| Invalid or malformed Carcara → Ethos cases | 12/12 rejected |
| Existing `tests_aci_simp.eo` | Passed |

Positive cases include unary conjunctions, explicit `true` and `false`, nested
conjunctions, repeated operands, and negated operands. Rejections cover wrong
or atomic heads, an empty clause, changed signs, missing/extra/changed/reordered
literals, removed duplicates or explicit `true`, negating the structural
terminator, and flattening a nested operand.

Run the focused tests from the respective repository roots:

```sh
# AletheInEunoia
ethos tests/rules/tests_and_neg.eo
ethos tests/rules/tests_aci_simp.eo

# Carcara
ulimit -c 0
ALETHE_EUNOIA_SIGNATURE=/home/caotic/Workspace/AletheInEunoia/signature \
ETHOS=/home/caotic/.local/bin/ethos \
cargo test --offline --test test_eunoia_and_neg -- --ignored --nocapture
```

## Same 50 QF_UF samples

This rerun uses the [previous selection](qf-uf-samples-20260927.json), seed
20260927, and reuses its cvc5 `dsl-rewrite` Alethe certificates. Certificates
were not regenerated. All 50 were translated again using the updated Carcara
and current production signature, with the same 51-rule QF_UF subset of
`big.rare`. The [original report](qf-uf-50-20260927.md) records generation and
selection details.

| Stage | Result |
| --- | ---: |
| Carcara translation | 50/50 passed |
| Final translated step concludes `@empty_cl` | 50/50 |
| Isolated `and_neg` checks | 50/50 files passed |
| Individual `and_neg` steps accepted | 57,810/57,810 |
| Complete Ethos proof checks | 0/50 passed |

The full checks reach these first failures:

| First failure | Files | Example |
| --- | ---: | --- |
| `not_and`: failed side condition | 21 | Case 01, `gensys_icl432.smt2` |
| `trans`: stuck evaluation | 13 | Case 02, `iso_icl353.smt2` |
| `evaluate`: missing Eunoia rule | 16 | Case 08, `iso_brn942.smt2` |

There were no translation failures, timeouts, or isolated `and_neg` failures.
These are first-error counts; a proof may contain further issues after its
first failure. The isolated checks omit assumptions and other proof steps,
retain the declarations, and include every premise-free `and_neg` instance.
Extracted counts match the original Alethe counts. Their success validates
those rule instances, not complete refutations.

Ethos was invoked without `--require-proof-of-false`; the translated final
empty clause was checked separately. None of the full files passed Ethos.

## Results and artifacts

- [Per-case CSV](qf-uf-and-neg-results-20260928.csv).
- Logs, generated proofs, isolated checks, driver, manifests and paired
  Carcara patch: `/tmp/eunoia-qfuf-50-and-neg-20260928`.
- Original inputs/certificates: `/tmp/eunoia-qfuf-50-20260927/cases`.
- Tested Carcara build: `/tmp/carcara-distinct-arg-list-20260927/target/debug/carcara`.
- Ethos: `/home/caotic/.local/bin/ethos` (0.2.4).

`manifest.json` records binary/signature/rule hashes, four workers, a 64 MiB
stack, and timeouts of 180 seconds for translation and 90 seconds for Ethos.
Each case records its cached certificate hash. The tested Carcara changes are
also applied to the sibling checkout at `/home/caotic/Workspace/carcara`.
