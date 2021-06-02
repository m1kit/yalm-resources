from hashlib import sha256 as hasher
import os
from os import path
import glob
from spdx_xml import nodes
import json
import progressbar

_dir = 'tests/classfier/positive'


def generate(dest, meta):
  print(f"Generating random tests...")
  with open(path.join(dest, meta['licenses-file'])) as f:
    licenses = json.load(f)
  valid_ids = set(license['id'] for license in licenses)

  for testfile in progressbar.progressbar(glob.glob('static/tests/*.txt')):
    license_id = path.splitext(path.split(testfile)[-1])[0]
    if not license_id in valid_ids:
      continue
    license_dir = path.join(dest, _dir, license_id)
    os.makedirs(license_dir, exist_ok=True)

    with open(testfile) as f:
      test = f.read()
    _generate_test(license_dir, test)


def _generate_test(dest: str, test: str):
  h = hasher()
  h.update(test.encode())
  digest = h.hexdigest()
  with open(path.join(dest, f"{digest}.txt"), 'w+') as f:
    f.write(test)
