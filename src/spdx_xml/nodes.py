import xml.dom.minidom as xml
import re


class Node:
  def __init__(self, tag: str):
    self._tag = tag

  def _to_dict(self):
    return {
        'type': self._tag,
    }

  def _is_empty(self):
    return False

  def _normalize(self):
    pass


def normalize(nodes: list[Node]) -> list[Node]:
  """
  Normalize the nodes to remove redundancy.
  First, we remove nodes that are empty.
  Then, consecutive text nodes are merged.
  """
  # Remove empty nodes
  nodes = list(filter(lambda node: not node._is_empty(), nodes))
  # Merge nodes
  nodes_merged = []
  for node in nodes:
    if nodes_merged and isinstance(node, TextNode) and isinstance(nodes_merged[-1], TextNode):
      nodes_merged[-1] = TextNode(nodes_merged[-1].text + node.text)
    else:
      nodes_merged.append(node)
  # Normalize
  for node in nodes_merged:
    node._normalize()
  return nodes_merged


def to_dict(nodes: list[Node]) -> list:
  return [node._to_dict() for node in nodes]


class TextNode(Node):
  _regex_hspace = re.compile('[^\S\n\v\f\r\u2028\u2029]+')
  _regex_vspace = re.compile('\s*[\n\v\f\r\u2028\u2029]\s*')

  def __init__(self, text: str):
    super().__init__('text')
    self.text = text

  def _to_dict(self):
    return {
        **super()._to_dict(),
        'content': self.text,
    }

  def _is_empty(self):
    return not self.text

  def _normalize(self):
    self.text = self._regex_vspace.sub('\n', self.text)
    self.text = self._regex_hspace.sub(' ', self.text)


class OptionaltNode(Node):
  def __init__(self, contents: list[Node]):
    super().__init__('optional')
    self.contents = contents

  def _to_dict(self):
    return {
        **super()._to_dict(),
        'content': to_dict(self.contents),
    }

  def _is_empty(self):
    return all(node._is_empty() for node in self.contents)

  def _normalize(self):
    self.contents = normalize(self.contents)


class VarNode(Node):
  def __init__(self, name: str, original: list[Node], pattern: str):
    super().__init__('var')
    self.name = name
    self.original = original
    self.pattern = pattern

  def _to_dict(self):
    return {
        **super()._to_dict(),
        'name': self.name,
        'content': to_dict(self.original),
        'pattern': self.pattern,
    }

  def _normalize(self):
    self.original = normalize(self.original)


class _XmlTransformer:
  """
  Transforms a template in a license XML into a json format.
  Based on spdx/LicenseListPublisher's code.
  See: https://github.com/spdx/LicenseListPublisher/blob/master/src/org/spdx/licensexml/LicenseXmlHelper.java
  """
  HSPACE_NODE = TextNode(' ')
  VSPACE_NODE = TextNode('\n')

  def __init__(self):
    self._transformers = {
        'list': self._transform_list_node,
        'alt': self._transform_alt_node,
        'optional': self._transform_optional_node,
        'br': self._transform_break_node,
        'p': self._transform_paragraph_node,
        'titleText': self._transform_optional_node,
        'copyrightText': self._transform_copyright_node,
        'bullet': self._transform_bullet_node,
        'item': self._transform_unprocessed,
        'text': self._transform_unprocessed,
        'standardLicenseHeader': self._transform_unprocessed,
    }

  def _transform_node(self, node: xml.Element) -> list[Node]:
    if node.nodeType == xml.Node.TEXT_NODE:
      return self._transform_text_node(node)
    elif node.nodeType == xml.Node.ELEMENT_NODE:
      if node.tagName not in self._transformers:
        raise NotImplementedError("Unsupported node type")
      spacing = node.getAttribute('spacing') if node.hasAttribute('spacing') else 'default'
      result = []
      if spacing in ('default', 'before', 'both'):
        result.append(self.HSPACE_NODE)
      result += self._transformers[node.tagName](node)
      if spacing in ('after', 'both'):
        result.append(self.HSPACE_NODE)
      return result
    else:
      raise NotImplementedError("Unsupported node type")

  def _transform_text_node(self, node: xml.Element) -> list[Node]:
    assert node.nodeType == xml.Node.TEXT_NODE
    return [TextNode(node.nodeValue)]

  def _transform_list_node(self, node: xml.Element) -> list[Node]:
    assert node.nodeType == xml.Node.ELEMENT_NODE
    results = []
    for child in node.childNodes:
      if child.nodeType == xml.Node.TEXT_NODE:
        results += self._transform_text_node(child)
      elif child.nodeType != xml.Node.ELEMENT_NODE:
        raise NotImplementedError(f"Unsupported node type")
      elif child.tagName == 'item':
        results.append(self.VSPACE_NODE)
        results += self._transform_unprocessed(child)
      elif child.tagName == 'list':
        results += self._transform_list_node(child)
      else:
        raise NotImplementedError("Unsupported node type")
    return results

  def _transform_alt_node(self, node: xml.Element) -> list[Node]:
    assert node.nodeType == xml.Node.ELEMENT_NODE
    original = self._transform_unprocessed(node)
    name = node.getAttribute('name')
    match = node.getAttribute('match')
    return [VarNode(name, original, match)]

  def _transform_optional_node(self, node: xml.Element) -> list[Node]:
    assert node.nodeType == xml.Node.ELEMENT_NODE
    contents = self._transform_unprocessed(node)
    return [OptionaltNode(contents)]

  def _transform_break_node(self, node: xml.Element) -> list[Node]:
    assert node.nodeType == xml.Node.ELEMENT_NODE
    assert not node.childNodes
    return [self.VSPACE_NODE]

  def _transform_paragraph_node(self, node: xml.Element) -> list[Node]:
    assert node.nodeType == xml.Node.ELEMENT_NODE
    result = []
    result.append(self.VSPACE_NODE)
    for child in node.childNodes:
      result += self._transform_node(child)
    result.append(self.VSPACE_NODE)
    return result

  def _transform_copyright_node(self, node: xml.Element) -> list[Node]:
    assert node.nodeType == xml.Node.ELEMENT_NODE
    original = self._transform_unprocessed(node)
    name = 'copyright'
    match = '.{0,5000}'
    return [VarNode(name, original, match)]

  def _transform_bullet_node(self, node: xml.Element) -> list[Node]:
    assert node.nodeType == xml.Node.ELEMENT_NODE
    original = self._transform_unprocessed(node)
    name = 'bullet'
    match = '.{0,20}'
    return [VarNode(name, original, match)]

  def _transform_unprocessed(self, node: xml.Element) -> list[Node]:
    if node.nodeType == xml.Node.TEXT_NODE:
      return self._transform_text_node(node)
    elif node.nodeType == xml.Node.ELEMENT_NODE:
      return sum([self._transform_node(child) for child in node.childNodes], [])
    else:
      raise NotImplementedError("Unsupported node type")


def parse_xml(text: xml.Element) -> list[Node]:
  """
  Parses a dom element in the spdx-license-XML format and returns a Node.
  """
  transformer = _XmlTransformer()
  tree = transformer._transform_node(text)
  tree = normalize(tree)
  return tree


def parse_json(nodes: list) -> list[Node]:
  """
  Deserialize nodes in json format.
  """
  results = []
  for node in nodes:
    assert 'type' in node
    if node['type'] == 'text':
      results.append(TextNode(node['content']))
    elif node['type'] == 'optional':
      content = parse_json(node['content'])
      results.append(OptionaltNode(content))
    elif node['type'] == 'var':
      name = node['name']
      content = parse_json(node['content'])
      pattern = node['pattern']
      results.append(VarNode(name, content, pattern))
    else:
      raise NotImplementedError('Unsupported node type')
  return results