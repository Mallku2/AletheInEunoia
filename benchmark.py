#!/usr/bin/env python3
"""Benchmark existing Alethe certificates: Carcara -> Eunoia -> Ethos.

Requires Python 3.9+ and the two executables; uses only the standard library.
See --help and README.md for folder layout and command examples.
"""

import argparse
import asyncio
from collections import Counter
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import random
import re
import shutil
import signal
import subprocess
import sys
import time


REPO = Path(__file__).resolve().parent
RULE_NAME = re.compile(r"\(\s*declare-rare-rule\s+([^\s()]+)")


def positive_int(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return number


def positive_seconds(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("must be a finite positive number")
    return number


def elaboration_pipeline(value):
    passes = value.split(",")
    allowed = {"polyeq", "hole", "local", "uncrowd", "reordering", "sat-refutation"}
    if any(name not in allowed for name in passes):
        raise argparse.ArgumentTypeError("expected comma-separated Carcara elaboration passes")
    return passes


def default_carcara():
    for name in ("carcara", "Carcara"):
        for build in ("debug", "release"):
            candidate = REPO.parent / name / "target" / build / "carcara"
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return str(candidate)
    return "carcara"


def arguments(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("folder", type=Path, help="root containing existing .alethe certificates")
    parser.add_argument("--problem-root", type=Path,
                        help="SMT source root with the same relative paths (default: folder)")
    parser.add_argument("--pattern", action="append",
                        help="recursive certificate glob; repeatable (default: *.alethe)")
    parser.add_argument("--output", type=Path,
                        help="new artifact directory (default: benchmark-results/<UTC timestamp>)")
    parser.add_argument("--carcara", default=default_carcara(), help="Carcara executable")
    parser.add_argument("--ethos", default="ethos", help="Ethos executable")
    parser.add_argument("--signature", type=Path, default=REPO / "signature",
                        help="Eunoia mechanization directory")
    parser.add_argument("--elaborate", action="store_true",
                        help="check/elaborate certificates before translation (e.g. missing pivots)")
    parser.add_argument("--elaboration-pipeline", type=elaboration_pipeline,
                        default="polyeq,local,uncrowd,reordering",
                        help="comma-separated Carcara passes; default excludes hole discharge")
    parser.add_argument("--elaboration-timeout", type=positive_seconds, default=180,
                        help="Carcara elaboration wall limit in seconds (default: 180)")
    parser.add_argument("--rare-file", type=Path, help="RARE definitions passed to Carcara")
    parser.add_argument("--rare-profile", choices=("all", "qf-uf"), default="all",
                        help="qf-uf prunes big.rare to the tested Boolean/UF subset")
    parser.add_argument("--workers", type=positive_int, default=10,
                        help="concurrent pipelines (default: 10)")
    parser.add_argument("--ethos-workers", type=positive_int, default=1,
                        help="concurrent Ethos checks (default: 1, to avoid contention)")
    parser.add_argument("--translation-timeout", type=positive_seconds, default=180,
                        help="Carcara wall limit in seconds (default: 180)")
    parser.add_argument("--ethos-timeout", type=positive_seconds, default=180,
                        help="Ethos wall limit in seconds (default: 180)")
    parser.add_argument("--ethos-stats", action=argparse.BooleanOptionalAction, default=True,
                        help="collect Ethos statistics (default: enabled)")
    parser.add_argument("--sample", type=positive_int, help="select N random certificates")
    parser.add_argument("--seed", type=int, default=0, help="sampling seed (default: 0)")
    failure = parser.add_mutually_exclusive_group()
    failure.add_argument("--fail-fast", dest="fail_fast", action="store_true", default=True,
                         help="stop and cancel running cases on the first failure (default)")
    failure.add_argument("--keep-going", dest="fail_fast", action="store_false",
                         help="process the whole selection despite failures")
    parser.add_argument("--require-complete", action="store_true",
                        help="treat incomplete proofs as failures (default: report separately)")
    args = parser.parse_args(argv)
    for field in ("folder", "signature", "problem_root", "rare_file"):
        value = getattr(args, field)
        if value is not None:
            setattr(args, field, value.expanduser().resolve())
    if not args.folder.is_dir():
        parser.error(f"certificate folder does not exist: {args.folder}")
    if args.problem_root is not None and not args.problem_root.is_dir():
        parser.error(f"problem root does not exist: {args.problem_root}")
    if not (args.signature / "rules" / "alethe.eo").is_file():
        parser.error(f"signature lacks rules/alethe.eo: {args.signature}")
    if args.rare_file is not None and not args.rare_file.is_file():
        parser.error(f"RARE file does not exist: {args.rare_file}")
    if args.rare_profile != "all" and args.rare_file is None:
        parser.error("--rare-profile requires --rare-file")
    for field in ("carcara", "ethos"):
        executable = shutil.which(os.path.expanduser(getattr(args, field)))
        if executable is None:
            parser.error(f"{field} executable not found: {getattr(args, field)}")
        setattr(args, field, str(Path(executable).absolute()))
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    args.output = (args.output or REPO / "benchmark-results" / timestamp).expanduser().resolve()
    if args.output.exists():
        parser.error(f"output directory already exists; choose a new path: {args.output}")
    return args, parser


def discover(args):
    certificates = sorted({path for pattern in (args.pattern or ["*.alethe"])
                           for path in args.folder.rglob(pattern) if path.is_file()})
    if args.sample is not None:
        if args.sample > len(certificates):
            raise ValueError(f"requested {args.sample} samples, found {len(certificates)} certificates")
        certificates = random.Random(args.seed).sample(certificates, args.sample)
    if not certificates:
        raise ValueError("no certificates match the requested patterns")
    return certificates


def problem_path(certificate, folder, problem_root=None):
    """foo.smt2.alethe -> foo.smt2; foo.alethe / foo.proof -> foo.smt2."""
    relative = certificate.relative_to(folder).with_suffix("")
    if relative.suffix != ".smt2":
        relative = relative.with_name(relative.name + ".smt2")
    return (problem_root or folder) / relative


def top_level_forms(source):
    """Split RARE forms without interpreting parentheses inside comments/quotes."""
    depth = 0
    start = None
    quoted = None
    escaped = False
    comment = False
    for index, char in enumerate(source):
        if comment:
            comment = char != "\n"
        elif quoted is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quoted:
                quoted = None
        elif char == ";":
            comment = True
        elif char in ('"', '|'):
            quoted = char
        elif char == "(":
            if depth == 0:
                start = index
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                raise ValueError("unbalanced RARE definitions")
            if depth == 0:
                yield source[start:index + 1]
    if depth or quoted is not None:
        raise ValueError("unterminated RARE definition or quote")


def prepare_rare(args):
    if args.rare_file is None:
        return None, None
    source = args.rare_file.read_text()
    forms = list(top_level_forms(source))
    names = [RULE_NAME.match(form).group(1) for form in forms if RULE_NAME.match(form)]
    if args.rare_profile == "qf-uf":
        selected = [(RULE_NAME.match(form).group(1), form) for form in forms
                    if RULE_NAME.match(form)]
        selected = [(name, form) for name, form in selected
                    if name.startswith(("bool-", "ite-", "eq-", "distinct-"))
                    and name != "distinct-binary-elim"]
        if not selected:
            raise ValueError("no QF_UF RARE rules found")
        names = [name for name, _ in selected]
        source = "\n".join(form for _, form in selected) + "\n"
    destination = args.output / "rules.rare"
    destination.write_text(source)
    return destination, names


def child_limits():
    # Set before spawning processes; no preexec_fn or pipe capture is needed.
    if os.name == "posix":
        import resource
        soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
        desired = 64 * 1024 * 1024
        if hard != resource.RLIM_INFINITY:
            desired = min(desired, hard)
        if soft != resource.RLIM_INFINITY and soft < desired:
            resource.setrlimit(resource.RLIMIT_STACK, (desired, hard))
        _, core_hard = resource.getrlimit(resource.RLIMIT_CORE)
        resource.setrlimit(resource.RLIMIT_CORE, (0, core_hard))


async def stop_process(process):
    def send(kill=False):
        try:
            if os.name == "posix":
                os.killpg(process.pid, signal.SIGKILL if kill else signal.SIGTERM)
            elif kill:
                process.kill()
            else:
                process.terminate()
        except ProcessLookupError:
            pass

    send()
    deadline = time.monotonic() + 2
    while process.poll() is None and time.monotonic() < deadline:
        await asyncio.sleep(0.05)
    # Also kill lingering children in the process group after the parent exits.
    send(kill=True)
    process.wait()


async def run_command(command, timeout, stdout_path, stderr_path=None):
    """Write subprocess output directly to artifacts, avoiding asyncio pipe stalls."""
    started = time.monotonic()
    metadata = {"command": command, "timeout_seconds": timeout}
    with stdout_path.open("wb") as stdout:
        stderr = stderr_path.open("wb") if stderr_path is not None else stdout
        try:
            try:
                process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=stdout,
                                           stderr=stderr, start_new_session=True)
            except OSError as error:
                metadata.update(returncode=None, timed_out=False, error=str(error))
            else:
                timed_out = False
                try:
                    while process.poll() is None:
                        if time.monotonic() - started >= timeout:
                            timed_out = True
                            await stop_process(process)
                            break
                        await asyncio.sleep(0.05)
                except asyncio.CancelledError:
                    await stop_process(process)
                    stderr.write(b"\nCANCELLED\n")
                    raise
                if timed_out:
                    stderr.write(f"\nTIMEOUT after {timeout}s\n".encode())
                metadata.update(returncode=process.returncode, timed_out=timed_out)
        finally:
            if stderr is not stdout:
                stderr.close()
    metadata["wall_seconds"] = round(time.monotonic() - started, 3)
    return metadata


def ethos_verdict(log):
    # Require an exact verdict line, never a substring in an error or statistic.
    verdicts = []
    with log.open(errors="replace") as stream:
        for line in stream:
            value = line.strip()
            if value in ("correct", "incomplete", "incorrect"):
                verdicts.append(value)
    return verdicts[0] if len(verdicts) == 1 else None


def log_tail(path):
    with path.open("rb") as stream:
        stream.seek(max(0, path.stat().st_size - 4096))
        return stream.read().decode(errors="replace").strip()[-2000:]


def failure_detail(path):
    with path.open(errors="replace") as stream:
        for line in stream:
            if re.search(r"A step of rule .* failed|Could not find (?:symbol|rule)|"
                         r"Unexpected conclusion for rule|failed to check|error:", line,
                         flags=re.IGNORECASE):
                return line.strip()[:2000]
    return log_tail(path)


def command_failed(result):
    return result.get("error") or result["timed_out"] or result["returncode"] != 0


def extract_elaborated_proof(raw, destination):
    # Carcara prints a checker status before the proof; it is not Alethe syntax.
    with raw.open("rb") as source, destination.open("wb") as target:
        verdict = source.readline().strip()
        if verdict not in (b"valid", b"holey"):
            raise ValueError(f"unexpected Carcara elaboration verdict: {verdict[:200]!r}")
        shutil.copyfileobj(source, target)
    return verdict.decode("ascii")


async def run_case(index, certificate, args, rare_file, ethos_slots, record):
    case_dir = args.output / "cases" / f"{index:05d}"
    case_dir.mkdir(parents=True)
    problem = problem_path(certificate, args.folder, args.problem_root)
    result = {"id": index, "certificate": str(certificate.relative_to(args.folder)),
              "problem": str(problem), "artifacts": str(case_dir.relative_to(args.output)),
              "stage": "input", "status": "failed"}
    started = time.monotonic()
    try:
        if not problem.is_file():
            result["error"] = f"SMT problem not found: {problem}"
            return result
        counts = Counter()
        with certificate.open(errors="replace") as stream:
            for line in stream:
                counts.update(re.findall(r":rule\s+(rare_rewrite|evaluate|hole)\b", line))
        result["alethe_steps"] = dict(counts)
        proof = certificate
        if args.elaborate:
            result["stage"] = "elaborate"
            command = [args.carcara, "elaborate"]
            if rare_file is not None:
                command.extend(["--rare-file", str(rare_file)])
            command.extend(["--pipeline", *args.elaboration_pipeline,
                            "--", str(certificate), str(problem)])
            elaboration = await run_command(command, args.elaboration_timeout,
                                            case_dir / "elaborate.stdout", case_dir / "elaborate.log")
            result["elaboration"] = elaboration
            if command_failed(elaboration):
                result["error"] = elaboration.get("error") or failure_detail(case_dir / "elaborate.log")
                return result
            proof = case_dir / "elaborated.alethe"
            elaboration["verdict"] = extract_elaborated_proof(case_dir / "elaborate.stdout", proof)
        result["stage"] = "translate"
        command = [args.carcara, "translate", "eunoia", "--eunoia-mech", str(args.signature)]
        if rare_file is not None:
            command.extend(["--rare-file", str(rare_file)])
        command.extend([str(proof), str(problem)])
        translation = await run_command(command, args.translation_timeout,
                                        case_dir / "proof.eo", case_dir / "translate.log")
        result["translation"] = translation
        if command_failed(translation):
            result["error"] = translation.get("error") or failure_detail(case_dir / "translate.log")
            return result
        result["stage"] = "ethos_wait"
        async with ethos_slots:
            result["stage"] = "ethos"
            command = [args.ethos]
            if args.ethos_stats:
                command.append("--stats")
            command.append(str(case_dir / "proof.eo"))
            checking = await run_command(command, args.ethos_timeout, case_dir / "ethos.log")
        result["ethos"] = checking
        verdict = ethos_verdict(case_dir / "ethos.log")
        result["verdict"] = verdict
        if command_failed(checking) or verdict not in ("correct", "incomplete"):
            result["error"] = checking.get("error") or failure_detail(case_dir / "ethos.log")
        elif verdict == "incomplete" and args.require_complete:
            result["error"] = "incomplete proof (--require-complete)"
        else:
            result["status"] = verdict
        return result
    except asyncio.CancelledError:
        result["status"] = "cancelled"
        raise
    except (OSError, ValueError) as error:
        result["error"] = str(error)
        return result
    finally:
        result["wall_seconds"] = round(time.monotonic() - started, 3)
        (case_dir / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        record(result)


def write_json(path, data):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    temporary.replace(path)


async def benchmark(args, certificates, rare_file, rare_names):
    started = time.monotonic()
    report = {"state": "running", "started_at": datetime.now(timezone.utc).isoformat(),
              "config": {name: str(value) if isinstance(value, Path) else value
                         for name, value in vars(args).items()},
              "selected": [str(path.relative_to(args.folder)) for path in certificates],
              "rare_rules": rare_names, "results": [], "first_failure": None}
    stopped = False
    pending = iter(enumerate(certificates, 1))
    active = set()
    ethos_slots = asyncio.Semaphore(args.ethos_workers)

    def checkpoint():
        report["counts"] = dict(Counter(row["status"] for row in report["results"]))
        report["verdict_counts"] = dict(Counter(row["verdict"] for row in report["results"]
                                               if row.get("verdict") is not None))
        report["running"] = sorted(active)
        report["not_started"] = len(certificates) - len(report["results"]) - len(active)
        report["wall_seconds"] = round(time.monotonic() - started, 3)
        report["results"].sort(key=lambda row: row["id"])
        write_json(args.output / "results.json", report)

    def record(result):
        active.discard(result["id"])
        report["results"].append(result)
        if result["status"] == "failed" and report["first_failure"] is None:
            report["first_failure"] = result
        checkpoint()
        print(f"[{len(report['results']):4d}/{len(certificates)}] "
              f"{result['status']:10s} {result['certificate']} "
              f"({result['stage']}, {result['wall_seconds']:.3f}s)", flush=True)

    async def worker():
        nonlocal stopped
        while not stopped:
            item = next(pending, None)
            if item is None:
                return
            active.add(item[0])
            checkpoint()
            result = await run_case(*item, args, rare_file, ethos_slots, record)
            if args.fail_fast and result["status"] == "failed":
                stopped = True

    workers = [asyncio.create_task(worker()) for _ in range(min(args.workers, len(certificates)))]
    checkpoint()
    remaining = set(workers)
    try:
        while remaining:
            done, remaining = await asyncio.wait(remaining, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                task.result()
            if stopped:
                break
        report["state"] = "failed" if report["first_failure"] else "complete"
    except asyncio.CancelledError:
        report["state"] = "interrupted"
        raise
    except Exception:
        report["state"] = "error"
        raise
    finally:
        for task in workers:
            if not task.done():
                task.cancel()
        await asyncio.gather(*workers, return_exceptions=True)
        checkpoint()
    return report


def main(argv=None):
    args, parser = arguments(argv)
    try:
        certificates = discover(args)
        args.output.mkdir(parents=True)
        rare_file, rare_names = prepare_rare(args)
        child_limits()
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(f"Selected {len(certificates)} certificates; workers={args.workers}, "
          f"ethos_workers={args.ethos_workers}\nArtifacts: {args.output}", flush=True)
    try:
        report = asyncio.run(benchmark(args, certificates, rare_file, rare_names))
    except KeyboardInterrupt:
        print(f"Interrupted. Partial results: {args.output / 'results.json'}", file=sys.stderr)
        return 130
    counts = report["counts"]
    print("Summary: " + ", ".join(f"{counts.get(key, 0)} {key}" for key in
                                ("correct", "incomplete", "failed", "cancelled")))
    print(f"Results: {args.output / 'results.json'}")
    if report["first_failure"]:
        failure = report["first_failure"]
        print(f"First failure: {failure['certificate']} ({failure['stage']})\n"
              f"{failure.get('error', 'See the case logs.')}", file=sys.stderr)
    return 1 if report["first_failure"] else 0


if __name__ == "__main__":
    sys.exit(main())
