from generators import equivalentwords, license_list, templates
import os
from datetime import datetime
import json

_generators = [
    equivalentwords,
    license_list,
    templates,
]
_meta_filepath = 'meta.json'


def main():
  dest = os.path.abspath('dist')
  os.makedirs(dest, exist_ok=True)
  meta = {
      'generated-at': datetime.utcnow().isoformat(),
  }
  for generator in _generators:
    generator.generate(dest, meta)
  with open(os.path.join(dest, _meta_filepath), 'w+') as f:
    json.dump(meta, f)


if __name__ == '__main__':
  main()
