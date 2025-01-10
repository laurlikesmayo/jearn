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

def create_test(prompt, age, format, length=10):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    f"You are a teacher creating a test for a {age}-year-old student on the topic: '{prompt}'. "
                    f"Provide exactly {length} questions only in JSON format. Each question should be straightforward, "
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


def ddoetopic(userid):
    userpref = UserPreferences.query.filter_by(user_id=userid).first()
    previous_topics = []
    ddoe = DDOE.query.filter_by(user_id=userid).first()
    if ddoe:
        previous_topics = ddoe.previous_topics
    age = userpref.age

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a bot which only returns direct, one-word, short answers."},
            {"role": "user", "content": (
                f"Recommend one niche, specific, and interesting topic that a {age} year old should learn, "
                f"which is not {previous_topics}. \n\n"
                "Please respond in JSON format, like this:\n"
                "{'topic': 'your_topic_here'}.\n\n"
                "Examples can be:\n"
                "- 'photosynthesis'\n"
                "- 'economic systems'\n"
                "- 'quantum computing'."
            )}
        ]
    )
    
    # Extract the JSON string and convert it to a Python dictionary
    topic_response = response.choices[0].message.content.strip().replace("'", '"')
    topic = json.loads(topic_response)
    topic = topic["topic"]
    
    return topic
        

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
            {"role": "system", "content": f"You are an expert writer and researcher on the topic of {topic}. Your task is to craft a highly specific and original blog article for a {age}-year-old audience."},
            {"role": "user", "content": f"""
                Please generate the article in **valid JSON format** using the following structure:

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

                Guidelines:
                1. The article should focus on a **unique, niche aspect of {topic}** and avoid any overlap with previously written articles titled {previous_article_titles}.
                2. Provide practical examples, specific details, or recent developments to make the article engaging and insightful.
                3. Ensure the JSON output is strictly valid:
                    - No trailing commas.
                    - No unnecessary formatting like triple quotes, backticks, or language identifiers (e.g., `json`).
                    - Directly output the JSON structure.

                Write the article now and ensure it adheres to the JSON standard exactly as described.
            """}
        ]
    )

    # Retrieve raw content
    raw_response = response.choices[0].message.content

    # Post-process: Remove formatting artifacts
    sanitized_response = (
        raw_response.strip("'''")
        .strip('"""')
        .strip('```')
        .strip('json')
    )

    # Additional cleanup for trailing commas
    sanitized_response = sanitized_response.replace(",\n}", "\n}").replace(",\n]", "\n]")

    try:
        # Parse and return valid JSON
        parsed_response = json.loads(sanitized_response)
        return parsed_response
    except json.JSONDecodeError as e:
        # If parsing fails, raise an error with the raw response
        raise ValueError(f"JSON decoding failed. Raw response: {sanitized_response}") from e




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

def ddoeword():
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"You are an english robot which spits out one english vocabulary word at a time. "},
            {"role": "user", "content": f"Generate a (slightly challenging) random vocabulary word that someone can learn"}
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




