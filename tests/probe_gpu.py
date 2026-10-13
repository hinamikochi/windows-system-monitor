import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from system_monitor.monitoring.gpu import GPU

gpu = GPU()
try:
    for _ in range(3):
        print(json.dumps(gpu.sample(), ensure_ascii=False), flush=True)
        time.sleep(1)
finally:
    gpu.close()
