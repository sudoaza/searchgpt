#!/usr/bin/env -S python3 -u

"""
  - search
  - read
  - analize
  - memory
  - 5-...
  - 4-plan
  - 3-execute
"""
import os, sys, re
from time import sleep
from googlesearch import search
from lib.scrap import *
from lib.easy_openai import *
from lib.models import *
from lib.app import *
from lib.vsys import *

def agent_start(prompt):
  agent = VSys()
  agent.conversation.append(usermsg(prompt))
  while True: # Tic tac 
    response = agent.step()
    print(response)
    sleep(1/4)

if __name__ == "__main__":
  if len(sys.argv) < 2:
    print(f"Usage: python -u {os.path.basename(__file__)} <prompt>")
    sys.exit(1)

  prompt = sys.argv[1]
  agent_start(prompt)

