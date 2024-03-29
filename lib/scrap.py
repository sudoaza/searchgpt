import os, sys, io, re
from googlesearch import search
import requests
from newspaper import Article
from bs4 import BeautifulSoup
import justext
from time import sleep
import pdftotext

def extract_text_from_pdf_binary(pdf_binary):
    pdf_file = io.BytesIO(pdf_binary)
    pdf = pdftotext.PDF(pdf_file)
    return "\n\n".join(pdf)

def get_article(url):
  headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Accept-Language': 'en-US,en;q=0.5',
  }
  backoff = 1
  while True:
    try:
      response = requests.get(url, headers=headers)
      if response.status_code == 404:
        return "404 Not Found"
      break
    except requests.exceptions.MissingSchema as e:
      return ""
    except Exception as e:
      print("Backoff\n" + str(e), file=sys.stderr)
      if backoff > 120:
        print("Quitting!")
        return ""
      sleep(backoff)
      backoff *= 2.72
  
  content_type = response.headers.get('content-type')
  if 'pdf' in content_type:
    pdf_content = response.content
    return extract_text_from_pdf_binary(pdf_content)
  else:
    html_content = response.content
    return extract_text(html_content)

# Make sure we extract article text from html
def extract_text(text):
  if isinstance(text, bytes):
    try:
      text = text.decode('utf-8')
    except Exception as e:
      try:
        text = text.decode('latin-1')
      except Exception as e:
        print("Failed to decode text.", file=sys.stderr)
        return ""

  # If not HTML return input
  if "<html" not in text.lower() and "<title" not in text.lower():
    return text

  # Newspaper library  
  article = Article("nourl", language="en")
  html = text
  article.set_html(html)
  article.parse()
  text = article.title + ".\n\n" + article.text + "\n\n"
  if article.authors and len(article.authors) > 0:
    text = text + "By " + ", ".join(article.authors) + ".\n"

  if len(article.text) > 50 and len(text)/len(html) > 0.005:
    return text
  
  # Justext
  text = ""
  paragraphs = justext.justext(html, justext.get_stoplist("English"))
  for paragraph in paragraphs:
    if not paragraph.is_boilerplate:
      # leave empty line after title
      if text == "":
        text += paragraph.text + "\n"
      else:
        text += paragraph.text

  if len(text) > 50 and len(text)/len(html) > 0.005:
    return text

  # Try <article> tag
  soup = BeautifulSoup(html, features="lxml")
  node = soup.find("article")
  if node:
    text = node.get_text("\n")

  if len(text) > 50 and len(text)/len(html) > 0.005:
    return text

  # Just dump all the text
  return soup.get_text("\n")

# Search in google and return the text of the first N results.
def do_search(query, num_results=10):
  answers = []
  for url in retry_search(query, num_results=num_results):
    answers.append( {"text": get_article(url), "source": url} )
  return answers

def retry_search(*args, **kwargs):
  backoff = 1
  while True:
    try:
      return [x for x in search(*args, **kwargs)]
    except (Exception, requests.exceptions.HTTPError) as e:
      print("Search error: ", e, file=sys.stderr)
      if backoff > 30:
        print("Quitting.", file=sys.stderr)
        break
      sleep(backoff)
      backoff *= 2.72

def clean_scrapy_text(text):
  return re.sub("[\n]{3,}","\n\n",text.strip())
