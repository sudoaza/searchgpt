#!/usr/bin/env -S python3 -u

import os, sys, re

from googlesearch import search
from lib.scrap import get_article, retry_search
from lib.easy_openai import *
from lib.models import *
from lib.app import *

agent_prompt = """Remember, you are a viable system, as such you must keep track of the world state you interact with, your current task and it's place in your long term plan.

When presented with a task, you will interpret it and provide your plan, what you will be doing now and your world representation.
For the plan, provide a list of steps. Each a short sentence. Build on this list to develop and remember the plan.
For the doing section, please provide a brief explanation of what current action you will be performing with what end or under what asumptions. Use this to build the response or research data for the {task}.
You will take several steps to answer your question, you will take time to analyze and set out your ideas.

Think of the information you will need to answer and look at past states to write the current state.

# Format

Please always format your response as follows, so you can remember what 
you are doing.
    Plan: [What is the long term plan?]
    Doing: [What are we doing? What are our assumptions? What problems?]
    Command: [One command to choose from available SEARCH/READ/CONTINUE/FINAL]

## Only Available Commands:
- SEARCH [Search query] to search for information online and get a list of URLs.
- READ [Url] to read the text information at that one URL.
- CONTINUE to continue analyzing the available information without requesting new information.
- FINAL [Final response] One or many lines of text with the final response to the {task}.

You can only read one URL at the time. Remember any other as tasks.
Update your plan when it changes, provide a response when you want and always include the doing section.

# Example
Task: Analyze glyphosate toxicity.
Plan:
  - Research literature about glyphosate toxicity. (Doing)
  - Compile top relevant papers talking about glyphosate effects on humans and animals.
  - Compile top parragraphs relevant to answering the question. 
  - Respond based on all researched information.
Donig: Searching for papers on glyphosate toxicity, this should be an authoritative source.
If information is incomplete we can do another search.
Command: SEARCH scientific publication glyfosate toxicity, harm and exposure

# Actual
Task: """

def agent_start(prompt):
  plan = ""
  control = ""
  command = ""
  system_prompt = agent_prompt + prompt
  while True: # Tic tac
    (prompt, response) = chat_complete(prompt, system=system_prompt)
    (plan_, control_, command_) = parse_state(response)
    print(response)
    if len(prompt) > 10:
      prompt = prompt[-10:]
      prompt[0] = {"role":"system","content":system_prompt}
    
    if plan_:
      plan = plan_
    if control_:
      control = control_
    if command_:
      command = command_
    else:
      ### ??? we should have gotten a command
      print("WARNING didn't get a Command!", file=sys.stderr)
      prompt.append({"role":"assistant", "content":plan+control})
      continue # skip nothing to process

    # SEARCH
    if is_command(command,"SEARCH"):
      query = " ".join(command_params(command))
      urls = retry_search(query, num_results=10)
      
      print("\n".join(urls))
      prompt.append(usermsg("Search results:\n" + "\n".join(urls)))

    # READ
    elif is_command(command,"READ"):
      url = command_param(command)
      if url[-1] == ".":
        url = url[:-1]
      print("Reading", url)
      text = get_article(url)
      sintesis = "Error, unable to READ URL. Try a different one."
      if text.strip() != "":
        n = 0
        sintesis = ""
        for piece in chunk(text, max_tokens=3968):
          _, response = chat_complete(piece, system="Hello assistant, please select information relevant to the task.\nReproduce titles, lines, parragraphs and context when relevant.\nAlso provide a general sintesis.\n"+plan+control)
          sintesis += response + "\n"
          n += 1
          if n > 6:
            break

      prompt.append(usermsg(sintesis))
      print(sintesis)
    # CONTINUE
    elif is_command(command,"CONTINUE"):
      prompt.append(usermsg("CONTINUE"))

    elif is_command(command,"FINAL"):
      response = command_params(command, sep=", ")
      return response

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
  if plan_start:
    plan_text = response[plan_start:control_start].strip()
  if control_start:
    control_text = response[control_start:command_start].strip()
  if command_start:
    command_text = response[command_start:].strip()

  return plan_text, control_text, command_text

if __name__ == "__main__":
  if len(sys.argv) < 2:
    print(f"Usage: python {os.path.basename(__file__)} <prompt>")
    sys.exit(1)

  prompt = sys.argv[1]
  agent_start(prompt)

