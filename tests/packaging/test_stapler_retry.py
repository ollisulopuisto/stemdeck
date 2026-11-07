"""Run the real helper with synthetic Apple responses, without a Mac/signing."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / 'scripts/macos/staple.sh'


class StaplerRetryTests(unittest.TestCase):
    def run_case(self, scenario):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            xcrun = root / 'xcrun'
            xcrun.write_text('''#!/usr/bin/env python3
import os,sys,pathlib
p=pathlib.Path(os.environ['CALLS']);calls=p.read_text().splitlines() if p.exists() else []
action=sys.argv[2];calls.append(action);p.write_text('\\n'.join(calls)+'\\n')
scenario=os.environ['SCENARIO']
if action=='validate' and scenario!='success':
 if scenario=='invalid':print('The validate action failed! Error73.');sys.exit(73)
 if scenario=='transient' and calls.count('validate')>1:sys.exit(0)
 print('error is Error Domain=NSURLErrorDomain Code=-1005 "The network connection was lost."');sys.exit(68)
''')
            xcrun.chmod(0o755)
            sleeper = root / 'sleep'
            sleeper.write_text('#!/bin/sh\nexit 0\n')
            sleeper.chmod(0o755)
            calls = root / 'calls'
            result = subprocess.run(['bash', str(SCRIPT), '/fake/StemDeck.app'],
                env=os.environ | {'PATH': str(root) + ':' + os.environ['PATH'],
                                  'CALLS': str(calls), 'SCENARIO': scenario},
                capture_output=True, text=True)
            return result.returncode, calls.read_text().splitlines()

    def test_success_needs_staple_and_validate(self):
        self.assertEqual(self.run_case('success'), (0, ['staple', 'validate']))

    def test_transient_validation_retries_without_resubmitting(self):
        self.assertEqual(self.run_case('transient'), (0, ['staple', 'validate', 'validate']))

    def test_persistent_network_error_still_fails(self):
        self.assertEqual(self.run_case('persistent'), (68, ['staple', 'validate', 'validate', 'validate']))

    def test_invalid_ticket_fails_without_retry(self):
        self.assertEqual(self.run_case('invalid'), (73, ['staple', 'validate']))


if __name__ == '__main__':
    unittest.main()
