from xeger import Xeger
from hashlib import sha256 as hasher
import os
from os.path import join as pjoin
from random import Random
from spdx_xml import nodes
import json
import progressbar

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
    license_dir = pjoin(dest, _dir, license_id)
    os.makedirs(license_dir, exist_ok=True)

    with open(pjoin(dest, meta['templates-dir'], f"{license_id}.json")) as f:
      template = nodes.parse_json(json.load(f))
    for _ in range(_tests_per_id):
      _generate_test(license_dir, template)


def _generate_test(dest: str, template: list[nodes.Node]):
  result = _dfs_nodes(template)
  h = hasher()
  h.update(result.encode())
  digest = h.hexdigest()
  with open(pjoin(dest, f"{digest}.txt"), 'w+') as f:
    f.write(result)


def _dfs_nodes(template: list[nodes.Node]) -> str:
  result = ''
  for node in template:
    if isinstance(node, nodes.TextNode):
      result += node.text
    elif isinstance(node, nodes.OptionaltNode):
      if _rand.random() < 0.5:
        result += _dfs_nodes(node.contents)
    elif isinstance(node, nodes.VarNode):
      result += _xeger.xeger(node.pattern)
  return result