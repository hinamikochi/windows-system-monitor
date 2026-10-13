import json
from pathlib import Path
import tempfile
import unittest

from system_monitor.config.store import Store, defaults, validate


class ConfigTests(unittest.TestCase):
    def test_invalid_types_and_bounds(self):
        value = validate(dict(interval=True, background_opacity=-1, position=['x', 3], modules=dict(cpu='false')))
        self.assertEqual(value['interval'], 1)
        self.assertEqual(value['background_opacity'], 0)
        self.assertIsNone(value['position'])
        self.assertTrue(value['modules']['cpu'])

    def test_round_trip_and_corrupt_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'settings.json'
            store = Store(path)
            settings = defaults()
            settings.update(interval=5, position=[-1200, 45], always_on_top=True)
            settings['modules']['gpu'] = False
            store.save(settings)
            self.assertEqual(store.load(), settings)
            self.assertFalse(path.with_suffix('.tmp').exists())
            path.write_text('{bad', encoding='utf-8')
            self.assertEqual(store.load(), defaults())

    def test_unknown_fields_are_ignored(self):
        self.assertEqual(validate(dict(unknown='value')), defaults())
