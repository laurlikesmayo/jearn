import openai
from .models import Users, UserPreferences, DDOE

from . import app, db
from random import randrange
from dotenv import load_dotenv
import os

def configure():
    load_dotenv()

# Create an OpenAI client instance
configure()
api_key = os.getenv('api_key')
client = openai.OpenAI(api_key=api_key)

def chat(prompt, age, language): 
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"talk in {language}"},
            {"role": "system", "content": f"You are talking to a {age} year old person"},
            {"role": "user", "content": prompt},
        ]
    )
    return response.choices[0].message.content

def create_test(prompt, age, format):
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
                messages=[{"role": "user", "content": f"Given this question '{questions[i]}', generate four answer choices. Format each choice as a letter followed by the option text, e.g., 'A. Option 1'."}]
            )
            Qchoice = response.choices[0].message.content.split("\n")
            choice.append(Qchoice)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Do not give an intro or outro. Only list the letter of the correct answer and not the actual answer itself."},
                    {"role": "user", "content": f"Given this question: '{questions[i]}', and given this list of possible answers: {Qchoice}, which letter is correct?"}]
            )
            answer = response.choices[0].message.content.split(" ")
            answer = answer[0].split(".")
            gptans.append(answer[0])
        else:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Do not give an intro or an outro."},
                    {"role": "user", "content": f"Given this question '{questions[i]}', give me a concise answer to that question"}]
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
        check = response.choices[0].message.content.strip()  # Strip any extraneous whitespace
        correctans.append([check, gptans[i]])

    return correctans

def testsandw(correctans, userid, topic):
    score = sum(int(ans[0]) for ans in correctans) / len(correctans)
    print(score)
    userpref = UserPreferences.query.filter_by(user_id=userid).first()
    strengths = userpref.strengths
    weaknesses = userpref.weaknesses
    if score > 0.7:
        if topic not in strengths:
            strengths.append(topic)
        if topic in weaknesses:
            weaknesses.remove(topic)
    else:
        if topic not in weaknesses:
            weaknesses.append(topic)
        if topic in strengths:
            strengths.remove(topic)
    userpref.strengths = strengths
    userpref.weaknesses = weaknesses

    db.session.commit()

def strengthrec(userid):
    userpref = UserPreferences.query.filter_by(user_id=userid).first()
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Please don't add an intro, outro, or explanation, just return what is asked."},
            {"role": "user", "content": f"Given that a student is very strong at {userpref.strengths}, recommend a topic that you think this student would be good at."}
        ]
    )
    return response.choices[0].message.content.strip()

def weakrec(userid):
    userpref = UserPreferences.query.filter_by(user_id=userid).first()
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Please don't add an intro, outro, or explanation, just return a direct answer to what is asked."},
            {"role": "user", "content": f"Given that a student is very weak at {userpref.weaknesses} topics, which topic is most crucial and important that the student should learn?"}
        ]
    )
    return response.choices[0].message.content.strip()


def ddoetopic(userid, num):
    userpref = UserPreferences.query.filter_by(user_id=userid).first()
    previous_topics = []
    ddoe = DDOE.query.filter_by(user_id=userid).first()
    if ddoe:
        previous_topics = ddoe.previous_topics
    strengths = userpref.strengths
    age = userpref.age
    
    weaknesses= userpref.weaknesses
    #0 = learn new, 1 = revise, 2 = continue off strength
    if num==1 and strengths:
        response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a bot which only returns direct, short answers to what is asked."},
            {"role": "user", "content": f"A {age} year old user is interested in {strengths}. Return one specific and niche topic that they should learn."}
        ]
        )
        return response.choices[0].message.content.strip()
    elif num == 2 and weaknesses:
        response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a bot which only returns direct, short answers to what is asked.."},
            {"role": "user", "content": f"pick a random topic from {weaknesses}"}
        ]
        )
        return response.choices[0].message.content.strip()
    else:
        response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a bot which only returns direct, one-word, short answers."},
            {"role": "user", "content": f"Recommend one specific and niche academic topic that a {age} year old should learn, which is not {previous_topics}. Examples can be, 'photosynthesis', 'cellular biology', 'object oriented programming'. "}
        ]
        )
        return response.choices[0].message.content.strip()
        

def ddoedescription(userid, topic):
    userpref = UserPreferences.query.filter_by(user_id=userid).first()
    age = userpref.age
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Please don't add an intro or an outro, just return a direct answer to what is asked."},
            {"role": "user", "content": f"Give a brief description to a {age} year old about {topic}. Then, return a paragraph teaching the basics of {topic}"}
        ]
    )
    return response.choices[0].message.content.strip()

def ddoeexamples(userid, topic):
    userpref = UserPreferences.query.filter_by(user_id=userid).first()
    age = userpref.age
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Please don't add an intro, outro, or explination, just return a direct answer to what is asked."},
            {"role": "user", "content": f"Give an {age} year old some real life examples of {topic}."}
        ]
    )
    return response.choices[0].message.content.strip()

def keywords(topic):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Please don't add an intro, outro, or explination, a direct answer to what is asked. "},
            {"role": "system", "content": "Do not add any punctuation, (eg '.', ',') or numbering (eg 1. 2.). Return all values on the same line"},

            {"role": "user", "content": f"Generate a list of 3-4 keywords related to {topic}. After each keyword listed, add the word SPLIT"}
        ])
    keywords = response.choices[0].message.content.strip()
    keywords = keywords.split('SPLIT')
    return keywords

def summary(articletext):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Please don't add an intro, outro, or explination, just return a direct answer to what is asked."},
            {"role": "user", "content": f"Give a 25-word summary of this article: {articletext}."}
        ]
    )
    return response.choices[0].message.content.strip()

def ddoearticle(topic, age, previous_article_titles):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"You are an expert at the topic {topic}. You are writing a super interesting blog article about your SPECIFIC EXPERIENCES/EXAMPLES with the topic {topic}"},
            {"role": "system", "content": f"Write the article on a very nieche area of the topic {topic}, but make sure it is NOT ABOUT about {previous_article_titles}."},
            {"role": "user", "content": f"Generate this article for a {age} year old. After the title, put the word 'SPLITHERE'. Do NOT include any words in bold (or asteriods **)"}
        ]
    )
    response = response.choices[0].message.content.split("SPLITHERE")
    try:
        title = response[0].split('Title: ')
        response[0] = "".join(title[1])

    except:
        pass
    return response

def generate_image(prompt, n=1, size="320x180"):
    # Request image generation from DALL-E
    response = openai.Image.create(
        prompt=prompt,
        n=n,
        size=size
    )
    # Extract image URL from the response
    image_url = response['data'][0]['url']
    return image_url

def ddoeword(user_id):
    pref = UserPreferences.query.filter_by(user_id = user_id).first()
    age = pref.age
    ddoe = DDOE.query.filter_by(user_id = user_id).first()
    if not ddoe:
        previous_words = []
    else:
        previous_words = ddoe.previous_words
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"You are an english robot which spits out one english vocabulary word at a time. "},
            {"role": "user", "content": f"Generate a word that a {age} year old should learn, which is not the words {previous_words}"}
        ]
    )
    return response.choices[0].message.content

def ddoedefinition(word):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": f"Give me the definition of {word}"}
        ]
    )
    return response.choices[0].message.content

