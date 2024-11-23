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