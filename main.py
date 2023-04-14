import os
import json
from time import time, sleep
from uuid import uuid4
import datetime
import requests
import openai
import aiohttp
import traceback
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



@app.route('/chat', methods=['POST'])
def chat():
    messages = request.json['messages']
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": messages,
        "temperature": 0.5,
        "top_p": 1,
        "n": 1,
        "stream": True
    }

    stream = OpenAIStream(payload)

    def generate():
        for chunk in stream:
            if not chunk:
                print("Empty chunk received")
                continue

            chunk_str = chunk.decode('utf-8')
            print(f"Chunk received: {chunk_str}")

            try:
                decoded_chunk = json.loads(chunk_str)
            except json.JSONDecodeError as e:
                print(f"JSONDecodeError: {e}")
                continue

            if "choices" in decoded_chunk:
                choices = decoded_chunk["choices"]
                if choices:
                    assistant_message = choices[0].get("message", {}).get("content", "")
                    yield f"data: {assistant_message}\n\n"
    return Response(stream_with_context(generate()),mimetype='text/event-stream')




if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=12345)