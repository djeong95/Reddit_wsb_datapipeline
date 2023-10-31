import requests
import os
import json
import pytz
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta
from airflow.hooks.S3_hook import S3Hook


def convert_timestamp_to_timezone(unix_timestamp, target_timezone):
    utc_time = datetime.fromtimestamp(unix_timestamp, tz=pytz.UTC) # Convert to UTC timezone first
    target_time = utc_time.astimezone(pytz.timezone(target_timezone))
    return target_time

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
            post_dict['created_utc_formatted']= convert_timestamp_to_timezone(post['data']['created_utc'], "UTC")
            post_dict['created_pst_formatted']= convert_timestamp_to_timezone(post['data']['created_utc'], "US/Pacific")
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
        post_dict['created_utc'] = post['data']['created_utc']
        post_dict['body']= post['data']['title']
        post_dict['score']= post['data']['score']
        post_dict['link_flair_text'] = post['data']['link_flair_text']
        post_dict['post_link_id'] = post['data']['id']
        post_dict['created_utc_formatted']= convert_timestamp_to_timezone(post['data']['created_utc'], "UTC")
        post_dict['created_pst_formatted']= convert_timestamp_to_timezone(post['data']['created_utc'], "US/Pacific")

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
                result['created_utc_formatted']= convert_timestamp_to_timezone(result['created_utc'], "UTC")
                result['created_pst_formatted']= convert_timestamp_to_timezone(result['created_utc'], "US/Pacific")

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

def datetime_serializer(obj):
    """
    Serialize datetime objects to ISO format strings. 
    
    This function is typically used as a custom serializer for JSON 
    serialization functions that do not natively support datetime objects.

    Parameters:
    - obj: The object to be serialized. Expected to be a datetime object.

    Returns:
    - str: ISO formatted string representation of the datetime object.

    Example:
    >>> import json, datetime
    >>> json.dumps({'time': datetime.datetime.now()}, default=datetime_serializer)

    Notes:
    - This function only handles datetime objects. For any other object type, it raises a TypeError.

    Raises:
    - TypeError: If the input object is not of type datetime.
    """

    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("Type not serializable")

def save_data_locally(reddit_posts: json, reddit_posts_comments: json, time_var: datetime, file_type:str, post_dir_path: str, post_comm_dir_path: str):
    """
    Save Reddit-related JSON data locally.

    This function takes in data related to Reddit posts and comments, and saves them into local JSON files. 
    The file paths are constructed using the provided directory paths, file type, and current time. 
    The files are saved in separate directories based on whether they contain posts or posts with comments.

    Parameters:
    - reddit_posts (json): reddit posts file to be saved locally.
    - reddit_posts_comments (json): reddit posts/comments file to be saved locally.
    - time_var (datetime): current time (UTC timezone) that the file is being saved.
    - file_type (str): Type of file being downloaded locally (ex. raw or staged).
    - post_dir_path (str): Name of the Amazon S3 bucket where the local file should be uploaded.
    - post_comm_dir_path (str): Destination key (path) in the S3 bucket. 
    This will be the identifier for the object in the bucket.

    Returns:
    - List[Path]: A list of file paths indicating where the data has been saved locally.

    Note:
    - This function uses a helper funciton called datetime_serializer to serialize datetime objects to save
    datetime objects in JSON file locally.

    Example:
    >>> posts = {...}  # some JSON data of posts
    >>> comments = {...}  # some JSON data of posts with comments
    >>> current_time = datetime.utcnow()
    >>> saved_paths = save_data_locally(posts, comments, current_time, 'raw', 'wsb_posts', 'wsb_posts_and_comms')
    """
    print(os.getcwd())
    post_paths = []

    directories = {
        post_dir_path: reddit_posts, 
        post_comm_dir_path: reddit_posts_comments
    }

    if not os.path.exists(Path(f"{file_type}")):
        os.makedirs(file_type, exist_ok=True)

    for dir_path, data in directories.items():
    
        if not os.path.exists(Path(f"{dir_path}")):
            os.makedirs(Path(f"{file_type}/{dir_path}"), exist_ok=True)
        file_path = Path(f"{file_type}/{dir_path}/{dir_path}-{time_var.year}-{time_var.month}-{time_var.day}-{time_var.hour}.json")

        with open(file_path, 'w') as f:
            json.dump(data, f, default=datetime_serializer)
        post_paths.append(str(file_path))

    return post_paths

def _fetch_reddit_data(client_id, secret_key, user_name, password, ti):
    """
    Fetch data from Reddit API, including posts and their associated comments. 
    
    This function fetches the top 100 posts (excluding memes and shitposts) from the `r/wallstreetbets`
    subreddit and then extracts comments and their nested replies for each post.

    Parameters:
    - client_id (str): Reddit app's client ID.
    - secret_key (str): Reddit app's secret key.
    - user_name (str): Reddit username for authentication.
    - password (str): Reddit password for the above username.

    Returns:
    - list: Paths of saved files containing the extracted Reddit posts and their associated comments.

    Notes:
    - The Reddit API requires authentication via an OAuth2 process.
    - The extracted posts are filtered to avoid memes and are sorted by relevance from the last day.
    - The function leverages helper functions: `extract_reddit_posts`, `extract_reddit_commentpost`, `extract_reddit_comments`, and `save_data_locally`.

    Raises:
    - Any exception raised during the HTTP request or JSON processing.

    Example:
    >>> paths = _fetch_reddit_data('YOUR_CLIENT_ID', 'YOUR_SECRET_KEY', 'RedditUserName', 'RedditPassword')
    """
     # Get API token to qualify for API data extraction
    client_auth = requests.auth.HTTPBasicAuth(client_id, secret_key)
    post_data = {
        "grant_type": "password",
        "username": user_name,
        "password": password
    }
    headers = {
        "User-Agent": f"PersonalProjectAPI/0.1 by {user_name}"
    }

    response = requests.post("https://www.reddit.com/api/v1/access_token", auth=client_auth, data=post_data, headers=headers)
    access_token = response.json()['access_token']
    headers['Authorization'] = f'bearer {access_token}'
    
    # If Reddit API access passes, get top 100 posts minus the memes
    if response.status_code == 200:
        
        # -flair%3AMeme%20-flair%3AShitpost (No Meme posts) and restrict_sr=on (restrict search to this subreddit)
        # include_over_18=on (over_18 posts OK) and sort=relevance&t=day (sort by relevance and time less than a day)
        posts_response = requests.get(
        f"https://oauth.reddit.com/r/wallstreetbets/search?q=-flair%3AMeme%20-flair%3AShitpost&restrict_sr=on&include_over_18=on&sort=relevance&t=day",
        headers=headers, 
        params={'limit': '100', 'raw_json':'1'})
        
        # Parse through Reddit posts and return a list of dictionary of Reddit posts
        reddit_posts = extract_reddit_posts(posts_response.json()['data']['children'])
        # total_sum_reddit_posts = len(reddit_posts) # Get total post numbers

        posts_comments_data = []
        total_sum_comments = 0
        
        # Iterate through the Reddit posts and extract their comments and replies to comments
        for reddit_post in reddit_posts:
            ID = reddit_post['id']
            comments_response = requests.get(
                f"https://oauth.reddit.com/r/wallstreetbets/comments/{ID}/?sort=confidence&t=day",
                headers=headers, 
                params={'limit': '100', 'raw_json':'1'},
            )

            # i == 0 is the main post; i == 1 is the comments and replies
            for i in range(len(comments_response.json())):
           
                for detail in comments_response.json()[i]['data']['children']:
                    
                    # Get post detail, type of post, and post id
                    if i == 0:
                        post_detail, post_link_flair_text, post_id = extract_reddit_commentpost(detail)
                        # Add to the data list
                        posts_comments_data.extend(post_detail)

                    else:
                        # Get comments and replies for the type of post and post id
                        comments_data = extract_reddit_comments(detail['data'], post_link_flair_text, post_id)
                        # Add to the data list
                        posts_comments_data.extend(comments_data)
                        
                        total_sum_comments += len(comments_data) # Get total number of replies and comments in a post
        
        # Prepare inputs for save_data_locally function
        now = datetime.utcnow()        
        post_dir_path = "wsb_posts"
        post_comm_dir_path = "wsb_posts_and_comms"
        file_type = "transformed"

        # save data locally and get the saved data's paths
        post_paths = save_data_locally(reddit_posts, posts_comments_data, now, file_type, post_dir_path, post_comm_dir_path)
    
    ti.xcom_push(key = 'list_of_path_strings', value = post_paths)

def _local_file_to_s3(filepath: str, bucket_name: str, key: str, remove_local: bool, ti):
    """
    Upload a local file to an Amazon S3 bucket. 
    
    This function uses the path of the local file to upload the file to S3 in a location specified in the key.
    Based on the boolean, the local file can be removed or left alone. 

    Parameters:
    - filepath (str): Path to the local file to be uploaded to S3.
    - bucket_name (str): Name of the Amazon S3 bucket where the local file should be uploaded.
    - key (str): Destination key (path) in the S3 bucket. This will be the identifier for the object in the bucket.
    - remove_local (bool): If set to True, the local file will be deleted after the upload.

    Returns:
    None

    Example:
    >>> local_file_to_s3('/path/to/local/file.txt', 'my-s3-bucket', 'destination/folder/file.txt', True)

    Notes:
    - This function utilizes the `S3Hook` from Airflow to handle the S3 interactions.
    - Ensure that the AWS credentials are set up correctly in your environment or in the Airflow connections for the `S3Hook` to work.

    Raises:
    - OSError: If there's an error during the removal of the local file.
    """
    # xcom_pull a list of paths that are strings
    post_paths = ti.xcom_pull(key = 'list_of_path_strings', task_ids = 'fetch_reddit_data_from_api_to_json_file')
    
    for post_path in post_paths:
    
        s3_hook = S3Hook(aws_conn_id="wsb_s3_conn_id")
        s3_hook.load_file(filename=post_path, bucket_name=bucket_name, key=post_path, replace=True)
    
    if remove_local:
        if os.path.isfile(filepath):
            os.remove(filepath)