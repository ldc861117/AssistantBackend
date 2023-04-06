import os
import openai
import atexit
import json
from time import time,sleep
from uuid import uuid4
import datetime
import pinecone
from flask import Flask, request, Response, stream_with_context

# Initialize the OpenAI API
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Initialize the Pinecone API
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
pinecone.init(api_key=PINECONE_API_KEY)

# Initialize the Flask app
app = Flask(__name__)

async def OpenAIStream(payload):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {OPENAI_API_KEY}'
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post('https://api.openai.com/v1/chat/completions', headers=headers, data=json.dumps(payload)) as resp:
            while True:
                chunk = await resp.content.read(1024)
                if not chunk:
                    break
                yield chunk

@app.route('/chat', methods=['POST'])
def chat():
    prompt = request.json['prompt']
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5,
        "top_p": 1,
        "n": 1,
        "stream": True
    }
    
    # call OpenAIStream function to generate text
    
    stream = OpenAIStream(payload)
    
    def generate():
      for chunk in stream:
          yield chunk.decode('utf-8')
          
    return Response(stream_with_context(generate()), mimetype='text/event-stream')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=12345)
