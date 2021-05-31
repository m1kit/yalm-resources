import requests
import os
from os.path import join as pjoin
import json
import progressbar
import re
from spdx_xml import nodes

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
      template = nodes.parse_json(json.load(f))
    _generate_words(words_path, license_id, template, equivalentwords)

  meta['words-dir'] = _dir


def _generate_words(dest: str, license_id: str, template: list[nodes.Node], equivalentwords):
  words = []
  for node in template:
    if not isinstance(node, nodes.TextNode):
      continue
    words += node.text.split()
  words = list(filter(_valid_word.fullmatch, words))
  words = [_normalize_word(word, equivalentwords) for word in words]
  words.sort()
  with open(dest, 'w+') as f:
    json.dump(words, f)


def _normalize_word(word, equivalentwords):
  word = word.lower()
  for pair in equivalentwords:
    if word == pair['from']:
      return pair['to']
  return word
