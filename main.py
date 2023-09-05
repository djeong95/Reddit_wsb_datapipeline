import requests
import os
import json
import pandas as pd
from dotenv import load_dotenv

def extract_reddit_posts(posts):
    """
    Extract fields from Reddit posts to loop through Reddit API comments. Filters for a score better than 5.

    Parameters:
    - posts (dict): The Reddit posts data in dictionary form. Typically includes fields like 'author', 'name','title',etc.
    Returns:
    - data (list): A list of dictionaries containing the extracted fields from each Reddit post that meets the criteria.
    Example usage:
    reddit_posts = extract_reddit_posts(posts_response.json()['data']['children'])
    """
    data = []
    for post in posts:
        post_dict = {}
        
        if (post['data']['subreddit'] == 'wallstreetbets') and (post['data']['score'] > 5):
            post_dict['kind'] = post['kind']
            post_dict['author'] = post['data']['author']
            post_dict['id'] = post['data']['id']
            post_dict['subreddit'] = post['data']['subreddit']
            post_dict['link_flair_text'] = post['data']['link_flair_text']
            post_dict['title']= post['data']['title']
            post_dict['selftext']= post['data']['selftext']
            post_dict['created_utc']= post['data']['created_utc']
            post_dict['num_comments']= post['data']['num_comments']
            post_dict['score']= post['data']['score']
            post_dict['upvote_ratio']= post['data']['upvote_ratio']

            data.append(post_dict)
    return data

def extract_reddit_commentpost(post):
    """
    Extract fields from Reddit posts to be used on extracting Reddit comments. Used with Reddit API comments.

    Parameters:
    - post (dict): The Reddit post data in dictionary form. Typically includes fields like 'author', 'name','title',etc.
    Returns:
    - data (list): A list of dictionaries containing the extracted fields from each Reddit post that meets the criteria.
    - link_flair_text (str): Type of post in wallstreetsbets subreddit. Ex. 'DD', 'Discussion', 'Meme', 'YOLO'
    - id (str): The id of the post used to extract Reddit comments
    Example usage:
    post_detail, post_link_flair_text, post_id = extract_reddit_commentpost(post)
    """
    data = []
    post_dict = {}
    if post['data']['subreddit'] == 'wallstreetbets':
        post_dict['author'] = post['data']['author']
        post_dict['id'] = post['data']['name']
        post_dict['created_utc']= post['data']['created_utc']
        post_dict['body']= post['data']['title']
        post_dict['score']= post['data']['score']
        post_dict['link_flair_text'] = post['data']['link_flair_text']
        post_dict['post_link_id'] = post['data']['id']

    data.append(post_dict)
    return data, post['data']['link_flair_text'], post['data']['id']

def extract_reddit_comments(data, link_flair_text, name, fields=('author' ,'id', 'created_utc', 'body', 'score')):
    """
    Extract specified fields from Reddit comments and their nested replies.

    Parameters:
    - data (dict): The Reddit comment data in dictionary form. Typically includes fields like 'author', 'body', etc.
    - link_flair_text: The Reddit post type that comment is from. Example: "YOLO", "Meme", "Gains", "Discussion"
    - name: The Reddit post name to link the comment to. 
    - fields (tuple): The fields to extract from each Reddit comment. Default is ('author', 'id', 'created_utc', 'body', 'score').
    
    Returns:
    - results (list): A list of dictionaries containing the extracted fields from each Reddit comment that meets the criteria.
    
    Example usage:
    extracted_comments = extract_reddit_comments(reddit_data, fields=('author', 'body'))
    """    

    results = [] # Initialize an empty list to store the extracted comments
    
    # Check if the provided fields are present in the data keys
    if set(fields).issubset(set(data.keys())):

        try:
            # Create a dictionary for each comment using the specified fields
            result = {field: data[field] for field in fields}   

            # Append the result to the results list if it is unique and its score is greater than 4
            if (result not in results) & (result['score'] > 4):
                result['link_flair_text'] = link_flair_text
                result['post_link_id'] = name
                results.append(result)

        except Exception as e:
            # Handle exceptions and print the error along with the field that caused it            
            print(f"Error occurred with field '{field}': {e}")
            print("Data:", data)
            print()

        # Extract replies to the comment if available
        replies = data.get('replies', {})

        if replies: 
            # Get the 'children' of the comment to find its replies
            children = replies.get('data', {}).get('children', [])

            for child in children:
                # Get data for each child comment
                child_data = child.get('data', {})

                # Recursively call the function to extract fields from the child comment
                child_result = extract_reddit_comments(child_data, link_flair_text, name, fields)

                # Append the result if it is unique
                if (child_result not in results):
                    results.extend(child_result)

    return results  # Return the list of extracted comments


if __name__ == "__main__":

    load_dotenv()
    # davidj_api

    CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
    SECRET_KEY = os.getenv("REDDIT_SECRET_KEY")
    USER_NAME = os.getenv("REDDIT_USER_NAME")
    PASSWORD = os.getenv("REDDIT_PASSWORD")

    client_auth = requests.auth.HTTPBasicAuth(CLIENT_ID, SECRET_KEY)
    post_data = {
        "grant_type": "password",
        "username": USER_NAME,
        "password": PASSWORD
    }
    headers = {
        "User-Agent": f"PersonalProjectAPI/0.1 by {USER_NAME}"
    }

    response = requests.post("https://www.reddit.com/api/v1/access_token", auth=client_auth, data=post_data, headers=headers)
    ACCESS_TOKEN = response.json()['access_token']
    headers['Authorization'] = f'bearer {ACCESS_TOKEN}'
    
    if response.status_code == 200:
    
        posts_response = requests.get(
        f"https://oauth.reddit.com/r/wallstreetbets/search?q=-flair%3AMeme%20-flair%3AShitpost&restrict_sr=on&include_over_18=on&sort=relevance&t=day",
        headers=headers, 
        params={'limit': '100', 'raw_json':'1'})
        
        reddit_posts = extract_reddit_posts(posts_response.json()['data']['children'])
        total_sum_reddit_posts = len(reddit_posts)
        data = []
        total_sum_comments = 0
        for reddit_post in reddit_posts:
            ID = reddit_post['id']
            comments_response = requests.get(
                f"https://oauth.reddit.com/r/wallstreetbets/comments/{ID}/?sort=confidence&t=day",
                headers=headers, 
                params={'limit': '100', 'raw_json':'1'},
            )

            for i in range(len(comments_response.json())):

                # if i = 0, it is post; if i = 1, it is comments of post            
                for detail in comments_response.json()[i]['data']['children']:
                    
                    if i == 0:
                        post_detail, post_link_flair_text, post_id = extract_reddit_commentpost(detail)
                        data.extend(post_detail)

                    else:
                        comments_data = extract_reddit_comments(detail['data'], post_link_flair_text, post_id)
                        data.extend(comments_data)
                        
                        total_sum_comments += len(comments_data)
                    
    print("total_reddit_posts:", total_sum_reddit_posts)
    print("total_reddit_comments:", total_sum_comments)


    print(pd.DataFrame.from_dict(reddit_posts))
    print(pd.DataFrame.from_dict(data))


    