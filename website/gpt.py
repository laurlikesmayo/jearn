from openai import OpenAI
# Set your OpenAI API key
api_key = "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"
# Create an OpenAI client instance
client = OpenAI(api_key = api_key)

def chat(prompt, age):
    response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are talking to a" + str(age) +"th grade person"},
        {"role": "user", "content": prompt},]
)
    return response.choices[0].message.content

