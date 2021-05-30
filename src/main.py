from generators import equivalentwords, license_list
import os
from datetime import datetime
import json

_generators = [
    equivalentwords,
    license_list,
]
_meta_filepath = 'meta.json'


def main():
  dest = os.path.abspath('dist')
  os.makedirs(dest, exist_ok=True)
  meta = {
      'generated-at': datetime.utcnow().isoformat(),
  }
  for generator in _generators:
    meta = {**meta, **generator.generate(dest)}
  with open(os.path.join(dest, _meta_filepath), 'w+') as f:
    json.dump(meta, f)


if __name__ == '__main__':
  main()
