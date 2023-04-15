import os, sys

sgpt_debug = os.environ.get('DEBUG',"0") == "1"

def debug(msg, end=""):
  if sgpt_debug:
    print(msg, end=end, file=sys.stderr)

def err(msg):
  print(msg, file=sys.stderr)
