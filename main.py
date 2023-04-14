import os
import json
from time import time
import openai
import pinecone

from flask import Flask, request, Response
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

@app.route('/chat', methods=['POST'])
def chat():
    messages = request.json['messages']
    stream = request.json.get('stream', False)  # Get the 'stream' parameter, default to False
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.5,
        top_p=1,
        n=1,
        stream=True
    )

    collected_messages = []

    def generate():
        for chunk in response:
            chunk_message = chunk['choices'][0]['delta']
            collected_messages.append(chunk_message)
            content = chunk_message.get('content', '').strip()
            if content != "":
                yield f"data: {content}\n\n"
        yield "data: [DONE]\n\n"
    if stream:
        return Response(generate(), content_type='text/event-stream')
    else:
        # If 'stream' is False, return the entire string
        for chunk in response:
            chunk_message = chunk['choices'][0]['delta']
            collected_messages.append(chunk_message)
        content = ''.join([msg.get('content', '') for msg in collected_messages])
        return {'content': content}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=12345)