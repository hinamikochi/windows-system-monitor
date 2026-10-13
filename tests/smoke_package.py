"""Run source or frozen app with isolated configuration and no visible UI."""
import os
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

root = Path(__file__).resolve().parents[1]
command = [sys.argv[1]] if len(sys.argv) > 1 else [sys.executable, str(root / 'main.py')]
with tempfile.TemporaryDirectory(dir=root) as directory:
    environment = os.environ.copy()
    environment['LOCALAPPDATA'] = directory
    environment['QT_QPA_PLATFORM'] = 'offscreen'
    data = Path(directory) / 'SystemMonitorWidget'
    if len(sys.argv) > 2:
        data.mkdir()
        (data / 'config.json').write_text(json.dumps({'disk_path': sys.argv[2]}), encoding='utf-8')
    process = subprocess.Popen(command + ['--smoke-test'], env=environment, cwd=root,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    duplicate = None
    try:
        deadline = time.monotonic() + 20
        while not (data / 'instance.lock').exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.05)
        if (data / 'instance.lock').exists():
            # Test that a source launch also respects a frozen application's lock.
            duplicate = subprocess.run([sys.executable, str(root / 'main.py')],
                                       env=environment, cwd=root, capture_output=True,
                                       text=True, timeout=8)
    finally:
        stdout, stderr = process.communicate(timeout=60)
    log = (data / 'app.log').read_text(encoding='utf-8') if (data / 'app.log').exists() else ''
    assert process.returncode == 0, (process.returncode, stderr, log)
    assert duplicate is not None and duplicate.returncode == 0, 'Duplicate launch must exit promptly'
    assert 'SMOKE PASS' in log, log
    assert (data / 'config.json').exists(), 'Configuration must survive packaged execution'
    if len(sys.argv) > 2:
        assert json.loads((data / 'config.json').read_text(encoding='utf-8'))['disk_path'] == sys.argv[2]
    assert not (data / 'instance.lock').exists(), 'Application lock must be released'
    print(log.strip())
    print('PASS: app startup, real metrics, source/packaged instance guard, configuration and graceful process exit.')
