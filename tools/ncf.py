# This is a Python module containing functions to parse and analyze ncf components

# This module is designed to run on the latest major versions of the most popular
# server OSes (Debian, Red Hat/CentOS, Ubuntu, SLES, ...)
# At the time of writing (November 2013) these are Debian 7, Red Hat/CentOS 6,
# Ubuntu 12.04 LTS, SLES 11, ...
# The version of Python in all of these is >= 2.6, which is therefore what this
# module must support

import re
import subprocess
import json
import os.path

tags = {}
tags["generic_method"] = ["name", "class_prefix"]
tags["technique"] = ["name", "description", "version"]

def parse_technique_metadata(technique_content):
  return parse_bundlefile_metadata(technique_content, "technique")

def parse_generic_method_metadata(technique_content):
  return parse_bundlefile_metadata(technique_content, "generic_method")

def parse_bundlefile_metadata(content, bundle_type):
  res = {}

  for line in content.splitlines():
    for tag in tags[bundle_type]:
      match = re.match("^\s*#\s*@" + tag + "\s+(.*)$", line)
      if match :
        res[tag] = match.group(1)

    if sorted(res.keys()) == sorted(tags[bundle_type]):
      # Found all the tags we need, stop parsing
      break

    if re.match("[^#]*bundle\s+agent\s+", line):
      # Any tags should come before the "bundle agent" declaration
      break
      
  if sorted(res.keys()) != sorted(tags[bundle_type]):
    missing_keys = [mkey for mkey in tags[bundle_type] if mkey not in set(res.keys())]
    raise Exception("One or more metadata tags not found before the bundle agent declaration (" + ", ".join(missing_keys) + ")")

  return res

def parse_technique_methods(technique_file):
  res = []

  # Check file exists
  if not os.path.exists(technique_file):
    raise Exception("No such file: " + technique_file)

  out = subprocess.check_output(["cf-promises", "-pjson", "-f", technique_file])
  promises = json.loads(out)

  # Sanity check: if more than one bundle, this is a weird file and I'm quitting
  if len(promises['bundles']) != 1:
    raise Exception("There is not exactly one bundle in this file, aborting")

  # Sanity check: the bundle must be of type agent
  if promises['bundles'][0]['bundleType'] != 'agent':
    raise Exception("This bundle if not a bundle agent, aborting")

  methods = [promiseType for promiseType in promises['bundles'][0]['promiseTypes'] if promiseType['name']=="methods"][0]['contexts']
  #print "context = " + methods[0]['contexts']['name']

  for context in methods:
    class_context = context['name']

    for method in context['promises']:
      method_name = None
      args = None

      promiser = method['promiser']

      for attribute in method['attributes']:
        if attribute['lval'] == 'usebundle':
          if attribute['rval']['type'] == 'functionCall':
            method_name = attribute['rval']['name']
            args = [arg['value'] for arg in attribute['rval']['arguments']]
          if attribute['rval']['type'] == 'string':
            method_name = attribute['rval']['value']

      if args:
        res.append({'class_context': class_context, 'method_name': method_name, 'args': args})
      else:
        res.append({'class_context': class_context, 'method_name': method_name})

  return res
