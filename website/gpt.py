import openai
from .models import Users, UserPreferences, DDOE

from . import app, db
from random import randrange
import random
import json
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
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    f"You are a teacher creating a test for a {age}-year-old student on the topic: '{prompt}'. "
                    f"Provide exactly 10 questions only in JSON format. Each question should be straightforward, "
                    "not open-ended, and should have a single, unambiguous correct answer. Do not include the answer choices"
                )
            },
            {
                "role": "user",
                "content": """
                    Generate a JSON object containing exactly 10 questions with the following structure:

                    {
                        "questions": [
                            "question 1", "question 2", "question 3" ...
                        ]
                    }

                    Only provide the 10 questions, formatted as JSON. Do not include any answer options.
                """
            }
        ]
    )
    response = response.choices[0].message.content
    questions_data = json.loads(response)
    questions = questions_data['questions']

    questions_with_choices = {}
    for question in questions:   
        if format.lower() == "mcq":
            # Make a request to generate answer choices
            choices_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Given this question '{question}', generate one correct answer and three incorrect options.  "
                            "Make sure to provide just the options, no additional text or number index. Provide the answers in JSON format, and structure the response like this:\n"
                            '{"correct": "Correct Option", "incorrect": ["Incorrect Option 1", "Incorrect Option 2", "Incorrect Option 3"]}'
                        )
                    }
                ]
            )
            
            # Process the choices response
            choices_content = choices_response.choices[0].message.content
            choices_data = json.loads(choices_content)

            # Prepare answer choices
            correct_answer = choices_data.get("correct")
            incorrect_answers = choices_data.get("incorrect", [])
            
            # Combine and shuffle the choices
            all_answers = incorrect_answers + [correct_answer]
            random.shuffle(all_answers)

            # Add question and choices to the dictionary
            questions_with_choices[f"{question}"] = {
                "choices": all_answers,
                "correct_answer": correct_answer  # Store the correct answer
            }
        else:
            written_answer_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages = [
                    {
                        "role": "user",
                        "content": (
                            f"Given the question '{question}', provide the correct answer in JSON format like this: "
                            '{ "correct_answer": "your_answer" }.'
                        ) 
                    }
                ]
            )
            written_answers_content = written_answer_response.choices[0].message.content
            written_answers_data = json.loads(written_answers_content)
            written_answer = written_answers_data.get("correct_answer")
            print(written_answer)
            questions_with_choices[f"{question}"] = {
                "correct_answer": written_answer
            }
    
    return questions_with_choices
#never access question by the index but access by the question itself. 
#make userans a dictionary (questionanswers) of dic[question][user_answer] = 'userans', dic[question][gptans] = blank, dic[question][correctans] = blank
def checktest(questionsanswers, formats, questions, questions_with_choices=None):
    if formats =='mcq':
        for question in questions:
            questionsanswers[question]['correct_answer'] = questions_with_choices[question]['correct_answer']
            if questionsanswers[question]['user_answer'] == questionsanswers[question]['correct_answer']:
                questionsanswers[question]['is_correct'] = 1
            else:
                questionsanswers[question]['is_correct'] = 0
    else:
        for question in questions:
            correct_answer = questionsanswers[question]['correct_answer'] = questions_with_choices[question]['correct_answer']
            user_answer = questionsanswers[question]['user_answer']
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a teacher evaluating a student's written answer. "
                            "Please assess whether the student's response accurately answers the following question: "
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Evaluate the student's answer: '{user_answer}' for the question: '{question}'. "
                            "If the answer is correct or reasonably accurate, respond with 1; "
                            "if it is incorrect or not sufficiently accurate, respond with 0. "
                            "Do not provide any additional explanations or comments."
                        )
                    }
                ]
            )
            check = response.choices[0].message.content.strip() 
            print(check) # Strip any extraneous whitespace
            if user_answer ==correct_answer:
                check = 1
            print( check)
            questionsanswers[question]['is_correct'] = int(check)


    return questionsanswers

def testsandw(questionanswers, userid, topic):
    print(questionanswers)
    correct_count = sum(1 for question in questionanswers if questionanswers[question]['is_correct'] == 1)


    score = (correct_count / len(questionanswers))
    print(score)
    userpref = UserPreferences.query.filter_by(user_id=userid).first()
    strengths = userpref.strengths
    weaknesses = userpref.weaknesses
    if score >= 0.6:
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
    return score

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
            {"role": "user", "content": f"Recommend one niche, specific, and interesting topic that a {age} year old should learn, which is not {previous_topics}. Examples can be, 'photosynthesis', 'economic systems', 'quantam comoputing'. "}
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
                {"role": "system", "content": f"You are an expert in the topic of {topic}. You are writing an insightful and unique blog article that draws on specific and nuanced experiences within this topic."},
                {"role": "system", "content": f"Write an article on a highly niche and specific aspect of {topic}. Ensure that it is distinct from previous articles titled {previous_article_titles}. This article is written for a {age} year old"},
                {"role": "user", "content": f"""
                    Please generate the article in JSON format with the following structure:

                    {{
                        "title": "string",
                        "content": {{
                            "introduction": "string",
                            "sections": [
                                {{
                                    "section_title": "string",
                                    "section_content": "string"
                                }}
                            ],
                            "conclusion": "string"
                        }}
                    }}

                    Write an article about a unique perspective on "{topic}", specifically focusing on an innovative or lesser-known area within the field. Be sure the article is not similar to the topics previously covered ({previous_article_titles}). Provide practical examples or recent developments, and format it according to the JSON structure above.
                """}
            ]        
    )
    response = response.choices[0].message.content
    response = json.loads(response)
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




