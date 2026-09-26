# Branch inventory

Snapshot: **2026-09-25**. Repository: [Mallku2/AletheInEunoia](https://github.com/Mallku2/AletheInEunoia).
Baseline: local and remote `main` at [`f706426`](https://github.com/Mallku2/AletheInEunoia/commit/f70642671d6d861905cad37bbd5c19b4c54225c5).

This inventory covers **all 60 remote branch heads**, verified with `git ls-remote --heads origin` and refreshed with `git fetch origin`. The only local branch is `main`. `origin/HEAD` is an alias and is not counted. Carcara's branches belong to a separate repository and are outside this inventory.

## How to read this document

- **Merged** means the branch head is an ancestor of current `main`. There are **12 such historical heads**, plus `main` itself. The other **47 heads diverge**.
- Numbers in **History** are **branch-only commits / main-only commits**, from `git rev-list --left-right --count main...origin/BRANCH`. They describe ancestry, not the amount of missing functionality. Ports and conflict resolutions can include equivalent code without including the original branch head.
- **Updated** is the head's committer date. A head can be a merge; summaries also inspect recent non-merge commits and signature/test changes.
- `_from_main` identifies a port, but does **not** guarantee a base equal to today's `main`, independence from other features, or a conflict-free merge. `_independent` variants can also have service dependencies.
- This is a source/history inventory, **not a fresh test certification of every branch**. Test references in a summary describe tests present on that branch. The earlier resolution-merge checks are recorded separately below.

## Latest changes to know about

| Date | Branch / commit | Change |
| --- | --- | --- |
| 2026-09-25 | `services/f_list_equal_mod_commut_and_length` · `7c0641b` | Latest comment cleanup, following `80709b4`: rename `$f_list_length` to `$f_list_count_up_to_nil` and update callers/tests. Counting still includes the nil terminator. |
| 2026-09-24 | `rules/qnt_cnf_from_main` · `40360a8` | Newly discovered remote branch: quantified-CNF rule/helpers and tests, on a base that includes `rules/simple_remaining_rules`. |
| 2026-09-24 | `main` · `f706426` | Commits the two structural RARE normalizers and `tests/programs/tests_normalize_lists.eo`, following the resolution merge. |
| 2026-09-23 | `rules/la_mult_pos_from_main` · `390bfd1` | Makes `$is_rel_op` total with a false fallback. Remote history was rewritten since the previous local tip `f8bf735`. |
| 2026-09-23 | `services/tautology_from_main` · `ff0a62d` | Allows arbitrary premises on `hole`, following the tautology implementation. Remote history was rewritten since the previous local tip `f471182`. |

## Review map

These are useful starting points for organizing further integration, not promises that a branch is ready to merge.

| Area | Starting point | Coordination needed |
| --- | --- | --- |
| Resolution | `rules/fixes_resolution_from_main` | Already merged as `90fa27b`. Both resolution branches normalize conclusions as well as premises; the difference from Carcara's stricter explicit-pivot literal preservation remains. |
| RARE lists | Current `main`; compare `rules/rare_rules` for historical definitions | Current `main` has the structural normalizers. The older RARE branch also contains a large accumulated rule stack. |
| `and_neg` / `and_intro` | `rules/fixes_and_neg_from_main`; `services/and_intro_from_main` | Review complete rule/helper changes. During the resolution merge, its incoming De Morgan helper alone regressed binary `and_neg`; `main` retained the prior helper. |
| AC simplification | `rules/ac_simp_from_main` | The declaration is `ac_simp`; our benchmark failures named `aci_simp`. Name/interface compatibility must be checked before counting this as coverage. |
| List services / contexts | `services/f_list_equal_mod_commut_and_length`, `services/f_list_zip_from_main`, `services/pairs_from_main` | Coordinate helper names and representations. The pairs branch also changes `refl` to take context as an argument; current `main` takes a premise. |
| Quantifier CNF | `rules/qnt_cnf_from_main`; compare `_independent` | New port overlaps existing normalization and quantified-rule work; also contains simple-rule ancestry. |
| Let rules | `rules/bind_let`, `rules/fixes_let` | These are broad stacks. The later branch renames `let_elim` to `let`, which affects the translator interface. |

### Selected branch dependencies

Arrows mean **ancestor branch head → descendant branch head**, checked from Git history. This is ancestry, not an exhaustive list of runtime dependencies.

- `services/f_list_zip_from_main` → `rules/bfun_elim_from_main`.
- `services/f_list_zip_from_main` → `services/pairs_from_main`.
- `rules/remaining_simplify_rules_from_main` → `rules/fixes_or_simplify_from_main`.
- `services/f_list_equal_mod_commut_and_length_independent` → `rules/qnt_join_independent`.
- `rules/simple_remaining_rules` → `rules/la_mult_pos_from_main`, `rules/qnt_cnf_from_main`, `services/tautology_from_main`, and `services/f_list_equal_mod_commut_and_length`.
- `services/f_list_concat_from_main` → `rules/fixes_resolution_from_main` → current `main`.

## Inventory


### Current branch, snapshots, and experiments

| Branch | Head · updated | History | Summary and latest work |
| --- | --- | --- | --- |
| [main](https://github.com/Mallku2/AletheInEunoia/tree/main) | [`f706426`](https://github.com/Mallku2/AletheInEunoia/commit/f70642671d6d861905cad37bbd5c19b4c54225c5) · 2026-09-24 | Current | Current integration branch. `90fa27b` merged the resolution port; `f706426` committed `$normalize_eo_list`, `$normalize_eo_pairwise`, and their regression file. |
| [rules/rare_rules](https://github.com/Mallku2/AletheInEunoia/tree/rules/rare_rules) | [`4747fc3`](https://github.com/Mallku2/AletheInEunoia/commit/4747fc3929f88371a00f0806f8213536a7f25964) · 2026-09-15 | 241 / 42 | Older fixed RARE-rule mechanization. Latest change adds RARE-list value constructors in `signature/theories/theory.eo`; earlier changes adapt Rare 2.0 declarations. Compare with the structural normalizers now on `main` before porting. |
| [performance_tweaks](https://github.com/Mallku2/AletheInEunoia/tree/performance_tweaks) | [`f743a3b`](https://github.com/Mallku2/AletheInEunoia/commit/f743a3b259c819d21cfafed1bfcbf136cafe11da) · 2026-08-21 | 248 / 42 | Free-variable and substitution performance work. Latest fix corrects a bug introduced in `$substitution_apply` by the optimization. Carries a large older rule/RARE stack; isolate the performance changes before integration. |
| [tests](https://github.com/Mallku2/AletheInEunoia/tree/tests) | [`af11ea5`](https://github.com/Mallku2/AletheInEunoia/commit/af11ea5bb5a9c0eea875f7e1071efe43aa0d705b) · 2026-09-23 | 241 / 42 | Older broad testing/integration snapshot. Latest commit is “some testing”; its ancestry includes the older RARE rules and many rule fixes. It is not the current `main` plus only tests. |
| [backup](https://github.com/Mallku2/AletheInEunoia/tree/backup) | [`4d3de89`](https://github.com/Mallku2/AletheInEunoia/commit/4d3de8959d2ff6e08e4770b1cd4b24216bf5c6e0) · 2026-08-07 | 120 / 86 | Historical snapshot of the older RARE development stack. Latest head merges `fixes_and_simplify_extra` into the RARE branch; includes many earlier rule changes. Use as a reference snapshot. |

### Rule ports from main

| Branch | Head · updated | History | Summary and latest work |
| --- | --- | --- | --- |
| [rules/ac_simp_from_main](https://github.com/Mallku2/AletheInEunoia/tree/rules/ac_simp_from_main) | [`9204f62`](https://github.com/Mallku2/AletheInEunoia/commit/9204f6248e6275e91d4f81755b1736e78fcc34f5) · 2026-09-21 | 2 / 95 | Port of AC simplification, formula ordering, commutativity normalization, and tests; also brings list/tree helpers and String typing. Declares `ac_simp`, not the `aci_simp` name emitted in our benchmark certificates. |
| [rules/bfun_elim_from_main](https://github.com/Mallku2/AletheInEunoia/tree/rules/bfun_elim_from_main) | [`bd96c96`](https://github.com/Mallku2/AletheInEunoia/commit/bd96c962d9dd9a5385e348d201483984471f8fe0) · 2026-09-22 | 6 / 95 | Boolean-function elimination checker and tests, plus `$int_exp`. Builds on `services/f_list_zip_from_main` and its list helpers; review that service dependency together with the rule. |
| [rules/fixes_and_neg_from_main](https://github.com/Mallku2/AletheInEunoia/tree/rules/fixes_and_neg_from_main) | [`3b1569f`](https://github.com/Mallku2/AletheInEunoia/commit/3b1569f18ec0f19e04f61fbe4e2c5eb7a9bc75f8) · 2026-09-21 | 1 / 95 | Port of the `and_neg` fix, De Morgan conversion, list helpers, and tests. Review the complete rule/helper change: importing just its helper through the resolution port regressed binary `and_neg`. |
| [rules/fixes_or_simplify_from_main](https://github.com/Mallku2/AletheInEunoia/tree/rules/fixes_or_simplify_from_main) | [`8caf212`](https://github.com/Mallku2/AletheInEunoia/commit/8caf2129b126cdadf6444d798330dfc9951fc07f) · 2026-09-21 | 5 / 95 | Ports `or_simplify` changes and then `not_and` fixes. Contains `remaining_simplify_rules_from_main`; includes the simplifier family and shared list representation changes. |
| [rules/fixes_resolution_from_main](https://github.com/Mallku2/AletheInEunoia/tree/rules/fixes_resolution_from_main) | [`1b8dee4`](https://github.com/Mallku2/AletheInEunoia/commit/1b8dee48da5903b9b05070e871e5b43c9b2be91b) · 2026-09-22 | Merged | Resolution fixes and 66 dedicated checks, including normalization of the conclusion. Merged via `90fa27b` with conflict resolutions; current quantified rules and the existing De Morgan helper were retained. |
| [rules/la_mult_pos_from_main](https://github.com/Mallku2/AletheInEunoia/tree/rules/la_mult_pos_from_main) | [`390bfd1`](https://github.com/Mallku2/AletheInEunoia/commit/390bfd10e9701fd9674342df869cb4b35df1f192) · 2026-09-23 | 7 / 46 | Positive-multiplier arithmetic rule and tests. Latest commit makes `$is_rel_op` total by returning false for other operators. Updated history includes `rules/simple_remaining_rules`; unrelated arithmetic tests were removed. |
| [rules/qnt_cnf_from_main](https://github.com/Mallku2/AletheInEunoia/tree/rules/qnt_cnf_from_main) | [`40360a8`](https://github.com/Mallku2/AletheInEunoia/commit/40360a86d3ed1d8a166a21a18e8b665fb9d65894) · 2026-09-24 | 5 / 46 | New port of quantified CNF conversion and tests: NNF, prenex conversion, distribution, and the `qnt_cnf` checker. Includes `rules/simple_remaining_rules` in its ancestry; inspect the overlap with current quantified rules. |
| [rules/remaining_simplify_rules_from_main](https://github.com/Mallku2/AletheInEunoia/tree/rules/remaining_simplify_rules_from_main) | [`1de9f23`](https://github.com/Mallku2/AletheInEunoia/commit/1de9f23c633e7137fda53bc4201025c14d9967c3) · 2026-09-21 | 2 / 95 | Port of `and`, `ite`, equality, division, unary-minus, minus, sum, and comparison simplifiers with tests. Latest adjustment adapts helper interfaces. Supplies the base for the OR/not-and port. |
| [rules/shuffle_from_main](https://github.com/Mallku2/AletheInEunoia/tree/rules/shuffle_from_main) | [`282ea9a`](https://github.com/Mallku2/AletheInEunoia/commit/282ea9ae8af99af61ff93631c1b3c66579a8a3ea) · 2026-09-21 | 1 / 95 | Clause-shuffle checker and tests, together with shared list services. Narrower than the older `rules/shuffle` stack, but still carries helper changes beyond the rule itself. |
| [rules/weakening_from_main](https://github.com/Mallku2/AletheInEunoia/tree/rules/weakening_from_main) | [`33b15b4`](https://github.com/Mallku2/AletheInEunoia/commit/33b15b45a375a9f62cb74040c2673b0e8ad1304b) · 2026-09-21 | 2 / 95 | Weakening checker and tests, with shared list/flattening helpers. The older branch also contains the previous simplification and clause-rule stack. |

### Service branches and ports

| Branch | Head · updated | History | Summary and latest work |
| --- | --- | --- | --- |
| [services/and_intro_from_main](https://github.com/Mallku2/AletheInEunoia/tree/services/and_intro_from_main) | [`7c29e68`](https://github.com/Mallku2/AletheInEunoia/commit/7c29e686d91fb467c72667c878408730253260fe) · 2026-09-22 | 1 / 95 | Focused `and_intro` checker/rule and tests. Despite the `services/` prefix, its main change is in `signature/rules/alethe.eo`. Relevant to the missing `and_intro` benchmark failure. |
| [services/f_list_concat_from_main](https://github.com/Mallku2/AletheInEunoia/tree/services/f_list_concat_from_main) | [`f92ce3e`](https://github.com/Mallku2/AletheInEunoia/commit/f92ce3e55c6a254a0e40727f64670e46e536c6a7) · 2026-09-22 | Merged | Adds generic `$f_list_concat` and adapts `$varlist_concat` and related helpers. Its head is included through the resolution merge; the merge retained the existing De Morgan helper. |
| [services/f_list_equal_mod_commut](https://github.com/Mallku2/AletheInEunoia/tree/services/f_list_equal_mod_commut) | [`d3afdd4`](https://github.com/Mallku2/AletheInEunoia/commit/d3afdd4838078a5fcc418463357a767697764947) · 2026-08-29 | Merged | Earlier list comparison, counting, nil-conversion, and flattening work. Latest cleanup removes unrelated simplifier content. Head is already in `main`; later comparison work has a separate branch. |
| [services/f_list_equal_mod_commut_and_length](https://github.com/Mallku2/AletheInEunoia/tree/services/f_list_equal_mod_commut_and_length) | [`7c0641b`](https://github.com/Mallku2/AletheInEunoia/commit/7c0641bfcf2f0141f2fc3ee424ce908e629ee627) · 2026-09-25 | 14 / 43 | Latest list-comparison work and flattening tests. Renames `$f_list_length` to `$f_list_count_up_to_nil`, updating callers/tests; latest commit cleans comments. Includes `rules/simple_remaining_rules` ancestry and newer helper changes. |
| [services/f_list_zip_from_main](https://github.com/Mallku2/AletheInEunoia/tree/services/f_list_zip_from_main) | [`ee38b09`](https://github.com/Mallku2/AletheInEunoia/commit/ee38b09c2f62ea96224715c2759ce953d715b08e) · 2026-09-22 | 3 / 95 | Adds `$f_list_zip`, `$f_list_map_zip`, repetition helpers, and list tests. Latest fix adjusts concatenation. Ancestor of both the pairs and Boolean-function elimination ports. |
| [services/pairs_from_main](https://github.com/Mallku2/AletheInEunoia/tree/services/pairs_from_main) | [`54838f6`](https://github.com/Mallku2/AletheInEunoia/commit/54838f6c711d68078f7e361d52c27c77ad409ee4) · 2026-09-22 | 5 / 95 | Adds typed `@Pair`/`@pair` values and projections; updates substitution, contexts, Skolem-variable construction, and tests. Also changes `refl` from `:premises (context)` to `:args (context)`, requiring translator coordination. |
| [services/tautology_from_main](https://github.com/Mallku2/AletheInEunoia/tree/services/tautology_from_main) | [`ff0a62d`](https://github.com/Mallku2/AletheInEunoia/commit/ff0a62ddc93aec6b85a2874079eb25811493c3d9) · 2026-09-23 | 6 / 46 | Tautology checker and tests, followed by a change allowing arbitrary premises on `hole`. Updated ancestry includes `rules/simple_remaining_rules`. Keep the trusted-hole interface change visible when reviewing this port. |

### Independent alternatives

| Branch | Head · updated | History | Summary and latest work |
| --- | --- | --- | --- |
| [rules/qnt_cnf_independent](https://github.com/Mallku2/AletheInEunoia/tree/rules/qnt_cnf_independent) | [`d792745`](https://github.com/Mallku2/AletheInEunoia/commit/d792745ebea911847638f0be6c3423324d9247fc) · 2026-09-17 | 5 / 120 | Separate quantified-CNF implementation and tests, including NNF/prenex/CNF helpers and flattening. Latest work polishes documentation. Compare with the newer `_from_main` port rather than merging both automatically. |
| [rules/qnt_join_independent](https://github.com/Mallku2/AletheInEunoia/tree/rules/qnt_join_independent) | [`b4eeeb6`](https://github.com/Mallku2/AletheInEunoia/commit/b4eeeb6a0cffe1988e4608f2b2d83b42433ec4dc) · 2026-09-17 | 5 / 120 | Quantifier-join rule, checker, and tests. Built on `services/f_list_equal_mod_commut_and_length_independent`. Current `main` already contains a `qnt_join` implementation, so compare the actual differences. |
| [rules/simple_remaining_rules_independent](https://github.com/Mallku2/AletheInEunoia/tree/rules/simple_remaining_rules_independent) | [`b1e8f8a`](https://github.com/Mallku2/AletheInEunoia/commit/b1e8f8a57087d0f2349909517b4065f2307b4216) · 2026-09-17 | 2 / 120 | Small rule implementations/tests: `not_equiv2`, `not_symm`, XOR, equivalence/ITE clauses, and `qnt_simplify`. Latest changes fix documentation; overlaps the older non-independent branch and current `main`. |
| [services/f_list_equal_mod_commut_and_length_independent](https://github.com/Mallku2/AletheInEunoia/tree/services/f_list_equal_mod_commut_and_length_independent) | [`cb0da25`](https://github.com/Mallku2/AletheInEunoia/commit/cb0da2588e28fd4872e7c164ac6e028b97d35fc3) · 2026-09-17 | 4 / 120 | Separate list-service implementation/tests: counting, equality modulo order/repetition, and nil-terminated representation conversions. Base of `qnt_join_independent`; predates the newest count-helper rename. |

### Older rule heads already merged

| Branch | Head · updated | History | Summary and latest work |
| --- | --- | --- | --- |
| [rules/bool_simplify](https://github.com/Mallku2/AletheInEunoia/tree/rules/bool_simplify) | [`5107a40`](https://github.com/Mallku2/AletheInEunoia/commit/5107a403b4631c2c8b450a82c5b0ba2ed2e80c1f) · 2026-06-16 | Merged | Boolean simplification and tests. Latest work improves tautology documentation and expands simplification cases. Historical head already included in `main`. |
| [rules/connective_def](https://github.com/Mallku2/AletheInEunoia/tree/rules/connective_def) | [`b555c46`](https://github.com/Mallku2/AletheInEunoia/commit/b555c46e616cd93c5a949bfa7689214673fa80c4) · 2026-08-04 | Merged | Definitions/checks for Boolean connectives with tests. Latest work completes the implementation and polishes its documentation; historical head is merged. |
| [rules/eq_congruent](https://github.com/Mallku2/AletheInEunoia/tree/rules/eq_congruent) | [`abc2154`](https://github.com/Mallku2/AletheInEunoia/commit/abc21546b3381cb3f04597098b7510896c645f04) · 2026-07-28 | Merged | Congruence rules and predicate-congruence work. Latest commits improve `eq_congruent_pred` documentation. This original head is merged; later predicate fixes remain in a separate branch. |
| [rules/eq_transitive](https://github.com/Mallku2/AletheInEunoia/tree/rules/eq_transitive) | [`c752e53`](https://github.com/Mallku2/AletheInEunoia/commit/c752e5382cd602a220da920963ce9e496953367b) · 2026-08-01 | Merged | Equality-transitivity checker/rule and tests. Latest work improves documentation. Already merged; this is distinct from the separate `trans` helper failure discussed in the benchmark audit. |
| [rules/ite_intro](https://github.com/Mallku2/AletheInEunoia/tree/rules/ite_intro) | [`1a9760c`](https://github.com/Mallku2/AletheInEunoia/commit/1a9760c43acf8a0ffdbd33263b9bc1acbd465fa7) · 2026-08-25 | Merged | ITE-introduction implementation, checks, and documentation. Latest cleanup removes unrelated `qnt_rm_unused` material. Original branch head is merged; `fixes_ite_intro` is a separate later-fix line. |
| [rules/la_generic](https://github.com/Mallku2/AletheInEunoia/tree/rules/la_generic) | [`c399a0d`](https://github.com/Mallku2/AletheInEunoia/commit/c399a0d6e07d8bd0aa9abb9fde431a67de3cdd76) · 2026-01-07 | Merged | Linear-arithmetic combination checker and test suites. Latest changes organize test groups using step IDs. Historical head already merged. |
| [rules/la_mult_neg](https://github.com/Mallku2/AletheInEunoia/tree/rules/la_mult_neg) | [`5612e9c`](https://github.com/Mallku2/AletheInEunoia/commit/5612e9cbde5d85c3405da39a9f0d6eb555ae9619) · 2025-11-20 | Merged | Negative-multiplier arithmetic rule. Latest changes correct type signatures/patterns and polish documentation. Historical head already merged. |
| [rules/onepoint](https://github.com/Mallku2/AletheInEunoia/tree/rules/onepoint) | [`3ee3b5d`](https://github.com/Mallku2/AletheInEunoia/commit/3ee3b5d4ee8c04a47f453bdb5e4a675e6323dc5a) · 2026-08-25 | Merged | One-point quantifier elimination and context checks. Latest cleanup removes unrelated quantifier/ITE material. Head already merged; retain the current implementation when resolving older branch conflicts. |
| [rules/qnt_rm_unused](https://github.com/Mallku2/AletheInEunoia/tree/rules/qnt_rm_unused) | [`9dd2a92`](https://github.com/Mallku2/AletheInEunoia/commit/9dd2a924755802902efdfc6c124184633340adc8) · 2026-09-14 | Merged | Unused quantified-variable removal and tests. Latest head merges an earlier `main`; preceding work polishes documentation. Already included in current `main`. |

### Older divergent rule branches

| Branch | Head · updated | History | Summary and latest work |
| --- | --- | --- | --- |
| [rules/ac_simp](https://github.com/Mallku2/AletheInEunoia/tree/rules/ac_simp) | [`6eae5b6`](https://github.com/Mallku2/AletheInEunoia/commit/6eae5b6064646ea93510640dcf25f38965c3eecb) · 2026-08-19 | 10 / 42 | Older AC-simplification development stack; latest own work fixes comparisons modulo commutativity and adds tests. Head merges the remaining-simplifier branch. Compare the narrower `ac_simp_from_main` port first. |
| [rules/and_intro](https://github.com/Mallku2/AletheInEunoia/tree/rules/and_intro) | [`3b4fe66`](https://github.com/Mallku2/AletheInEunoia/commit/3b4fe66ae69c01e721fdfc3fa37f9bd529fa48bf) · 2026-08-19 | 119 / 42 | Older conjunction-introduction rule/tests on top of the accumulated predicate-congruence and Boolean-function stack. A narrower port exists as `services/and_intro_from_main`. |
| [rules/bfun_elim](https://github.com/Mallku2/AletheInEunoia/tree/rules/bfun_elim) | [`441c2b4`](https://github.com/Mallku2/AletheInEunoia/commit/441c2b4c50460fa5a71eeed5fd1906bdd8dcfb78) · 2026-08-19 | 101 / 42 | Older Boolean-function elimination stack, with list and substitution fixes. Head incorporates the resolution branch. A narrower rule port exists as `bfun_elim_from_main`. |
| [rules/bind_let](https://github.com/Mallku2/AletheInEunoia/tree/rules/bind_let) | [`4cc9e4f`](https://github.com/Mallku2/AletheInEunoia/commit/4cc9e4fa31dadfc139b1da73300a35762d01ddb7) · 2026-08-19 | 201 / 42 | Let-binding congruence, premise checks, tests, and performance work. Latest own work improves performance and code organization; head incorporates `fixes_misc`. Review its context/substitution dependencies. |
| [rules/fixes_ac_simp](https://github.com/Mallku2/AletheInEunoia/tree/rules/fixes_ac_simp) | [`e4c0482`](https://github.com/Mallku2/AletheInEunoia/commit/e4c0482d80978b84bf5801c9e709595e5fbfb080) · 2026-08-01 | 66 / 86 | Older comparator/order fixes for AC simplification. Latest work rewrites `$less_or_equal_formulas` and improves performance. Compare with the AC port and current shared list helpers. |
| [rules/fixes_and_neg](https://github.com/Mallku2/AletheInEunoia/tree/rules/fixes_and_neg) | [`7f86090`](https://github.com/Mallku2/AletheInEunoia/commit/7f860904b8bbc8494eb1f3f61a037b344aa851fb) · 2026-08-19 | 40 / 42 | Older `and_neg` fixes and tests, built on the shuffle/arithmetic stack. The focused alternative is `fixes_and_neg_from_main`; the complete rule change matters alongside its helper changes. |
| [rules/fixes_and_simplify](https://github.com/Mallku2/AletheInEunoia/tree/rules/fixes_and_simplify) | [`7b0cbbb`](https://github.com/Mallku2/AletheInEunoia/commit/7b0cbbb8bfcb8c97968896b815d00e4057aed31b) · 2026-06-06 | 15 / 97 | Early `and_simplify` checker fixes and tests; latest cleanup removes dead test-runner code. Later simplifier branches overlap this work; this historical head is not merged by ancestry. |
| [rules/fixes_and_simplify_extra](https://github.com/Mallku2/AletheInEunoia/tree/rules/fixes_and_simplify_extra) | [`01cc1cd`](https://github.com/Mallku2/AletheInEunoia/commit/01cc1cdff682ca276f44f3dcc4781207fffbc743) · 2026-08-07 | 111 / 86 | Later rewrite of `and_simplify`, including conversion between desugared lists and surface terms for comparison. Head merges let-related work. Broad ancestor of the backup/RARE development stack. |
| [rules/fixes_eq_congruent_pred](https://github.com/Mallku2/AletheInEunoia/tree/rules/fixes_eq_congruent_pred) | [`d14d939`](https://github.com/Mallku2/AletheInEunoia/commit/d14d9398e2bde18901b6fad26cb452d01edcf6f8) · 2026-08-19 | 108 / 42 | Predicate-congruence fixes for actual veriT usage, with substitution/pair changes. Head merges the Boolean-function stack. Compare against current congruence rules before selecting commits. |
| [rules/fixes_hole](https://github.com/Mallku2/AletheInEunoia/tree/rules/fixes_hole) | [`08bed25`](https://github.com/Mallku2/AletheInEunoia/commit/08bed25b12e1914f4dbf4b599aa05ce0443fc9af) · 2026-08-19 | 149 / 42 | Permits arbitrary premises for `hole` and fixes tautology tests; head merges the tautology stack. The focused tautology port also carries the hole-interface change. |
| [rules/fixes_ite_intro](https://github.com/Mallku2/AletheInEunoia/tree/rules/fixes_ite_intro) | [`7ab1b09`](https://github.com/Mallku2/AletheInEunoia/commit/7ab1b09f9aa4c1e1088c90fd6b26aea6dd74dba7) · 2026-04-09 | 21 / 86 | Fixes ITE-subterm retrieval and the order of ITE terms in equalities. Separate from the merged original ITE branch; inspect these targeted fixes against the current checker. |
| [rules/fixes_let](https://github.com/Mallku2/AletheInEunoia/tree/rules/fixes_let) | [`37d0be6`](https://github.com/Mallku2/AletheInEunoia/commit/37d0be6488eb9ed2540e5ee6cf8e3d186b58eec7) · 2026-08-19 | 217 / 42 | Let-elimination fixes, including flipped premise equalities and termination conditions. Latest commits rename `let_elim` to `let`; this affects Carcara rule-name translation. Carries the bind-let and miscellaneous stack. |
| [rules/fixes_misc](https://github.com/Mallku2/AletheInEunoia/tree/rules/fixes_misc) | [`b6b51b6`](https://github.com/Mallku2/AletheInEunoia/commit/b6b51b688e03ab10d6ce6adb8ba9cea6d575da15) · 2026-08-19 | 186 / 42 | Broad collection of Boolean-term construction, `symm`, substitution/pair, and test-runner changes. Latest head merges `fixes_refl`; select individual changes rather than treating it as one small fix. |
| [rules/fixes_not_and](https://github.com/Mallku2/AletheInEunoia/tree/rules/fixes_not_and) | [`e62e625`](https://github.com/Mallku2/AletheInEunoia/commit/e62e6258038d63b5f1f1c655608e305578b5ddf3) · 2026-08-19 | 59 / 42 | Fixes `not_and` comparisons and documentation; head merges the OR-simplification stack. Related changes are included in `fixes_or_simplify_from_main`. |
| [rules/fixes_or_simplify](https://github.com/Mallku2/AletheInEunoia/tree/rules/fixes_or_simplify) | [`814ff8e`](https://github.com/Mallku2/AletheInEunoia/commit/814ff8ec853f67f962b1e250d11f4936b0af3f06) · 2026-08-19 | 50 / 42 | OR-simplification fixes, tests, and documentation, on top of the `and_neg` stack. The focused port also contains subsequent `not_and` fixes. |
| [rules/fixes_refl](https://github.com/Mallku2/AletheInEunoia/tree/rules/fixes_refl) | [`32d02f4`](https://github.com/Mallku2/AletheInEunoia/commit/32d02f489002d785b2c900f050b17d8a6c928147) · 2026-08-19 | 164 / 42 | Latest change makes context an explicit argument to `refl`, alongside earlier pair/substitution work. Current `main` expects a context premise, so this is an alternate interface, not a compatible replacement. |
| [rules/fixes_resolution](https://github.com/Mallku2/AletheInEunoia/tree/rules/fixes_resolution) | [`fd6483c`](https://github.com/Mallku2/AletheInEunoia/commit/fd6483caf8b435d939373b92a49125ec8694c142) · 2026-08-19 | 90 / 42 | Accumulated resolution development branch, including weakening and earlier rule stacks. Conclusion-normalization changes were ported through `_from_main`; this full branch head is not merged. |
| [rules/la_mult_pos](https://github.com/Mallku2/AletheInEunoia/tree/rules/la_mult_pos) | [`6413b79`](https://github.com/Mallku2/AletheInEunoia/commit/6413b79e01fd76aff2e7e6cf0968808df2d0a2a5) · 2026-08-19 | 22 / 42 | Older positive-multiplier arithmetic implementation/tests and aggregate test runner; head merges AC simplification. The updated `_from_main` port includes the latest total `$is_rel_op` change. |
| [rules/qnt_cnf](https://github.com/Mallku2/AletheInEunoia/tree/rules/qnt_cnf) | [`ecf32a6`](https://github.com/Mallku2/AletheInEunoia/commit/ecf32a631badb2cc6e3812a21217f38aa742d991) · 2026-09-21 | 3 / 89 | Earlier quantified-CNF rule, normalization helpers, tests, and documentation fixes. Overlaps the independent implementation and the new `_from_main` port; compare their bases and current quantified-rule code. |
| [rules/qnt_join](https://github.com/Mallku2/AletheInEunoia/tree/rules/qnt_join) | [`a35008d`](https://github.com/Mallku2/AletheInEunoia/commit/a35008d36c1e0d80f0361553bccef0438853be64) · 2026-08-31 | 2 / 96 | Older quantifier-join development/cleanup branch. Its latest work removes the duplicate `qnt_join` definition and unrelated rules; remaining changes from its merge base are mainly list services. Do not infer scope from its name alone. |
| [rules/remaining_simplify_rules](https://github.com/Mallku2/AletheInEunoia/tree/rules/remaining_simplify_rules) | [`115c417`](https://github.com/Mallku2/AletheInEunoia/commit/115c41788ed49cf7fee6fc9a18bc7b5861a6b07b) · 2026-08-31 | 3 / 36 | Older simplifier development/cleanup line. Latest work removes unrelated simple-rule tests and adjusts `qnt_simplify` placement, then merges list services. The `_from_main` port carries the simplifier implementation set explicitly. |
| [rules/shuffle](https://github.com/Mallku2/AletheInEunoia/tree/rules/shuffle) | [`4556ba2`](https://github.com/Mallku2/AletheInEunoia/commit/4556ba29febf14db704cb3e57bc4247ed5bbae37) · 2026-08-19 | 31 / 42 | Clause-permutation checker/tests, on top of the positive-arithmetic stack. Latest own work polishes documentation. A focused `shuffle_from_main` port is available. |
| [rules/simple_remaining_rules](https://github.com/Mallku2/AletheInEunoia/tree/rules/simple_remaining_rules) | [`f8b491b`](https://github.com/Mallku2/AletheInEunoia/commit/f8b491b59af136bca051b6da2f22c37faa8fe6cf) · 2026-09-21 | 3 / 62 | Collection of small remaining rules and tests; latest changes polish rule documentation and test premise names. Now an ancestor of several refreshed ports; overlaps rules already present on current `main`. |
| [rules/tautology](https://github.com/Mallku2/AletheInEunoia/tree/rules/tautology) | [`26c8191`](https://github.com/Mallku2/AletheInEunoia/commit/26c819172cb0cf7c2d5e23c84f2d2113cc6bc55f) · 2026-08-19 | 126 / 42 | Older tautology checker/tests, on top of the conjunction-introduction stack. Compare the focused `services/tautology_from_main` port, including its separate hole change. |
| [rules/weakening](https://github.com/Mallku2/AletheInEunoia/tree/rules/weakening) | [`e19e49b`](https://github.com/Mallku2/AletheInEunoia/commit/e19e49b0f6629a186ab8cefb662d2a722675b0fb) · 2026-08-19 | 66 / 42 | Weakening rule/tests, on top of the not-and/OR/and-neg stack. A narrower `weakening_from_main` port is available; this original head remains divergent. |

## Integration notes for current main

- Resolution merge: [`90fa27b`](https://github.com/Mallku2/AletheInEunoia/commit/90fa27ba5233f4832b9ee9cf9763003ff9eac283), parents `dd85399` and `1b8dee4`. Conflicts were resolved by preserving current quantified-rule implementations and existing tests, removing a duplicate helper, and retaining the existing De Morgan helper to avoid an `and_neg` regression.
- Previously verified for that merge: 66 resolution checks, six extracted failing benchmark resolution steps, list/program suites, and Carcara's RARE/`refl` integration checks. This does not certify complete benchmark refutations or all other branches. The full Alethe suite then stopped at the existing missing string-literal type declaration.
- [`f706426`](https://github.com/Mallku2/AletheInEunoia/commit/f70642671d6d861905cad37bbd5c19b4c54225c5) commits the previously local RARE normalizers/tests. They are now part of the baseline, not pending local edits.

## Refreshing the inventory

```bash
git fetch origin
git for-each-ref --sort=refname \
  --format='%(refname:short) %(objectname:short) %(committerdate:short) %(subject)' \
  refs/heads refs/remotes/origin
```

For a selected branch, inspect ancestry and code separately:

```bash
branch=rules/qnt_cnf_from_main
git rev-list --left-right --count "main...origin/$branch"
git log --first-parent --no-merges -5 "origin/$branch"
git diff --stat "main...origin/$branch"
git diff "main...origin/$branch" -- signature tests
```

The three-dot diff shows changes since the common ancestor. Use `git diff main..origin/BRANCH` to compare complete current trees, and read the actual definitions before deciding whether an older branch contributes missing work. Update this snapshot when branch heads or `main` change.
