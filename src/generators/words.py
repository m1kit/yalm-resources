import requests
import os
from os.path import join as pjoin
import json
import progressbar
import re
from spdx_xml import template

_dir = 'words'
_valid_word = re.compile(r'[a-zA-Z]+')


def generate(dest, meta):
  print(f"Generating word set...")
  with open(pjoin(dest, meta['licenses-file'])) as f:
    licenses = json.load(f)
  with open(pjoin(dest, meta['equivalentwords-file'])) as f:
    equivalentwords = json.load(f)

  os.makedirs(pjoin(dest, _dir), exist_ok=True)

  for license in progressbar.progressbar(licenses):
    license_id = license['id']
    words_path = pjoin(dest, _dir, f"{license_id}.json")
    with open(pjoin(dest, meta['templates-dir'], f"{license_id}.json")) as f:
      root = template.parse_json(json.load(f))
    _generate_words(words_path, license_id, root, equivalentwords)

  meta['words-dir'] = _dir


def _generate_words(dest: str, license_id: str, root: template.Node, equivalentwords):
  words = _dfs_template(root)
  words = list(filter(_valid_word.fullmatch, words))
  words = [_normalize_word(word, equivalentwords) for word in words]
  words.sort()
  with open(dest, 'w+') as f:
    json.dump(words, f)


def _dfs_template(root: template.Node) -> list[str]:
  if isinstance(root, template.SequentialNode):
    return sum([_dfs_template(node) for node in root.nodes], [])
  elif isinstance(root, template.TextNode):
    return root.text.split()
  else:
    return []


def _normalize_word(word, equivalentwords):
  word = word.lower()
  for pair in equivalentwords:
    if word == pair['from']:
      return pair['to']
  return word
