from groq import Groq
import os
from prompts import system_prompt


key = os.getenv("GROQ_API_KEY")


def analyze_code(file_content , file_name):
    prompt = f"""
  You are an expert code reviewer. Carefully analyze the following code and provide a detailed review.

  Focus on:
  - Code Style & Formatting
  - Correctness & Bugs
  - Performance Improvements
  - Best Practices
  - Actionable Suggestions

  File Name: {file_name}

  Code Content:
  {file_content}

  Now, provide a detailed JSON output with the following structure:

  {{
    "issues": [
      {{
        "type": "<style|bugs|performance|best_practice>",
        "line": <line_number>,
        "description": "<short description of the issue>",
        "suggestion": "<actionable fix or improvement>"
      }}
    ]
  }}
  """

    client = Groq(api_key=key)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
           {'role': 'system', 'content': system_prompt},
            {"role": "user", "content": prompt}
        ],
        top_p=1,
        response_format={
            "type": "json_object"
        },
        temperature = 1
    )

   
    result = response.choices[0].message.content.strip()
    return result





