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

def maketest(prompt, subject, age, format):
    response = client.chat.completions.create(
    model = "gpt-3.5-turbo",
    messages = [
        {"role": "system", "content": f"You are a {subject} teacher creating a test. The level of the test should be for a {age} year old."},
        {"role": "system", "content":"after every question, can you put the word 'SPLITHERE' so i can split it in my python code?"},
        {"role": "system", "content": "do not include an intro, just start straight form the questions."},
        {"role": "user", "content": f"create a {format} test for the user about the topic {prompt}. After that, print the word 'ANSWERS' and list the answers. list the answers, and after each answer listed put the word 'SPLITHERE'"},
    ]
    )

    reply = response.choices[0].message.content
    reply = reply.split("ANSWERS")
    questions = reply[0].split("SPLITHERE")
    answers = reply[1].split('SPLITHERE')
    return questions, answers



print(maketest("cellular respiration", "science", 10, "written"))