import requests

# Replace with your actual TikTok API credentials
client_id = 'awvelf0ikfg0jdj4'
client_secret = 'LEUaeHwtg4yGFb30TM2dGTKNJ8Zd9GIC'

# Step 1: Get access token using OAuth 2.0
auth_url = 'https://open-api.tiktok.com/oauth/access_token'
auth_data = {
    'client_id': client_id,  # Corrected parameter name
    'client_secret': client_secret,
    'grant_type': 'client_credentials'
}
auth_response = requests.post(auth_url, data=auth_data)
auth_data = auth_response.json()

access_token = auth_data.get('access_token')

# Step 2: Search for videos related to a topic
search_url = 'https://api.tiktok.com/video/search/'
query = 'strawberry chocolate'
params = {
    'count': 10,  # Number of videos to retrieve
    'keyword': query,
    'access_token': access_token
}

response = requests.get(search_url, params=params)
videos = response.json()

for video in videos.get('items', []):
    print(video['desc'], video['video']['downloadAddr'])