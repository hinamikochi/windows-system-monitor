import copy
import json
import logging
import os
from pathlib import Path
from system_monitor.monitoring.disks import default_disk, normalize_disk

MODULES = ('cpu', 'ram', 'gpu', 'disk', 'network', 'battery')


def defaults():
    return dict(modules=dict.fromkeys(MODULES, True), interval=1, background_opacity=65,
                always_on_top=False, startup=False, position=None, disk_path=default_disk())


def data_directory():
    return Path(os.environ.get('LOCALAPPDATA', Path.home() / '.local' / 'share')) / 'SystemMonitorWidget'


def validate(raw):
    result = defaults()
    if not isinstance(raw, dict):
        return result
    modules = raw.get('modules', {})
    result['disk_path'] = normalize_disk(raw.get('disk_path'))
    if isinstance(modules, dict):
        for key in MODULES:
            if type(modules.get(key)) is bool:
                result['modules'][key] = modules[key]
    if type(raw.get('interval')) is int and raw['interval'] in (1, 2, 5):
        result['interval'] = raw['interval']
    if type(raw.get('background_opacity')) is int:
        result['background_opacity'] = max(0, min(100, raw['background_opacity']))
    for key in ('always_on_top', 'startup'):
        if type(raw.get(key)) is bool:
            result[key] = raw[key]
    position = raw.get('position')
    if isinstance(position, list) and len(position) == 2 and all(type(n) is int and abs(n) < 100000 for n in position):
        result['position'] = position
    return result


class Store:
    def __init__(self, path=None):
        self.path = Path(path) if path else data_directory() / 'config.json'

    def load(self):
        try:
            return validate(json.loads(self.path.read_text(encoding='utf-8')))
        except (OSError, ValueError):
            logging.getLogger(__name__).debug('Using default configuration', exc_info=True)
            return defaults()

    def save(self, settings):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix('.tmp')
        temporary.write_text(json.dumps(validate(copy.deepcopy(settings)), indent=2), encoding='utf-8')
        os.replace(temporary, self.path)
