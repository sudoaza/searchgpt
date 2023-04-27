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

from googlesearch import search
from lib.scrap import *
from lib.easy_openai import *
from lib.models import *
from lib.app import *

def agent_start(prompt):
  plan = ""
  control = ""
  command = ""
  urls = []
  system_prompt = agent_prompt + prompt
  while True: # Tic tac
    max_tokens_convo = 4000 - token_count3(system_prompt)
    
    # Always but first round
    if type(prompt) == list:
      prompt = truncate_convo(prompt, max_tokens_convo)
      if len(prompt) > 0:
        if prompt[0]["role"] != "system":
          prompt[0] = sysmsg(system_prompt)
      else:
        print("WHAT just happened?", file=sys.stderr)
        prompt = [sysmsg(system_prompt),agentmsg(plan+control)]

    (prompt, response) = chat_complete(prompt, system=system_prompt)
    (plan_, control_, command_) = parse_state(response)
    print(response)
    
    if plan_:
      plan = plan_
    if control_:
      control = control_
    if command_:
      command = command_
    else:
      ### ??? we should have gotten a command
      print("WARNING didn't get a Command!", file=sys.stderr)
      prompt.append([usermsg('You did not provide a line starting with "Command:". Repeat but send the "Command" line.')])
      continue # skip nothing to process

    # SEARCH
    if is_command(command,"SEARCH"):
      query = " ".join(command_params(command))
      urls = retry_search(query, num_results=6, advanced=True)
      urls_list = "\n\n".join([str(i+1) + ": " + url.url + "\n" + url.title + "\n" + url.description for i, url in enumerate(urls)])
      debug(urls_list)
      prompt.append(usermsg("Search results:\n" + urls_list))

    # READ
    elif is_command(command,"READ"):
      url_n = command_param(command)
      url_n = re.search(r'\d+', url_n).group()
      url = urls[int(url_n) - 1].url
      info("Reading", url_n, url)
      text = get_article(url)
      text = clean_scrapy_text(text)
      debug(text)
      info("Read chars:",len(text), "words:", len(text.split()), "parragraphs:", len(text.split("\n\n")))
      if len(text) > 0:
        prompt.extend( [usermsg("Text: " + piece) for piece in chunk(text, max_tokens=max_tokens_convo, token_counter=token_count3)][:6] )
      else:
        prompt.extend( [usermsg("Unable to read article, read another.")])

    # CONTINUE
    elif is_command(command,"CONTINUE"):
      prompt.append(usermsg("CONTINUE"))

    # FINAL
    elif is_command(command,"FINAL"):
      response = " ".join(command_params(command))
      print('New task or exit:', end="")
      new_prompt = input()
      if new_prompt.strip() == "" or new_prompt.strip().lower() == "exit":
        return response
      system_prompt = agent_prompt + new_prompt
      prompt.extend([sysmsg(system_prompt), usermsg(new_prompt)])

    else:
      print("WARNING got invalid Command!", command, file=sys.stderr)

def is_command(text, command_name):
  return text.startswith("Command: "+command_name) or text.startswith(command_name)

def command_params(text, sep=" "):
  if text.startswith("Command: "):
    text = text[9:]
  # remove command name
  text = " ".join(text.split(" ")[1:])
  return text.split(sep)

def command_param(text):
  return command_params(text)[0]

def parse_state(response):
  plan_start = control_start = command_start = None
  # find the indexes of the Plan, Control, and Command sections
  if "Plan:" in response:
    plan_start = response.index("Plan:")
  if "Doing:" in response:
    control_start = response.index("Doing:")
  if "Command:" in response:
    command_start = response.index("Command:")
  plan_text = control_text = command_text = None
  # extract the text of each section
  if plan_start is not None and plan_start >= 0:
    plan_text = response[plan_start:control_start].strip()
  if control_start is not None and control_start >= 0:
    control_text = response[control_start:command_start].strip()
  if command_start is not None and command_start >= 0:
    command_text = response[command_start:].strip()

  return plan_text, control_text, command_text

if __name__ == "__main__":
  if len(sys.argv) < 2:
    print(f"Usage: python {os.path.basename(__file__)} <prompt>")
    sys.exit(1)

  prompt = sys.argv[1]
  agent_start(prompt)

