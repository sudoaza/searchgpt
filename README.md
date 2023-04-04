# SearchGPT

Has the same API as the regular complete, it accepts a prompt and gives an answer.

- Asks the LLM to provide search queries to answer a prompt.
- Gets some results from the queries.
- Scraps the text from the results.
- Sintetizes the text keeping only the relevant information.
- Answers the prompt with the information as context.

Expect around 3 minutes for an answer and 20 requests to OpenAI.

It currently uses text-davinci-003 model, equivalent to GPT2 because when I did this the Chat API and GPT3.5 model were not public.
You can easily burn through your free API credits using this.

## Usage

    DEBUG=1 ./searchgpt.py "Name all the Klingons killed by Worf, son of Mogh"

## Installation

    pip install -r requirements.txt