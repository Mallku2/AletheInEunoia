#!/usr/bin/env python3
"""Seeded differential/mutation checks for RARE lists and distinct.

Requires a current Carcara executable and Ethos. Writes generated inputs, logs,
and a JSON report to --output. No third-party Python packages are needed.
"""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import itertools
import json
from pathlib import Path
import random
import resource
import subprocess
import tempfile


RARE = """(declare-rare-rule distinct-false
 ((T Type) (t T) (xs T :list) (ys T :list) (zs T :list))
 :args (t xs ys zs) :conclusion (= (distinct xs t ys t zs) false))
"""
DECLARATIONS = "\n".join([
    "(declare-sort U 0)", "(declare-sort V 0)",
    *[f"(declare-const {prefix}{i} {sort})"
      for prefix, sort in [("u", "U"), ("v", "V"), ("i", "Int"),
                           ("r", "Real"), ("p", "Bool")]
      for i in range(12)],
    "(declare-fun fu (U) U)", "(declare-fun fv (V) V)",
])
POOLS = {
    "U": ["u0", "u1", "u2", "(fu u0)", "(fu (fu u1))", "(ite p0 u0 u1)"],
    "V": ["v0", "v1", "v2", "(fv v0)", "(ite p0 v1 v2)"],
    "Bool": ["true", "false", "p0", "p1", "(not p0)", "(and p0 p1)",
             "(or p0 false)", "(distinct u0 u1)", "(= u0 u1)"],
    "Int": ["0", "1", "2", "i0", "i1", "(+ i0 1)", "(ite p0 i0 i1)"],
    "Real": ["r0", "r1", "r2", "0.0", "2.0", "0.5", "1.5", "(- 0.5)",
             "(/ 1.0 3.0)", "(+ r0 r1)"],
}
FRESH = {"U": "u11", "V": "v11", "Bool": "p11", "Int": "i11", "Real": "r11"}


def application(op, xs):
    return f"({op} {' '.join(xs)})"


def rare_list(xs):
    return application("rare-list", xs) if xs else "rare-list"


def eo_list(xs):
    return application("eo::List::cons", xs) if xs else "eo::List::nil"


def rare_step(name, t, fragments, operands, rhs="false"):
    args = " ".join([t, *(rare_list(xs) for xs in fragments)])
    return (f'(step {name} (cl (= {application("distinct", operands)} {rhs})) '
            f':rule rare_rewrite :args ("distinct-false" {args}))')


def inequalities(operands):
    return [f"(not (= {x} {y}))" for x, y in itertools.combinations(operands, 2)]


def conjunction(xs):
    return "true" if not xs else xs[0] if len(xs) == 1 else application("and", xs)


class Runner:
    def __init__(self, args):
        self.args = args
        self.output = Path(args.output).resolve()
        self.output.mkdir(parents=True, exist_ok=False)
        self.signature = Path(args.signature).resolve()
        self.problem = self.output / "problem.smt2"
        self.problem.write_text(f"(set-logic ALL)\n{DECLARATIONS}\n(check-sat)\n")
        self.rules = self.output / "rules.rare"
        self.rules.write_text(RARE)
        # Equivalent declarations for direct Eunoia checks, with no SMT commands.
        declarations = DECLARATIONS.replace("(declare-sort U 0)", "(declare-const U Type)")
        declarations = declarations.replace("(declare-sort V 0)", "(declare-const V Type)")
        declarations = declarations.replace("(declare-fun fu (U) U)", "(declare-const fu (-> U U))")
        declarations = declarations.replace("(declare-fun fv (V) V)", "(declare-const fv (-> V V))")
        self.eo_prelude = f'(include "{self.signature}/rules/alethe.eo")\n{declarations}\n'
        self.counts = Counter()
        self.failures = []

    def command(self, cmd, log):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.args.timeout)
            Path(log).write_text(result.stdout + result.stderr)
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired as exc:
            Path(log).write_text(f"TIMEOUT: {exc}")
            return 124, "", "timeout"

    def check(self, name, commands, expected=True, pipeline=True):
        stem = self.output / name
        target = stem.with_suffix(".eo")
        if pipeline:
            source = stem.with_suffix(".alethe")
            source.write_text("\n".join(commands) + "\n")
            code, stdout, stderr = self.command([
                self.args.carcara, "translate", "eunoia", "--eunoia-mech", str(self.signature),
                "--rare-file", str(self.rules), str(source), str(self.problem),
            ], stem.with_suffix(".translation.log"))
            if code != 0:
                # Generated negative cases deliberately remain valid Alethe syntax.
                # A translator failure is a separate result, not an Ethos rejection.
                return {"name": name, "ok": False, "stage": "translation", "code": code,
                        "diagnostic": (stdout + stderr)[-2000:]}
            target.write_text(stdout)
        else:
            target.write_text(self.eo_prelude + "\n".join(commands) + "\n")
        code, stdout, stderr = self.command(
            [self.args.ethos, str(target)], stem.with_suffix(".ethos.log"))
        accepted = code == 0 and "correct" in stdout
        # Ethos deliberately aborts on proof errors. Segfaults, timeouts, and
        # unrelated failures must never be counted as expected rejections.
        rejected = code in (1, -6) and "Error:" in stdout + stderr
        ok = accepted if expected else rejected
        return {"name": name, "ok": ok, "stage": "ethos", "code": code,
                "expected": "accept" if expected else "reject",
                "diagnostic": "" if ok else (stdout + stderr)[-2000:]}

    def record(self, result, category, weight=1):
        self.counts[category] += weight
        if not result["ok"]:
            self.failures.append(result)
            print(f"FAIL {result['name']}: {result['stage']}", flush=True)

    def positive_batch(self, name, commands, pipeline=True):
        result = self.check(name, commands, pipeline=pipeline)
        self.record(result, name, len(commands))
        if not result["ok"]:
            # Independent cases: bisect to save one short, reproducible failure.
            candidates = commands
            while len(candidates) > 1:
                mid = len(candidates) // 2
                left = candidates[:mid]
                probe = self.check(name + "-reduce", left, pipeline=pipeline)
                candidates = candidates[mid:] if probe["ok"] else left
            self.check(name + "-minimal", candidates, pipeline=pipeline)


def fuzz(args):
    rng = random.Random(args.seed)
    run = Runner(args)
    instances = []
    # Include every empty/singleton/two/three-element fragment shape per sort.
    for sort in POOLS:
        for lengths in itertools.product(range(4), repeat=3):
            t = rng.choice(POOLS[sort])
            fragments = [[rng.choice(POOLS[sort]) for _ in range(n)] for n in lengths]
            instances.append((sort, t, fragments))
    for _ in range(args.cases):
        sort = rng.choice(list(POOLS))
        t = rng.choice(POOLS[sort])
        fragments = [[rng.choice(POOLS[sort]) for _ in range(rng.randrange(args.max_fragment + 1))]
                     for _ in range(3)]
        instances.append((sort, t, fragments))
    positive = []
    for i, (sort, t, (xs, ys, zs)) in enumerate(instances):
        operands = xs + [t] + ys + [t] + zs
        positive.append(rare_step(f"rare_{i}", t, [xs, ys, zs], operands))
    for i in range(0, len(positive), 100):
        run.positive_batch(f"rare-valid-{i // 100}", positive[i:i + 100])
    print(f"RARE valid: {len(positive)} cases", flush=True)

    negatives = []
    mutations = ["replace", "insert", "drop", "order", "rhs", "type"]
    for i in range(args.mutations):
        sort, t, fragments = rng.choice(instances)
        fragments = [xs.copy() for xs in fragments]
        xs, ys, zs = fragments
        operands = xs + [t] + ys + [t] + zs
        rhs = "false"
        kind = mutations[i % len(mutations)]
        if kind == "insert":
            operands.insert(rng.randrange(len(operands) + 1), FRESH[sort])
        elif kind == "drop" and len(operands) > 2:
            operands.pop(len(xs))  # Delete one of the two scalar witness positions.
        elif kind == "order" and len(set(operands)) > 1:
            a = rng.randrange(len(operands))
            b = next(j for j, term in enumerate(operands) if term != operands[a])
            operands[a], operands[b] = operands[b], operands[a]
        elif kind == "rhs":
            rhs = "true"
        elif kind == "type":
            other = "U" if sort != "U" else "Bool"
            rng.choice(fragments).append(rng.choice(POOLS[other]))
        else:
            operands[rng.randrange(len(operands))] = FRESH[sort]
        name = f"rare-reject-{kind}-{i}"
        negatives.append((name, [rare_step("bad", t, fragments, operands, rhs)], True))

    elimination = []
    for i in range(max(80, args.cases // 3)):
        sort = rng.choice(list(POOLS))
        operands = [rng.choice(POOLS[sort]) for _ in range(rng.randrange(2, 9))]
        pairs = inequalities(operands)
        rhs = "false" if sort == "Bool" and len(operands) > 2 else conjunction(pairs)
        elimination.append(f'(step elim_{i} (cl (= {application("distinct", operands)} {rhs})) '
                           ':rule distinct_elim)')
    run.positive_batch("elimination-valid", elimination)
    # Use distinct UF variables so deleting a comparison is never redundant.
    for i in range(max(30, args.mutations // 3)):
        operands = [f"u{j}" for j in range(rng.randrange(3, 9))]
        pairs = inequalities(operands)
        kind = ["missing", "wrong-pair", "extra", "rhs"][i % 4]
        if kind == "missing":
            pairs.pop(rng.randrange(len(pairs)))
        elif kind == "wrong-pair":
            pairs[rng.randrange(len(pairs))] = "(not (= u0 u11))"
        elif kind == "extra":
            pairs.append("(not (= u0 u11))")
        rhs = "true" if kind == "rhs" else conjunction(pairs)
        negatives.append((f"elimination-reject-{kind}-{i}", [
            f'(step bad (cl (= {application("distinct", operands)} {rhs})) :rule distinct_elim)'
        ], True))

    def negative(case):
        name, commands, pipeline = case
        return run.check(name, commands, expected=False, pipeline=pipeline)

    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for result in pool.map(negative, negatives):
            run.record(result, "negative-proof-cases")
    print(f"Negative proofs: {len(negatives)} cases", flush=True)

    typing = []
    for i in range(max(160, args.cases)):
        n = rng.randrange(0, 25)
        sort = rng.choice(list(POOLS))
        tagged = [(sort, rng.choice(POOLS[sort])) for _ in range(n)]
        if i % 2 and n >= 2:
            other = rng.choice([s for s in POOLS if s != sort])
            tagged[rng.randrange(n)] = (other, rng.choice(POOLS[other]))
        terms = [term for _, term in tagged]
        same = len({s for s, _ in tagged}) <= 1
        expected = "true" if same else "false"
        typing.append(f'(define sort_{i} () ($same_sort {eo_list(terms)}) :is_eq {expected})')
        expr = application("distinct", terms) if terms else "(_ distinct eo::List::nil)"
        typing.append(f'(define type_{i} () (eo::is_ok (eo::typeof {expr})) :is_eq {expected})')
    # Stress the linear sequence representation; do not quadratically expand it.
    for n in [0, 1, 2, 32, 128, 512]:
        terms = ["u0", "u1", "u2"] * (n // 3) + ["u0"] * (n % 3)
        expr = application("distinct", terms) if terms else "(_ distinct eo::List::nil)"
        typing.append(f'(define long_{n} () {expr} :type Bool '
                      f':is_eq (_ distinct {eo_list(terms)}))')
    run.positive_batch("sort-and-representation-properties", typing, pipeline=False)
    print(f"Type/representation: {len(typing)} assertions", flush=True)

    report = {"seed": args.seed, "arguments": vars(args), "counts": dict(run.counts),
              "total_checks": sum(run.counts.values()), "failures": run.failures,
              "signature_sha256": {str(p.relative_to(run.signature)):
                  hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in run.signature.rglob("*.eo")}}
    (run.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"{report['total_checks']} checks; {len(run.failures)} unexpected results; {run.output}", flush=True)
    return bool(run.failures)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--carcara", required=True)
    parser.add_argument("--ethos", default="ethos")
    parser.add_argument("--signature", default=str(Path(__file__).resolve().parents[1] / "signature"))
    parser.add_argument("--seed", type=int, default=20260927)
    parser.add_argument("--cases", type=int, default=600)
    parser.add_argument("--mutations", type=int, default=240)
    parser.add_argument("--max-fragment", type=int, default=8)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    if args.cases < 0 or args.mutations < 0 or args.max_fragment < 0 or args.jobs < 1 or args.timeout <= 0:
        parser.error("counts must be nonnegative; jobs and timeout must be positive")
    if args.output is None:
        args.output = str(Path(tempfile.mkdtemp(prefix="eunoia-distinct-fuzz-")) / "run")
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    raise SystemExit(fuzz(args))


if __name__ == "__main__":
    main()
