# Initial `aci_simp` audit — 2026-09-28

## Rule contract

An Alethe step has the form:

```lisp
(step t1 (cl (= lhs rhs)) :rule aci_simp)
```

It has no premises or explicit arguments. Equivalence is checked using the
applicable associativity, commutativity, identity, and idempotency properties
of each operator. These properties are operator-specific; for example,
arithmetic addition permits reordering but does not permit duplicate removal.
Constant evaluation is not part of this rule. See
[Alethe rule 118](https://verit.gitlabpages.uliege.be/alethe/specification.pdf#page=57).

For the current QF_UF workload, the relevant operators are `or` and `and`:

```text
(or p (or q p) false) → operands [p, q, p] → set {p, q}
(or q p)             → operands [q, p]    → set {p, q}
                                                    → equal
```

The neutral elements are `false` for `or` and `true` for `and`. Empty results
normalize to the corresponding neutral element; singleton results normalize
to the sole operand.

The local cvc5 producer maps `ACI_NORM` to `aci_simp` in
`cvc5/src/proof/alethe/alethe_post_processor.cpp:2915`. Its normalizer in
`cvc5/src/expr/aci_norm.cpp:150` flattens occurrences of the same outer
operator, keeping subterms headed by other operators opaque. This describes
the local producer's behavior; the specification allows solver-dependent
normalization. Different outer operators also receive special handling in
`isACINorm` at line 215.

## Eunoia at the initial audit

At the initial audit there was no `aci_simp` declaration. The existing
[`$check_ac_simp`](../signature/rules/alethe.eo) always returns `true`, and its
`ac_simp` rule expects the entire equality clause as an explicit argument.
Thus both the checker and its calling convention need attention.

Confirmed with Ethos 0.2.4: this arbitrary equality is accepted by the current
trusted placeholder:

```lisp
(declare-const p Bool)
(declare-const q Bool)
(step bad (@cl (= p q)) :rule ac_simp :args ((@cl (= p q))))
```

## Existing AC branch

Inspected `origin/rules/ac_simp_from_main` at `9204f6248e6275e91d4f81755b1736e78fcc34f5`
in a temporary snapshot. Its `signature/rules/tautologies.eo` contains a real
Boolean `ac_simp` checker, with recursive Boolean normalization and a formula
ordering implementation.

It is not ready to serve as the missing rule:

- The first `aci_simp` step from sample 02 of the previous QF_UF batch still
  fails when run against that branch after changing only its rule name to
  `ac_simp`.
- `(or p (or q r)) = (or r p q)` fails. Evaluation remains stuck in the
  ordering/comparison helpers, including `$less_or_equal_strings`.
- `(or p false) = p` fails with a false side condition.
- `(or p p) = p`, `(or false false) = false`, and `(and true true) = true`
  pass the branch checker.

These are observations with the installed Ethos version, not an exhaustive
test of that branch.

## Carcara reference-checker problems

The current sibling Carcara checkout is `tests`, `8f8b2c9`, with the existing
local translation fixes. The tested binary is
`/tmp/carcara-distinct-arg-list-20260927/target/debug/carcara`.

In `src/checker/rules/simplification.rs:852`, `apply_aci_simp` removes duplicates
for every supported associative operator. At line 835, operand comparison is
unordered for every supported operator except bitvector concatenation,
including string concatenation.

The following invalid equalities were accepted as `aci_simp` steps:

| Left side | Right side | cvc5 on the negated equality |
| --- | --- | --- |
| `(+ i i)` | `i` | `sat` |
| `(* i i)` | `i` | `sat` |
| `(bvxor a a)` | `a` | `sat` |
| `(str.++ x y)` | `(str.++ y x)` | `sat` |
| `(str.++ x x)` | `x` | `sat` |
| `(concat a a b)` | `(concat a b b)` | `sat` |

Here `i` is an integer, `a` and `b` are 4-bit vectors, and `x` and `y` are
strings. Each probe supplies the negated equality as its sole assertion,
uses `aci_simp` to derive the equality, then resolves to the empty clause.
Carcara reports `valid` for these purported refutations of satisfiable inputs.

Carcara also rejects the valid equalities `(or false false) = false` and
`(and true true) = true`. Removing all neutral operands leaves a zero-operand
application in its normalizer instead of returning the neutral constant.

Consequently, the current Carcara checker cannot be the sole oracle for a new
Eunoia implementation.

## Suggested implementation boundary

Implement a checked, premise-free `aci_simp` declaration using
`:conclusion-explicit (@cl (= lhs rhs))`. For QF_UF, flatten each outer `or` or
`and`, remove that operator's neutral element, and compare the remaining
operands as sets, handling empty and singleton results. Keep differently
headed subterms opaque to match the current producer. Preserve the distinction
between an operator's structural nil terminator and an ordinary operand.

Further operator support needs separate policies: multisets for commutative
operators without idempotency, and ordered sequences for concatenation.
Include negative cases from the table above before accepting those theories.

## Test of the revised sketch

The subsequent sketch obtains nil values through `eo::nil`, constructs and
joins operand spines with `eo::cons` and `eo::list_concat`, removes duplicates
with `eo::list_setof`, and compares the results with `eo::list_meq`. Its
`aci_simp` rule enables this treatment for Boolean `or` and `and`.

Tested with the installed Ethos on 2026-09-28:

| Check | Result |
| --- | ---: |
| Focused positive proof steps | 11/11 accepted |
| Negative helper assertions | 7/7 returned false |
| Left/right spine assertions | 3/3 passed |
| Negative applications of the actual rule | 9/9 rejected at `aci_simp` |
| Extracted benchmark `aci_simp` steps | 9,908/9,908 accepted |
| Benchmark files covered | 50/50 |

The negative rule applications cover changed/missing operands, normalization
inside a different operator, mixed-root reordering, absorption, distribution,
XOR duplicate removal, and invalid arithmetic duplicate removal. Some of these
equalities are logically valid but outside this sketch's normalization policy.

All `aci_simp` steps were extracted from the
[50-sample QF_UF batch](qf-uf-50-20260927.md). Their source Alethe counts match
the extracted counts. Original assumptions and other proof steps were omitted;
all extracted steps are premise-free. These results validate the rule
instances, not complete refutations. The runner stops at the first unexpected
result; there were no unexpected outcomes or timeouts.

The tested sketch is `/tmp/eunoia-aci-sketch-20260928/sketch-native.eo`, with
the 21 focused assertions in `test-native.eo`. The extraction/rejection runner,
per-case results, and all Ethos logs are under
`/tmp/eunoia-aci-rule-test-20260928` (`run.py`, `results.json`, `run.log`,
`case-01.eo` through `case-50.eo`, and `reject-*.eo`).

The sketch was loaded as an additional include for these initial tests.

## Production integration

The tested rule is now in [`signature/rules/alethe.eo`](../signature/rules/alethe.eo),
along with `$aci_operands`, `$aci_equal`, and `$check_aci_simp`. Carcara's normal
signature includes expose it without a translator change.

The 21 focused checks are retained in
[`tests/rules/tests_aci_simp.eo`](../tests/rules/tests_aci_simp.eo). Run them from
the repository root with:

```sh
ethos tests/rules/tests_aci_simp.eo
```

Validation through the production signature passed all 21 focused checks,
all 9 expected rule rejections, and all 9,908 extracted benchmark instances
across 50 files. The extracted files use the normal signature includes, with
no prototype include. The existing `tests_distinct.eo` and
`tests_normalize_lists.eo` also passed.

A complete rerun of benchmark case 02 passed its former missing-`aci_simp`
location at line 89 and stopped at the known `and_neg` failure at line 575.
Thus the rule is integrated, while that full proof still does not validate.
Integration results and logs are in `/tmp/eunoia-aci-integration-20260928`,
including `results.json` and `full-case-02.json`.

## Initial audit reproduction artifacts

Artifacts are under `/tmp/eunoia-aci-simp-audit-20260928`:

- `results.json`: 13 Carcara/cvc5 probes, with exact terms and commands.
- Each named case directory: SMT2 input, Alethe proof, and both tools' logs.
- `trusted-ac-simp.eo`: current Eunoia placeholder probe and its logs.
- `branch-results.json`: eight Boolean probes of the AC branch.
- `branch-benchmark-02.eo`: the extracted benchmark step and its Ethos logs.
- `branch/signature`: the inspected branch snapshot.

The integrated rule currently supports Boolean `or` and `and`; other theories
need their own operator policies.
