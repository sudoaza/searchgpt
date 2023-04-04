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

# Call Openai completion API.
def complete(prompt, max_tokens=1000, temperature=0.7, model='text-davinci-003', best_of=3):
  api_params = {
    'engine': model,
    'prompt': prompt,
    'temperature': temperature,
    'max_tokens': max_tokens,
    'best_of': best_of,
  }
  response = openai.Completion.create(**api_params)
  generated_text = response.choices[0].text
  return generated_text

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
