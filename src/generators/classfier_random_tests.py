from xeger import Xeger
from hashlib import sha256 as hasher
import os
from os.path import join as pjoin
from random import Random
from spdx_xml import template
import json
import progressbar
from util import escape_license_id

_seed = 'm1k17'
_rand = Random(_seed)
_xeger = Xeger(limit=20, seed=_seed)
_dir = 'tests/classfier/positive'
_tests_per_id = 3


def generate(dest, meta):
  print(f"Generating random tests...")
  with open(pjoin(dest, meta['licenses-file'])) as f:
    licenses = json.load(f)

  for license in progressbar.progressbar(licenses):
    license_id = license['id']
    license_path = escape_license_id(license_id)
    license_dir = pjoin(dest, _dir, license_path)
    os.makedirs(license_dir, exist_ok=True)

    with open(pjoin(dest, meta['templates-dir'], f"{license_path}.json")) as f:
      root = template.parse_json(json.load(f))
    for _ in range(_tests_per_id):
      _generate_test(license_dir, root)


def _generate_test(dest: str, root: template.Node):
  result = _dfs_template(root)
  h = hasher()
  h.update(result.encode())
  digest = h.hexdigest()
  with open(pjoin(dest, f"{digest}.txt"), 'w+') as f:
    f.write(result)


def _dfs_template(root: template.Node) -> str:
  if isinstance(root, template.SequentialNode):
    return ''.join(_dfs_template(node) for node in root.nodes)
  elif isinstance(root, template.TextNode):
    return root.text
  elif isinstance(root, template.OptionalNode):
    if _rand.random() < 0.5:
      return ''
    return _dfs_template(root.content)
  elif isinstance(root, template.VarNode):
    return _xeger.xeger(root.pattern)
  else:
    raise NotImplementedError("Unsupported node type")
