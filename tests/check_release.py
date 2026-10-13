from pathlib import Path
import hashlib
import json
import sys

import pefile

root = Path(__file__).resolve().parents[1]
path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else root / 'dist' / 'SystemMonitor.exe'
binary = pefile.PE(str(path))
assert binary.OPTIONAL_HEADER.Subsystem == 2, 'Release must use the Windows GUI subsystem'
assert binary.FILE_HEADER.Machine == 0x8664, 'Expected x64 executable'
resource_types = {entry.id for entry in binary.DIRECTORY_ENTRY_RESOURCE.entries}
assert 14 in resource_types, 'Executable must embed its icon'
manifest = next(entry for entry in binary.DIRECTORY_ENTRY_RESOURCE.entries if entry.id == 24)
entry = manifest.directory.entries[0].directory.entries[0].data.struct
data = binary.get_data(entry.OffsetToData, entry.Size)
assert b'asInvoker' in data, 'Executable must not request Administrator'
binary.close()
report = dict(file=path.name, bytes=path.stat().st_size,
              sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
              architecture='x64', console=False, administrator=False)
(path.parent / 'release-info.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
