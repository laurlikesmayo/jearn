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
            {"role": "system", "content": f"You are a teacher creating a test about {prompt} in {format} format. The level of the test should be for a {age} year old."},
            {"role": "user", "content": "Generate a list of questions. Do not list any of the answers / mcq choices. Do not include an intro or outro."},
        ]
    )
    reply = response.choices[0].message.content
    questions = reply.split('\n')
    for i in range(len(questions)):
        if format.lower() == "mcq":
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": f"Given this question {questions[i]}, generate four answer choices. Format each choice as a letter followed by the option text, e.g., 'A. Option 1'. "}]
            )
            Qchoice = response.choices[0].message.content.split("\n")
            choice.append(Qchoice)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Do not give an intro or outro. Only list the letter of the correct answer and not the actual answer itself."},
                    {"role": "user", "content": f"Given this question: {questions[i]}, and given this list of possible answers: {Qchoice}, which letter is correct?"}]
            )
            answer = (response.choices[0].message.content).split(" ")
            answer = answer[0].split(".")
            answers.append(answer[0])
        else:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"Do not give an intro or an outro."},
                    {"role": "user", "content": f"Given this question {questions[i]}, give me a concise answer to that question"}]
            )
            answer = response.choices[0].message.content
            answers.append(answer)

        
    return questions, choice, answers




#print(maketest("cellular respiration", 10, "written"))