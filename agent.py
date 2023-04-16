#!/usr/bin/env -S python3 -u

import os, sys, re

from googlesearch import search
from lib.scrap import get_article, retry_search
from lib.easy_openai import *
from lib.models import *
from lib.app import *

agent_prompt = """Remember, you are a viable system, as such you must reproduce yourself at each time step. Keep track of the environment you interact with, your current task and it's place in your long term plan.

When presented with a task, you will interpret it and provide your plan, what you will be doing now and your world representation.
For the plan, provide a list of 3 or 4 steps. Each a short sentence, can include sub-tasks. Build on this list to develop and remember the plan and keep track of it.
For the doing section, please provide a brief explanation of what current action you will be performing with what end or under what asumptions. Use this to build the response or research data for the {task}.
Once a step is Done you can remove it. 

Write what you plan to search and read as tasks but only execute one command at a time. A good plan is the search, read, analyze, plan loop. Search for some information, read a couple of articles, sintetize them identifying more specific subjects to research deeper.
Stop when you have enough information to answer the task truthfully and with confidence.

# Format

    Plan: [What is the long term plan?]
    Doing: [What are we doing? How are you doing it? What are our assumptions? What problems?]
    Command: [One command to choose from available SEARCH/READ/CONTINUE/FINAL]

## Only Available Commands:
- SEARCH [Google Search query]
- READ [Number] to read more information about that search result.
- CONTINUE [Temporary response] to write a temporary conclusion and continue analyzing the past conversation.
- FINAL [Final response] One or many lines of text with the final response based on research for the {task}.

You can only issue one command per update.

# Example
Task: Analyze glyphosate toxicity.
Plan:
  - Research literature about glyphosate toxicity. (Doing)
  - Compile top relevant papers talking about glyphosate effects on humans and animals.
  - Compile top parragraphs relevant to answering the question. 
  - Respond based on all researched information.
Doing: Searching for papers on glyphosate toxicity, this should be an authoritative source.
If information is incomplete we can do another search. I will write a Google search query for the SEARCH Command.
I will pick 3 diverse urls from the results and read each.
Command: SEARCH scientific publication glyfosate toxicity, harm and exposure

# Example 2
Doing: Reading relevant paper. Assuming papers are an authoritative and trustworthy source.
Command: READ 1

# Example 3
Doing: Sintetizing relevant information from previous article and compiling with previous information.
COMMAND: CONTINUE Glyphosate is a widely used herbicide with low hazard potential to mammals, as established by all regulatory assessments since its introduction in 1974. However, in March 2015, the International Agency for Research on Cancer (IARC) concluded that glyphosate is probably carcinogenic. This conclusion was not confirmed by the European Union (EU) assessment or the recent joint WHO/FAO evaluation, both using additional evidence. Differences in the evaluation of the available evidence and the use of different data sets, particularly on long-term toxicity/carcinogenicity in rodents, may partially explain the divergent views. This review presents the scientific basis of the glyphosate health assessment conducted within the EU renewal process, explains the differences in the carcinogenicity assessment with IARC, and suggests that actual exposure levels are below reference values and do not represent a public concern. The EU assessment did not identify a carcinogenicity hazard, revised the toxicological profile, and conducted a risk assessment for some representative uses.

# Example 4
Doing: Reading relevant paper. Assuming papers are an authoritative and trustworthy source.
Command: READ 2

# Actual
Task: """

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
      prompt.append({"role":"assistant", "content":plan+control})
      continue # skip nothing to process

    # SEARCH
    if is_command(command,"SEARCH"):
      query = " ".join(command_params(command))
      urls = retry_search(query, num_results=6, advanced=True)
      urls_list = "\n\n".join([str(i+1) + ": " + url.url + "\n" + url.title + "\n" + url.description for i, url in enumerate(urls)])
      print(urls_list)
      prompt.append(usermsg("Search results:\n" + urls_list))

    # READ
    elif is_command(command,"READ"):
      url_n = command_param(command)
      url_n = re.search(r'\d+', url_n).group()
      url = urls[int(url_n) - 1].url
      print("Reading", url_n, url)
      text = get_article(url)
      print(text)
      if text.strip() != "":
        prompt.extend( [usermsg("Text: " + piece) for piece in chunk(text, max_tokens=max_tokens_convo, token_counter=token_count3)][:6] )

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

