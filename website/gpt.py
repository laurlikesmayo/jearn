from openai import OpenAI
# Set your OpenAI API key
from .models import Users, UserPreferences
from . import app, db
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
    gptans = []
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
            gptans.append(answer[0])
        else:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"Do not give an intro or an outro."},
                    {"role": "user", "content": f"Given this question {questions[i]}, give me a concise answer to that question"}]
            )
            answer = response.choices[0].message.content
            gptans.append(answer)

        
    return questions, choice, gptans

def checktest(userans, gptans, formats):
    correctans = []
    for i in range(len(userans)):
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a teacher checking a student's test. Print 1 if the answer is correct, 0 if it is wrong. Do not include an intro/outro/explanation."},
                {"role": "user", "content": f"Is the student's answer '{userans[i]}' along the same lines as the teacher's answer '{gptans[i]}'? If it is, print out 1; if it is not, print out 0."}
            ]
        )
        
        # Assuming response.choices[0].message.content contains the expected output
        check = response.choices[0].message.content.strip()  # Strip any extraneous whitespace
        correctans.append([check, gptans[i]])

    return correctans

def testsandw(correctans, userid, topic):
    score = 0
    for i in len(correctans):
        score += int(correctans[i][0])
        score = score/len(correctans)

    userpref = UserPreferences.query.filter_by(user_id=userid).first()

    if score>0.8 and topic not in userpref.strenghts:
        userpref.strengths.append(topic)
        if topic in userpref.weaknesses:
            userpref.weaknesses.remove(topic)
        db.session.commit
    elif topic not in userpref.weaknesses:
        userpref.weaknesses.append(topic)
        if topic in userpref.strengths:
            userpref.strengths.remove(topic)
        db.session.commit()
