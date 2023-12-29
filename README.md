# WallStreetBets Data Pipeline for Sentimentality Analysis via NLP model

<img width="500" alt="image" src="https://github.com/djeong95/Yelp_review_datapipeline/assets/102641321/0bc4a69b-fd0e-45a2-bd5c-d5b6e9477d8e">

## Problem Statement
WallStreetBets is an online forum in Reddit where retail investors share their colorful viewpoints on everything from stocks and government bonds to global economic trends and their own gains and losses. Since it is a popular hub for these retail investors, this project aims to monitor the daily sentiment within the foum to get a sense of where these market participants might be focusing their energy every day. 

This project uses the Reddit API to tap into the "wisdom of the crowd" and find out which stocks/bonds these "diamond-handed 💎" reddit users are thinking would send them "to the moon" 🚀🌕.

## Technology Stack

- Reddit API
- Docker-compose (Run locally)
- Apache Airflow (Execute twice a day)
- AWS S3 (Simple Storage Service)
- AWS Redshift

This project is still being brainstormed. Below AWS services are still under consideration:

- AWS Lambda 
    - Hugging Face 
        - [j-hartmann/emotion-english-distilroberta-base](https://huggingface.co/j-hartmann/emotion-english-distilroberta-base) 
        - [cardiffnlp/twitter-roberta-large-2022-154m](https://huggingface.co/cardiffnlp/twitter-roberta-large-2022-154m)
- AWS QuickSight
- AWS CloudWatch
- Terraform or Cloudformation as Infrastructure-as-Code (IaC) tool to set up Cloud environment
## Data Pipeline Architecture
<img width="705" alt="image" src="https://github.com/djeong95/Reddit_wsb_datapipeline/assets/102641321/035e947e-e2b4-417b-8e3c-25624b8fce01">

## Data Structures:
Staging Table before HuggingFace:
| Column | Data Type | Context |
| --- | --- | --- |
| author | String | username of comment or post  |
| id | String | randomly generated comment_id, regardless of the username; post_id start with "t3_" |
| created_utc | int64 | Unix timestamp of comment/ post|
| body | String | body of text |
| score | int64 | upvotes |
| link_flair_text | String | type of post, like "Discussion", "News", "Gain", "DD" |
| post_link_id | String | post_id for linking comments to post |
| created_utc_formatted | timestamp | Date in UTC format |
| created_pst_formatted | timestamp | Date in PST format |
| type | String | comment or post |

User Mention Table:
| Column | Data Type | Context |
| --- | --- | --- |
| post_link_id | String | post_id |
| id | String | comment_id or post_id |
| Ticker mentioned | Array | Stock ticker/symbol |

Ticker Mentions Table (Aggregate Table from post and comment):
| Column | Data Type | Context |
| --- | --- | --- |
| Ticker | String | Stock ticker/symbol |
| Number of Mentions | int64 | Number of times ticker was mentioned |

User Sentiment Table:
| Column | Data Type | Context |
| --- | --- | --- |
| post_link_id | String | post_id |
| id | String | comment_id or post_id |
| Ticker mentioned | String | Stock ticker/symbol |
| Sentiment Score | float64 | Sentiment Score |

Sentimentality Score Table (Aggregate Table from post and comment):
| Column | Data Type | Context |
| --- | --- | --- |
| Ticker | String | Stock ticker/symbol |
| Sentiment Score | float64 | Aggregate score for sentiment |


## Data Dashboard
TBD
## Future Improvements

#### Data Ingestion (API to S3)
- Allow Airflow to use execution_date to pull data for dates not executed
    - Reddit API either allows for Past 24 hours or Past week. Data pipeline must ingest data that are delayed
- Get raw data to S3 and transform and decide to store transformed data in S3 or Redshift (AWS Lambda?)
- Move docker-compose data ingestion to an EC2 instance that triggers based on schedule so data ingestion can occur outside of localhost

#### Data Storage (S3 to Redshift)
- Redshift is a relational database management system so `body` column has to be limited with `VARCHAR(1000)`
    - Is DynamoDB a better service for this?

## Reproduce It Yourself

1. Register to use the [Reddit API](https://www.reddit.com/prefs/apps) under *create application*. You will need the application client id and secret key to access the API by clicking "are you a developer? create an app...".

https://www.youtube.com/watch?v=FdjVoOf9HN4&t=6s&ab_channel=JamesBriggs

2. Fork this repo, and clone it to your local environment.

3. To create the docker-compose.yaml file from scratch,
Download docker-compose example file
Delete everything about Celery
```bash
# Create REDDIT_WSB_DATAPIPELINE folder

# Set directory to REDDIT_WSB_DATAPIPELINE
docker-compose up -d

docker ps # See if all items were fired up correctly

# activate fernet key
# save sensitive variables in webserver
```

`AIRFLOW__CORE__FERNET_KEY: ${FERNET_KEY}`


```python
# # Use below code to generate Fernet key and save to env file
# # to be referred in docker-compose file for data encryption
from cryptography.fernet import Fernet
fernet_key= Fernet.generate_key()
print(fernet_key.decode())

# Add the resulting fernet_key into your .env file as FERNET_KEY={YOUR_FERNET_KEY_HERE}
# Add under 'environment' in docker-compose `AIRFLOW__CORE__FERNET_KEY: ${FERNET_KEY}`
# docker-compose file will read from env file in your directory when docker-compose -d is executed
```