import os
import json
from time import time, sleep
from uuid import uuid4
import datetime
import requests
import openai
import aiohttp

import pinecone

from flask import Flask, request, Response, stream_with_context, g
from flask_cors import CORS



# Initialize the OpenAI API key from environment variable

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY


# Initialize Pinecone API key from environment variable

PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
pinecone.init(api_key=PINECONE_API_KEY)

PINECONE_ENV = os.environ.get("PINECONE_ENV")


# Initialize Flask app instance

app = Flask(__name__)
CORS(app)

@app.before_first_request
def initialize_pinecone():
    pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)


def OpenAIStream(payload):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {OPENAI_API_KEY}'
    }

    with requests.post('https://api.openai.com/v1/chat/completions', headers=headers, data=json.dumps(payload), stream=True) as resp:
        for chunk in resp.iter_content(chunk_size=1024):
            if not chunk:
                break
            yield chunk


@app.route('/chat-test', methods=['POST'])
def chat_test():
    messages = request.json['messages']
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": messages,
        "temperature": 0.5,
        "top_p": 1,
        "n": 1,
        "stream": True
    }
    
    # call OpenAIStream function to generate text
    
    stream = OpenAIStream(payload)
    
    response_text = ""
    for chunk in stream:
        chunk_text = chunk.decode('utf-8')
        if chunk_text.startswith("data: "):
            response_json = json.loads(chunk_text[6:])
            if "choices" in response_json:
                content = response_json["choices"][0]["delta"]["content"]
                response_text += content

    return {"response": response_text}


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=12345)