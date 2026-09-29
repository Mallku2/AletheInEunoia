# The `rare-list` / `distinct` mismatch before the fix

## The problem in one sentence

A RARE list is a sequence of operands to insert into an application; treating
that sequence as one ordinary Eunoia term loses its meaning for pairwise
operators such as `distinct`.

The problem affects empty, singleton, and nonempty fragments. Empty fragments
make the mismatch especially visible because there is no operand value that
means “insert nothing.”

## A concrete Alethe step

```lisp
(step t1613.t6
  (cl (= @p_2431 false))
  :rule rare_rewrite
  :args ("distinct-false"
         c_4
         (rare-list c_0 c_1 c_2)
         rare-list
         (rare-list c_5)))
```

Assume all `c_i` have an uninterpreted sort `U`. The rule has these parameters
and conclusion:

```lisp
; A direct declaration adaptation, before interpreting RARE list semantics:
(declare-rule distinct-false
  ((@T0 Type)
   (t @T0)
   (xs @T0 :list)
   (ys @T0 :list)
   (zs @T0 :list))
  :args (t xs ys zs)
  :conclusion-explicit
    (@cl (= (distinct xs t ys t zs) false)))
```

Here, bare `rare-list` is the empty-list syntax accepted by Carcara. The step
binds:

```text
t  = c_4
xs = [c_0, c_1, c_2]
ys = []
zs = [c_5]
```

RARE interprets the list parameters by splicing their elements into the
operand sequence:

```text
(distinct xs t ys t zs)
          |
          | insert each list's elements; an empty list inserts nothing
          v
(distinct c_0 c_1 c_2 c_4 c_4 c_5)
          |
          | two operands are the same term, c_4
          v
false
```

In this example, `@p_2431` denotes the assembled `distinct` expression.

## Why an ordinary term cannot represent each fragment

### Empty fragments have no operand identity

For `and` and `or`, an associative fold can use `true` and `false`, respectively,
as neutral elements. `distinct` compares every pair of operands instead of
combining operands into another value of their element sort.

Trying to fill the empty `ys` position with a term changes the application:

| Replacement for `ys` | Problem |
| --- | --- |
| `true` or `false` | A Boolean is not an operand of sort `U`. Even for Boolean operands, it introduces additional comparisons. |
| Some term `u : U` | It introduces another operand and comparisons involving `u`. |
| No operand | This is the required behavior, but it is a sequence operation, not substitution by an ordinary term. |

An empty set of pairwise comparisons does evaluate to `true`. That `true` is
the identity of the **conjunction of comparisons**, not an element of `U` that
can be inserted into `distinct`.

### Nonempty fragments cannot be folded independently

This conversion is also incorrect:

```text
[c_0, c_1, c_2]  ->  (distinct c_0 c_1 c_2)
```

The expression on the right has type `Bool`; it is not a sequence of three
values of type `U`.

Checking each fragment separately would also omit comparisons between
fragments and the scalar operands. The complete sequence must be available
before constructing all pairwise comparisons.

The singleton fragment `[c_5]` must similarly contribute the operand `c_5`.
Replacing it with the result of a singleton distinctness check would discard
that operand and its comparisons with the rest of the sequence.

## Why keeping Eunoia's `:list` annotation was insufficient

Eunoia's `:list` annotation supports list behavior in operator spines and
patterns. Copying the annotation does not supply a translation of Alethe's
explicit `rare-list` arguments into arbitrary operand sequences.

In particular, the mechanical declaration above does not explain how an
argument such as `(rare-list c_0 c_1 c_2)` becomes three operands, or how an
empty argument disappears. The input representation and the rule's use of it
must agree.

This is a representation mismatch with the existing `:pairwise` declaration,
not a limitation preventing Eunoia from expressing pairwise semantics. An
alternative declaration is discussed below.

## Discarded prototype: normalize an assembled sequence

The initial prototype preserved list arguments structurally:

```text
rare-list                 -> eo::List::nil
(rare-list c_0 c_1 c_2)    -> (eo::List::cons c_0 c_1 c_2)
(rare-list c_5)            -> (eo::List::cons c_5)
```

For each application, it assembles list fragments and ordinary operands in
their original order:

```text
xs ++ [t] ++ ys ++ [t] ++ zs
                |
                v
[c_0, c_1, c_2, c_4, c_4, c_5]
                |
                | $normalize_eo_pairwise
                v
conjunction of (distinct operand_i operand_j), for every i < j
```

Empty fragments contribute nothing. Duplicate operands remain: removing the
second `c_4` would destroy the reason this rule concludes `false`.

In that prototype, Carcara dispatched a `distinct` application to
`$normalize_eo_pairwise`. The program accepted a binary comparison operator
as a parameter; it did not itself match on `distinct`. Ordinary associative
applications used the separate `$normalize_eo_list` program. Singleton
elimination was applied after the full result had been assembled.

The generated rule computes its conclusion with `:conclusion`, allowing the
normalizer to construct the term that must match the certificate. It does not
retain the mechanical `:conclusion-explicit` template shown above.

`$normalize_eo_pairwise` and the corresponding Carcara dispatch were removed
after adopting native `:arg-list` support. This section records the prototype
for comparison; it does not describe the current implementation.

**The essential change is to preserve the operand sequence until the enclosing
application determines how to interpret it.**

## Current implementation: preserve `distinct` itself with `:arg-list`

The implementation adopted on 2026-09-27 uses the installed Ethos 0.2.4 support for
the `:arg-list` attribute documented in the
[Ethos manual](https://github.com/cvc5/ethos/blob/main/user_manual.md#argument-list).
This representation avoids our custom pairwise normalizer when instantiating
a RARE rule. The declaration and rule shape are:

```lisp
(declare-parameterized-const distinct ((xs eo::List))
  (eo::requires ($same_sort xs) true Bool)
  :arg-list eo::List::cons)

(declare-rule distinct-false
  ((A Type)
   (t A)
   (xs eo::List :list)
   (ys eo::List :list)
   (zs eo::List :list))
  :args (t xs ys zs)
  :conclusion
    (@cl (= (distinct xs t ys t zs) false)))
```

`$same_sort` checks that all operands have the same type; it does
not expand or normalize the formula. The compiler additionally preserves the
checks that each RARE list parameter contains elements of its declared type.
Those generated requirements are omitted from the rule sketch above.

```text
Surface syntax:  (distinct c_0 c_1 c_2 c_4 c_4 c_5)
                         |
                         | :arg-list packages the operands
                         v
Internal form:   distinct applied to one eo::List containing all six operands
```

Native `:list` handling assembles the fragments using `eo::list_concat`, so
the rule body can retain `(distinct xs t ys t zs)`. The result remains a
`distinct` term over a sequence instead of expanding into a conjunction of
binary comparisons.

`eo::List::cons` is the sequence constructor, not the concatenation service.
For example, `(eo::List::cons a b c)` constructs the sequence `[a, b, c]`.
In a program pattern such as `(eo::List::cons x xs)`, declaring `xs` with
`:list` binds the remaining sequence, so the pattern decomposes the head from
the tail. `eo::list_concat` is the separate operation that joins two sequence
fragments. Eunoia's `:list` splicing can make a `cons` expression look like a
concatenation at the surface, but the two operations have different roles.

The original example, all-empty fragments, and a nonempty middle fragment
passed. Removing the repeated operand or changing the expected operand order
was rejected. Keeping `:conclusion-explicit` failed: the generated concatenation
is evaluatable, so this form needs `:conclusion`.

The production signature and Carcara's `Distinct` case now use this
representation. `distinct_elim` reads the preserved operand list and constructs
pairwise inequalities only when checking that elimination rule. It also handles
the impossibility of more than two distinct Boolean operands.

Empty and singleton whole applications remain `distinct` terms; their truth is
established by rules rather than automatic pairwise desugaring. Ordinary uses
need no explicit list constructor:

```lisp
(distinct true true)
```

Regression coverage is in
[`tests/rules/tests_distinct.eo`](../tests/rules/tests_distinct.eo) and Carcara's
`tests/test_eunoia_rare.rs`, including homogeneous typing, duplicate preservation,
empty fragments, singleton applications, and invalid elimination conclusions.

## Seeded fuzz testing

[`tests/fuzz_distinct.py`](../tests/fuzz_distinct.py) generates Alethe proof
fragments, translates them with Carcara, and checks the result with Ethos. The
expected operand sequences are assembled independently in Python. Negative
cases mutate the conclusion or RARE arguments; they must translate successfully
and then be rejected by Ethos. Separate properties check sorts and preservation
of the operand sequence directly in Eunoia.

```bash
python3 tests/fuzz_distinct.py \
  --carcara /path/to/current/carcara --ethos ethos \
  --seed 20260927 --cases 1200 --mutations 480 --max-fragment 12
```

The runner prints its artifact directory, containing the inputs, translated
proofs, diagnostics, and `report.json`. Failing positive batches are reduced to
a single case. Each run needs a new output directory if `--output` is supplied.

The 2026-09-27 run completed **4,966 checks with no unexpected results**:

| Category | Checks |
| --- | ---: |
| Valid RARE instantiations | 1,520 |
| Valid `distinct_elim` steps | 400 |
| Mutated proofs rejected by Ethos | 640 |
| Sort and representation assertions | 2,406 |

Coverage includes every combination of fragment lengths 0 through 3 for each
of five sorts (`Bool`, `Int`, `Real`, `U`, and `V`), longer random fragments,
nested operands, duplicate and Boolean operands, and sequences up to 512 elements.

The initial smoke run exposed an existing Carcara printer bug: a fractional
Real constant was printed as `/ 1.0 2.0)` instead of `(/ 1.0 2.0)`. The successful
run includes the printer correction and regression fixtures for positive and
negative fractional constants. These are generated proof-fragment tests, not a rerun of the earlier
50 complete cvc5 certificates.
