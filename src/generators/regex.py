import requests
import os
from os.path import join as pjoin
import json
import progressbar
import re
from spdx_xml import template

_dir = 'regex'


def generate(dest, meta):
  print(f"Generating regex...")
  with open(pjoin(dest, meta['licenses-file'])) as f:
    licenses = json.load(f)

  os.makedirs(pjoin(dest, _dir), exist_ok=True)

  for license in progressbar.progressbar(licenses):
    license_id = license['id']
    regex_path = pjoin(dest, _dir, f"{license_id}")
    with open(pjoin(dest, meta['templates-dir'], f"{license_id}.json")) as f:
      root = template.parse_json(json.load(f))
    _generate_regex(regex_path, license_id, root)

  meta['regex-dir'] = _dir


def _generate_regex(dest: str, license_id: str, root: template.Node):
  with open(dest, 'w+') as f:
    f.write(str(root))
