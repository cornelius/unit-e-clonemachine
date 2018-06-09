#!/usr/bin/env python3
# vim: ts=2 sw=2 sts=2 expandtab

import subprocess
import re
from typing import *

def toLower(s: str) -> str:
  return s.translate(str.maketrans(
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
    'abcdefghijklmnopqrstuvwxyz'
  ))

def substitute(string: str,
               needle: str,
               replacer: Callable[[str], str],
               match_before: str = "",
               match_after: str = "",
               case_sensitive: bool = True,
               blacklist: Sequence[str] = []) -> str:
  haystack = string if case_sensitive else toLower(string)
  out = []
  needle_length = len(needle)
  ix = 0
  begin_offset = haystack.find(needle, ix)
  while begin_offset >= 0:
    end_offset = begin_offset + needle_length
    before = string[begin_offset - 1 : begin_offset]
    after = string[end_offset : end_offset + 1]
    match = string[begin_offset : end_offset]
    blacklisted = False
    for item in blacklist:
      item_haystack = item if case_sensitive else toLower(item)
      item_ix = item_haystack.find(needle)
      ctx_begin_offset = begin_offset - item_ix
      ctx_end_offset = ctx_begin_offset + len(item)
      context = string[ctx_begin_offset : ctx_end_offset]
      if context == item:
        blacklisted = True
        break
    if not blacklisted and re.match(match_before, before) and re.match(match_after, after):
      out.append(string[ix : begin_offset])
      out.append(replacer(match))
    else:
      out.append(string[ix:end_offset])
    ix = end_offset
    begin_offset = haystack.find(needle, ix)
  out.append(string[ix : len(string)])
  return "".join(out)

def replaceRecursively(needle: str,
                       replacement: str,
                       match_before: str = "$|[^a-zA-Z0-9]",
                       match_after: str = "$|[^a-zA-Z0-9]"):
  files = subprocess.run(["grep", "-RIF", "-l", needle, "."], stdout=subprocess.PIPE)
  for f in files.stdout.splitlines():
    path = f.decode('utf8')
    with open(path, 'r') as source_file:
      contents = source_file.read()
    out = substitute(contents, needle, lambda x: replacement, match_before, match_after)
    with open(path, 'w') as source_file:
      source_file.write(out)

def applyRecursively(func, command = ['find', '.', '-type', 'f']):
  files = subprocess.run(command, stdout=subprocess.PIPE)
  for f in files.stdout.splitlines():
    path = f.decode('utf8')
    if any(map(lambda x: len(x) > 1 and x.startswith('.'), path.split('/')[:-1])):
      continue;
    func(path)

def gitMoveFile(path, needle, replacement):
  target = path.replace(needle, replacement)
  if target == path:
    return
  target_parent = '/'.join(target.split('/')[:-1])
  subprocess.run(['mkdir', '-p', target_parent])
  result = subprocess.run(["git", "mv", path, target])
  if result.returncode != 0:
    exit(result.returncode)

def replaceBitcoinIdentifier(occurence: str):
  if occurence == 'bitcoin':
    return 'unite'
  if occurence == 'BITCOIN':
    return 'UNITE'
  if occurence == 'Bitcoin':
    return 'UnitE'
  raise Exception("Don't know how to handle %s" % occurence)

def f(path):
  with open(path, 'r') as source_file:
    contents = source_file.read()
  altered = substitute(contents, "bitcoin", replaceBitcoinIdentifier, case_sensitive = False, blacklist = [
    "The Bitcoin Core developers",
    "Bitcoin Developer",
    "As Bitcoin relies on 80 byte header hashes"
  ])
  with open(path, 'w') as target_file:
    target_file.write(altered)

replaceRecursively("8333", "7182")
subprocess.run(['git', 'commit', '-am', 'Turned mainnet port 8333 into 7182'])
subprocess.run(['git', 'push'])

replaceRecursively("18333", "17182")
subprocess.run(['git', 'commit', '-am', 'Turned testnet port 18333 into 17182'])
subprocess.run(['git', 'push'])

applyRecursively(lambda path: gitMoveFile(path, "bitcoin", "unite"))
subprocess.run(['git', 'commit', '-am', 'Moved paths containing "bitcoin" to respective "unite" paths'])

applyRecursively(f, ['grep', '-RIFil', 'bitcoin', '.'])
subprocess.run(['git', 'commit', '-am', 'Renamed occurences of "bitcoin" to "unite"'])
subprocess.run(['git', 'push'])

