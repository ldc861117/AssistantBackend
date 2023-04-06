import os
import openai
import json
from uuid import uuid4
import pinecone
import aiohttp
from quart import Quart, request, Response
import asyncio

# Initialize the OpenAI API
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Initialize the Pinecone API
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
pinecone.init(api_key=PINECONE_API_KEY)

# Initialize the Quart app
app = Quart(__name__)

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
async def chat():
    prompt = (await request.json)['prompt']
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

    async def generate(response):
        async for chunk in stream:
            await response.write(chunk.decode('utf-8'))

    return Response(stream_with_context(generate), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=12345)
