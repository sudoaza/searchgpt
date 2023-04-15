#!/usr/bin/env -S python3 -u

import os, sys

from lib.models import *
from lib.app import *

if __name__ == "__main__":
  if len(sys.argv) < 2:
    print(f"Usage: python {os.path.basename(__file__)} <prompt>")
    sys.exit(1)

  prompt = sys.argv[1]
  print( complete_with_sources(prompt) )