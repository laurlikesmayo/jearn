from openai import OpenAI
# Set your OpenAI API key
from dotenv import load_dotenv
import os
def configure():
    load_dotenv()
# Create an OpenAI client instance
configure()
api_key = os.getenv('api_key')
client = OpenAI(api_key = api_key)

def chat(prompt, age, language): 
    response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "talk in" + language},
        {"role": "system", "content": "You are talking to a" + str(age) +"year old person"},
        {"role": "user", "content": prompt},]
)
    return response.choices[0].message.content

