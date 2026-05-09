from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn

ROOT = Path('/home/sarap/XDEI/P2_/terragalicia-dss')
sys.path.insert(0, str(ROOT / 'backend'))
sys.path.insert(1, str(ROOT))

os.environ.setdefault('ORION_BASE_URL', 'http://127.0.0.1:1026')
os.environ.setdefault('QUANTUMLEAP_BASE_URL', 'http://127.0.0.1:8668')
os.environ.setdefault('REDIS_URL', 'redis://127.0.0.1:6379/0')
os.environ.setdefault('ML_SERVICE_URL', 'http://127.0.0.1:8010')
os.environ.setdefault('APP_ENV', 'development')
os.environ.setdefault('APP_DEBUG', 'true')

from main import app  # noqa: E402

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000, log_level='info')
