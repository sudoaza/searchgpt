# SearchGPT

Has the same API as the regular complete, it accepts a prompt and gives an answer.

- Asks the LLM to provide search queries to answer a prompt.
- Gets some results from the queries.
- Scraps the text from the results.
- Sintetizes the text keeping only the relevant information.
- Answers the prompt with the information as context.

Expect around 3 minutes for an answer and 20 requests to OpenAI.