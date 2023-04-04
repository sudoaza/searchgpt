#!/usr/bin/env -S python3 -u

import os, sys, re

from googlesearch import search
from lib.scrap import get_article
from lib.easy_openai import *

# @TODO response max token hardcoded to 1000 and model max token hardcoded to 4096

complete_prompt = """Answer requests truthfully.

Answer this request taking into account the provided information and any other knowledge you have access to.

When appropriate provide quotes with relevant information providing the source in this format.

"Text literally copied from the original source of information"
Source: http://www.source.com/article

Request: """
complete_scaffold = "\n\nRelevant information:\n"
complete_tokens = token_count(complete_prompt + complete_scaffold)
def complete_with_sources(prompt):
  queries = generate_search_queries(prompt)
  corpus = ""
  # Do only 2 search queries, thats usually enough info.
  for query in queries[:2]:
    results = do_search(query, num_results=3)
    for result in results:
      sintesis = sintetize(prompt, result["text"])
      corpus += sintesis + "\nSource: " + result["source"] + "\n\n"

  base_token_count = complete_tokens + token_count(prompt) + 1000 
  max_tokens = 4096 - base_token_count
  sintesis_count = 0
  while token_count(corpus) > max_tokens:
    corpus = sintetize(prompt, corpus)
    sintesis_count += 1
    if sintesis_count > 3:
      corpus = truncate(corpus, max_tokens=max_tokens)
      break

  debug("O")
  return complete(complete_prompt + prompt + "\n\nRelevant information:\n" + corpus + "\n\n")


search_prompt = """Produce search queries to find relevant information to a request.

Create 3 search queries that can be run in a search engine like Google or Bing and will find relevant information to answer a particular information request.
The results of this search queries should contain information necesary to correctly answer the request.
Notice the request can be a simple question or a complex task.

Provide the answer in this format:

- First search query
- Second search query
- Third search query

# Example

Request: How to play starcraft?

- How to play starcraft?
- Starcraft tutorials
- Starcraft guide

# Real

Request: """
def generate_search_queries(original_query):
  debug("O")
  response = complete(search_prompt + original_query.strip() + "\n\n- ")
  return re.findall(r'^- (.+)', response, flags=re.MULTILINE)


sintetize_prompt = """Sintetize information relevant to a query.

Sintetize the information provided under the request text keeping only the parragraphs or lines that can help answer, complete, confirm, correct or reject the request query and ignore those that are not relevant.
The selected parragraphs or lines should be reproduced literally and completely. No new information should be created, only extracts from the original text.
Avoid lines or parragraphs that are redundant, duplicated or that provide the same ideas or concepts without any new information keeping only the most relevant ones.
Keep all the source URLs (lines starting with "Source: ") that follow relevant information to be kept.

# Format

Query: One or many text lines with the query.
Text:
Many lines of text that could be relevant to answer the query.
Source: URL

Response:
Selected lines from the text that are relevant to answering the query.

# Example

Query: Known pizza types
Text:
Chocolate icecream
Pizza diavola
Pizza margherita
Red wine
Cotto e funghi pizza

Response:
Pizza diavola
Pizza margherita
Cotto e funghi pizza

# Request

"""
sintetize_scaffold = "Query: \nText:\n\n\nResponse:\n"
sintetize_tokens = token_count(sintetize_prompt + sintetize_scaffold)
def sintetize(query, text):
  def doit(query, text):
    debug("O")
    return complete(
      sintetize_prompt + 
      "Query: " + query.strip() + 
      "\nText:\n" + text.strip() +
      "\n\nResponse:\n",
      best_of=1
    )
  sintesis = ""
  base_token_count = sintetize_tokens + token_count(query) + 1000
  left = text
  sintesis_count = 0
  while len(left) > 0:
    sintesis_count += 1
    chunk = truncate(left, max_tokens=4096-base_token_count)
    left = left[min(len(chunk)+1,len(left)):] # For all chunks but the last we need to cut the separator too
    sintesis += doit(query, chunk)
    if sintesis_count > 3:
      break
  return sintesis

sgpt_debug = os.environ.get('DEBUG',"0") == "1"

def debug(msg, end=""):
  if sgpt_debug:
    print(msg, end=end, file=sys.stderr)

def err(msg):
  print(msg, file=sys.stderr)

# Search in google and return the text of the first N results.
def do_search(query, num_results=10):
  debug("S")
  answers = []
  for url in retry_search(query, num_results=num_results):
    debug(".")
    answers.append( {"text": get_article(url), "source": url} )
  return answers

def retry_search(*args, **kwargs):
  backoff = 1
  while True:
    try:
      return search(*args, **kwargs)
    except Exception as e:
      err("Search error: ", e)
      if backoff > 30:
        err("Quitting.")
        break
      backoff *= 2.72


if __name__ == "__main__":
  if len(sys.argv) < 2:
    print(f"Usage: python {os.path.basename(__file__)} <prompt>")
    sys.exit(1)

  prompt = sys.argv[1]
  print( complete_with_sources(prompt) )