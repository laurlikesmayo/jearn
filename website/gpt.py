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

def maketest(prompt, age, format):
    choice = []
    answers = []
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"You are a teacher creating a test. The level of the test should be for a {age} year old."},
            {"role": "system", "content": f"create a {format} test for the user about the topic {prompt}. "},
            {"role": "user", "content": "first, give me the list of questions (NOT NUMBERED)"},
        ]
    )
    reply = response.choices[0].message.content
    questions = reply.split('\n')
    for i in range(len(questions)):
        if format.lower() == "mcq":
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": f"Given this question {questions[i]}, give me a list of multiple choice answers,"}]
            )
            Qchoice = response.choices[0].message.content.split("\n")
            choice.append(Qchoice)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"GIVE ME NO EXPLINATION, INTRO, OR WHATEVER. JUST GIVE ME PURELY WHAT I ASK FOR BELOW"},
                    {"role": "user", "content": f"Given this question {questions[i]}, and given this list of possible answers {Qchoice}, return me the INDEX of which answer is correct in the list"}]
            )
            answer = (response.choices[0].message.content).split("Index")
            answers.append(answer)
        else:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"GIVE ME NO EXPLINATION, INTRO, OR WHATEVER. JUST GIVE ME PURELY WHAT I ASK FOR BELOW"},
                    {"role": "user", "content": f"Given this question {questions[i]}, give me the answer to that question"}]
            )
            answer = (response.choices[0].message.content)
            answers.append(answer)

        
    return questions, choice, answers




print(maketest("cellular respiration", 10, "mcq"))