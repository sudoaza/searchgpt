from lib.scrap import get_article
from lib.easy_openai import *

# @TODO response max token hardcoded to 1000 and model max token hardcoded to 4096

complete_prompt = """Answer requests truthfully.

Answer this request taking into account the provided information and any other knowledge you have access to.

When appropriate provide quotes with relevant information providing the source in this format.

Text literally copied from the original source of information
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
    if sintesis_count > 1:
      corpus = truncate(corpus, max_tokens=max_tokens)
      break

  return complete(complete_prompt + prompt + "\n\nRelevant information:\n" + corpus + "\n\n")


search_prompt = """Produce search queries to find relevant information to a request.

Create 3 search queries that can be run in a search engine like Google or Bing and will find relevant information to answer a particular information request.
The results of this search queries should contain information necesary to correctly answer the request.
Notice the request can be a simple question or a complex task.

Provide the answer in this format:

- First search query
- Second search query
- Third search query

# Examples

Request: How to play starcraft?

- How to play starcraft?
- Starcraft tutorials
- Starcraft guide

Request: Exploits for apache 2.4.41

- Exploits apache 2.4.41
- Vulnerabilities apache 2.4
- Bug fixes apache 2.4.42

# Real

Request: """
def generate_search_queries(original_query):
  response = complete(search_prompt + original_query.strip() + "\n\n")
  return re.findall(r'^- (.+)', response, flags=re.MULTILINE)

sintetize_prompt = """Sintetize information relevant to a query.

Sintetize the information provided under the request text keeping the parragraphs or lines that can help answer, complete, confirm, correct or reject the request query.
Ignore content that is not relevant but you can keep content that helps give context to relevant information.
For example keeping the previous line or the complete parragraph.

The selected parragraphs or lines should be reproduced literally and completely.
Avoid lines or parragraphs that are redundant, duplicated or that dont add new important information or details. You can ignore content and copyright warnings.
Keep all the source URLs (lines starting with "Source: ") that follow relevant information to be kept.

# Format

Query: One or many text lines with the query.
Text:
Many lines of text that could be relevant to answer the query.
Source: URL

Response:
Selected lines from the text that are relevant to answering the query.

# Example

Query: Exploits apache 2.4.41
Text:
Searching exploits for apache 2.4
Apache 2.4.17 < 2.4.38 - 'apache2ctl graceful' 'lo | linux/local/46676.php
Apache < 2.2.34 / < 2.4.27 - OPTIONS Memory Leak   | linux/webapps/42745.py
Apache HTTP Server 2.4.49 - Path Traversal & Remot | multiple/webapps/50383.sh
Apache HTTP Server 2.4.50 - Remote Code Execution  | multiple/webapps/50512.py
Apache Tomcat 3.2.3/3.2.4 - 'RealPath.jsp' Informa | multiple/remote/21492.txt
Source: searchsploit

Response:
Searching exploits for apache 2.4
Apache HTTP Server 2.4.49 - Path Traversal & Remot | multiple/webapps/50383.sh
Apache HTTP Server 2.4.50 - Remote Code Execution  | multiple/webapps/50512.py
Source: searchsploit

# Request
"""
sintetize_scaffold = "Query: \nText:\n\n\nResponse:\n"
sintetize_tokens = token_count(sintetize_prompt + sintetize_scaffold)
def sintetize(query, text):
  def doit(query, text):
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
    sintesis += doit(query, chunk) + "\n"
    if sintesis_count > 1:
      break
  return sintesis

choose_page_prompt = """Which of this web pages are the most likely to have the answer to this request?

Anwer in this format:
- http://example.com/url-of-top-candidate
- http://example2.com/url-of-other-candidate
- http://example3.com/no-more-than-3

Request: """
chopse_scaffold = "\n\nWeb Pages:\n\n\nResponse:\n"

def choose_articles(query, urls):
  prompt = choose_page_prompt + "Request: " + query.strip() + "\nWebpages:\n" + urls.strip() + "\n\nResponse:\n"
  response = complete(prompt)
  return re.findall(r'^- (.+)', response, flags=re.MULTILINE)
