"""Regression checks for benchmark verdicts, selection, and process cleanup."""

import asyncio
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import benchmark


CARCARA_STUB = """#!/usr/bin/env python3
from pathlib import Path
import sys
mode = Path(sys.argv[-2]).read_text().strip()
if sys.argv[1] == 'elaborate':
    if mode == 'elaboration-fail':
        print('error: deliberate elaboration failure', file=sys.stderr)
        sys.exit(8)
    print('holey' if mode == 'incomplete' else 'valid')
    print(mode)
    sys.exit(0)
if mode == 'translation-fail':
    print('error: deliberate translation failure', file=sys.stderr)
    sys.exit(7)
print(mode)
"""

ETHOS_STUB = """#!/usr/bin/env python3
from pathlib import Path
import os
import sys
import time
mode = Path(sys.argv[-1]).read_text().strip()
if mode == 'slow':
    print('PID=' + str(os.getpid()), flush=True)
    time.sleep(60)
    print('correct')
elif mode == 'delayed-fail':
    time.sleep(0.2)
    print('proof.eo:2.3: A step of rule resolution failed')
    sys.exit(1)
elif mode == 'bogus':
    print('statistics: correct=17, incomplete=2')
elif mode == 'wrong-exit':
    print('correct')
    sys.exit(3)
else:
    print(mode)
"""


class BenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="benchmark test ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.certificates = self.root / "certificates"
        self.problems = self.root / "SMT problems"
        self.certificates.mkdir()
        self.problems.mkdir()
        self.tools = self.root / "tool paths"
        self.tools.mkdir()
        for name, source in (("carcara", CARCARA_STUB), ("ethos", ETHOS_STUB)):
            executable = self.tools / name
            executable.write_text(source)
            executable.chmod(0o755)
        self.run_number = 0

    def case(self, name, mode="correct", problem=True):
        certificate = self.certificates / name
        certificate.parent.mkdir(parents=True, exist_ok=True)
        certificate.write_text(mode + "\n")
        if problem:
            source = benchmark.problem_path(certificate, self.certificates, self.problems)
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text("(set-logic QF_UF)\n(check-sat)\n")
        return certificate

    def run_benchmark(self, *options, expected=0):
        self.run_number += 1
        output = self.root / f"run {self.run_number}"
        completed = subprocess.run([
            sys.executable, str(benchmark.REPO / "benchmark.py"), str(self.certificates),
            "--problem-root", str(self.problems), "--output", str(output),
            "--carcara", str(self.tools / "carcara"), "--ethos", str(self.tools / "ethos"),
            *options,
        ], capture_output=True, text=True, timeout=15, cwd=self.root)
        self.assertEqual(completed.returncode, expected, completed.stdout + completed.stderr)
        return json.loads((output / "results.json").read_text()), output

    def test_default_rare_file_is_bundled(self):
        self.case("a.alethe")
        report, output = self.run_benchmark()
        bundled = benchmark.REPO / "big.rare"
        self.assertEqual(report["config"]["rare_file"], str(bundled))
        self.assertEqual((output / "rules.rare").read_bytes(), bundled.read_bytes())
        command = report["results"][0]["translation"]["command"]
        self.assertEqual(command[command.index("--rare-file") + 1], str(output / "rules.rare"))

    def test_nested_paths_and_incomplete_policy(self):
        self.case("nested/a.smt2.alethe")
        self.case("nested/b.alethe", "incomplete")
        report, output = self.run_benchmark()
        self.assertEqual(report["counts"], {"correct": 1, "incomplete": 1})
        self.assertEqual(report["state"], "complete")
        self.assertEqual(report["running"], [])
        self.assertEqual(report["not_started"], 0)
        self.assertTrue((output / "cases/00001/proof.eo").is_file())
        self.assertTrue((output / "cases/00002/ethos.log").is_file())
        strict, _ = self.run_benchmark("--require-complete", "--keep-going", expected=1)
        self.assertEqual(strict["counts"], {"correct": 1, "failed": 1})
        self.assertEqual(strict["verdict_counts"], {"correct": 1, "incomplete": 1})

    def test_rejects_missing_verdict_incorrect_and_nonzero_exit(self):
        for name, mode in (("a", "bogus"), ("b", "incorrect"), ("c", "wrong-exit")):
            self.case(name + ".alethe", mode)
        report, _ = self.run_benchmark("--keep-going", expected=1)
        self.assertEqual(report["counts"], {"failed": 3})
        self.assertEqual([row["verdict"] for row in report["results"]],
                         [None, "incorrect", "correct"])

    def test_translation_failure_stops_before_ethos(self):
        self.case("a.alethe", "translation-fail")
        self.case("b.alethe")
        report, output = self.run_benchmark("--workers", "1", expected=1)
        self.assertEqual(report["first_failure"]["stage"], "translate")
        self.assertEqual(report["first_failure"]["translation"]["returncode"], 7)
        self.assertEqual(report["not_started"], 1)
        self.assertFalse((output / "cases/00001/ethos.log").exists())

    def test_missing_problem_is_reported(self):
        self.case("a.alethe", problem=False)
        report, _ = self.run_benchmark(expected=1)
        self.assertEqual(report["first_failure"]["stage"], "input")
        self.assertIn("SMT problem not found", report["first_failure"]["error"])

    def test_elaboration_strips_checker_status(self):
        self.case("a.alethe")
        self.case("b.alethe", "incomplete")
        report, output = self.run_benchmark("--elaborate")
        self.assertEqual(report["counts"], {"correct": 1, "incomplete": 1})
        self.assertEqual([row["elaboration"]["verdict"] for row in report["results"]],
                         ["valid", "holey"])
        self.assertEqual((output / "cases/00001/elaborated.alethe").read_text(), "correct\n")
        self.assertTrue(report["results"][0]["translation"]["command"][-2]
                        .endswith("elaborated.alethe"))

    def test_elaboration_failure_is_separate(self):
        self.case("a.alethe", "elaboration-fail")
        report, _ = self.run_benchmark("--elaborate", expected=1)
        self.assertEqual(report["first_failure"]["stage"], "elaborate")
        self.assertNotIn("translation", report["first_failure"])

    def test_sampling_is_reproducible_and_globs_deduplicate(self):
        for i in range(5):
            self.case(f"nested/{i}.smt2.alethe")
        options = ("--sample", "3", "--seed", "42", "--pattern", "*.alethe",
                   "--pattern", "*.smt2.alethe")
        first, _ = self.run_benchmark(*options)
        second, _ = self.run_benchmark(*options)
        self.assertEqual(first["selected"], second["selected"])
        self.assertEqual(len(first["selected"]), 3)

    def test_timeout_is_failure_and_process_is_reaped(self):
        self.case("a.alethe", "slow")
        report, output = self.run_benchmark("--ethos-timeout", "0.25", expected=1)
        result = report["first_failure"]
        self.assertTrue(result["ethos"]["timed_out"])
        self.assertLess(result["ethos"]["wall_seconds"], 5)
        self.assertIsNone(result["verdict"])
        self.assert_process_stopped(output / "cases/00001/ethos.log")

    def test_fail_fast_cancels_a_running_process(self):
        self.case("a.alethe", "delayed-fail")
        self.case("b.alethe", "slow")
        report, output = self.run_benchmark("--workers", "2", "--ethos-workers", "2",
                                          expected=1)
        self.assertEqual(report["counts"], {"failed": 1, "cancelled": 1})
        self.assertEqual(report["first_failure"]["certificate"], "a.alethe")
        self.assertIn("resolution failed", report["first_failure"]["error"])
        self.assertEqual(report["running"], [])
        self.assert_process_stopped(output / "cases/00002/ethos.log")

    @unittest.skipUnless(os.name == "posix", "uses SIGINT")
    def test_interrupt_saves_partial_results_and_stops_checker(self):
        self.case("a.alethe", "slow")
        output = self.root / "interrupted run"
        with tempfile.TemporaryFile() as console:
            process = subprocess.Popen([
                sys.executable, str(benchmark.REPO / "benchmark.py"), str(self.certificates),
                "--problem-root", str(self.problems), "--output", str(output),
                "--carcara", str(self.tools / "carcara"), "--ethos", str(self.tools / "ethos"),
            ], stdin=subprocess.DEVNULL, stdout=console, stderr=console)
            try:
                log = output / "cases/00001/ethos.log"
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline:
                    if log.exists() and "PID=" in log.read_text():
                        break
                    time.sleep(0.02)
                else:
                    self.fail("checker did not start")
                process.send_signal(signal.SIGINT)
                self.assertEqual(process.wait(timeout=5), 130)
                report = json.loads((output / "results.json").read_text())
                self.assertEqual(report["state"], "interrupted")
                self.assertEqual(report["counts"], {"cancelled": 1})
                self.assertEqual(report["running"], [])
                self.assert_process_stopped(log)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()

    def assert_process_stopped(self, log):
        pid = int(next(line[4:] for line in log.read_text().splitlines()
                       if line.startswith("PID=")))
        if os.name == "posix":
            with self.assertRaises(ProcessLookupError):
                os.kill(pid, 0)

    def test_qf_uf_rule_subset(self):
        self.case("a.alethe")
        source = self.root / "big.rare"
        source.write_text("""; parentheses inside comments: ) (
(declare-rare-rule bool-test ((p Bool)) :args (p) :conclusion p)
(declare-rare-rule seq-test () :args () :conclusion true)
(declare-rare-rule distinct-false () :args () :conclusion false)
(declare-rare-rule distinct-binary-elim () :args () :conclusion true)
""")
        report, output = self.run_benchmark("--rare-file", str(source),
                                            "--rare-profile", "qf-uf")
        self.assertEqual(report["rare_rules"], ["bool-test", "distinct-false"])
        self.assertNotIn("seq-test", (output / "rules.rare").read_text())
        self.assertIn("--rare-file", report["results"][0]["translation"]["command"])

    def test_form_scanner_handles_quotes_and_rejects_unbalanced_source(self):
        source = '; )\n(rule |name (a)| "string ; ( )" "doubled ""quote""" )\n(rule b)'
        self.assertEqual(len(list(benchmark.top_level_forms(source))), 2)
        for invalid in ("(rule a", ")", '(rule "unterminated)'):
            with self.assertRaises(ValueError):
                list(benchmark.top_level_forms(invalid))


class ProcessGroupTests(unittest.IsolatedAsyncioTestCase):
    @unittest.skipUnless(sys.platform.startswith("linux"), "uses Linux process state")
    async def test_timeout_kills_descendants(self):
        with tempfile.TemporaryDirectory() as temporary:
            log = Path(temporary) / "group.log"
            command = [sys.executable, "-c", "import subprocess,sys,time; "
                       "p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)']); "
                       "print(p.pid,flush=True); time.sleep(60)"]
            result = await benchmark.run_command(command, 0.3, log)
            self.assertTrue(result["timed_out"])
            pid = int(log.read_text().splitlines()[0])
            stat = Path(f"/proc/{pid}/stat")
            for _ in range(20):
                if not stat.exists() or stat.read_text().split()[2] == "Z":
                    break
                await asyncio.sleep(0.05)
            else:
                os.kill(pid, signal.SIGKILL)
                self.fail("descendant survived the timeout")


if __name__ == "__main__":
    unittest.main()
