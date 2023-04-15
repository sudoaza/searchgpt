import os
import openai

from transformers import GPT2TokenizerFast, logging

logging.set_verbosity_error()

# Set up the OpenAI API credentials
openai.api_key = os.environ['OPENAI_API_KEY']

cached_tokenizer = None

def gpt2_tokenizer():
  global cached_tokenizer
  if cached_tokenizer is None:
    cached_tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
  return cached_tokenizer

def token_count(text):
  tokenizer = gpt2_tokenizer()
  token_dict = tokenizer(text)
  return len(token_dict['input_ids'])

def truncate(text, max_tokens=4096, split_str="\n"):
  keep = ""
  for piece in text.split(split_str):
    if token_count(keep + split_str + piece) > max_tokens:
      break
    keep += split_str + piece
  return keep

def chunk(text, max_tokens=4096, split_str="\n"):
  chunks = []
  while len(text) > 0:
    chunk = truncate(text, max_tokens=max_tokens, split_str=split_str)
    text = text[len(chunk):]
    if len(chunk) < 3:
      break
    chunks.append(chunk)
  return chunks

# Call Openai completion API.
def complete(prompt, max_tokens=1000, temperature=0.7, model='text-davinci-003', best_of=3):
  api_params = {
    'engine': model,
    'prompt': prompt,
    'temperature': temperature,
    'max_tokens': max_tokens,
    'best_of': best_of,
  }
  for _ in range(3):
    try:
      response = openai.Completion.create(**api_params)
      generated_text = response.choices[0].text
      return generated_text
    except openai.error.APIConnectionError as e:
      pass
  raise e

def truncate_and_complete(prompt, max_tokens=1000, temperature=0.7, model='text-davinci-003', best_of=3, model_max_tokens=4096, split_str="\n"):
  truncated_prompt = truncate(
    prompt,
    max_tokens=model_max_tokens-response_max_tokens,
    split_str=split_str
  )
  return complete(
    truncated_prompt,
    max_tokens=max_tokens,
    temperature=temperature,
    model=model,
    best_of=best_of
  )


def usermsg(msg):
  return {"role":"user","content":msg}

def agentmsg(msg):
  return {"role":"assistant","content":msg}

def chat_complete(prompt, system="You are a helpful assistant."):
  if type(prompt) == str:
    prompt = [{"role": "system", "content": system }, usermsg(prompt)]

  response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=prompt)
  response_text = response.choices[0].message.content
  prompt.append(agentmsg(response_text))
  return prompt, response_text