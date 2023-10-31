# WallStreetBets Data Pipeline for Sentimentality Analysis via NLP model

<img width="500" alt="image" src="https://github.com/djeong95/Yelp_review_datapipeline/assets/102641321/0bc4a69b-fd0e-45a2-bd5c-d5b6e9477d8e">

## Problem Statement
WallStreetBets is an online forum in Reddit where retail investors share their colorful viewpoints on everything from stocks and government bonds to global economic trends and their own gains and losses. Since it is a popular hub for these retail investors, this project aims to monitor the daily sentiment within the foum to get a sense of where these market participants might be focusing their energy every day. 

This project uses the Reddit API to tap into the "wisdom of the crowd" and find out which stocks/bonds these "diamond-handed 💎" reddit users are thinking would send them "to the moon" 🚀🌕.

## Technology Stack

- Reddit API
- Apache Airflow (execute twice a day)
- AWS S3 (Simple Storage Service)

This project is still being brainstormed. Below AWS services are still under consideration:
- AWS Glue 
- AWS Athena
- AWS Redshift
- AWS Lambda 
    - Python 
    - pandas
    - Hugging Face 
        - [j-hartmann/emotion-english-distilroberta-base](https://huggingface.co/j-hartmann/emotion-english-distilroberta-base) 
        - [cardiffnlp/twitter-roberta-large-2022-154m](https://huggingface.co/cardiffnlp/twitter-roberta-large-2022-154m)
    - Flask
- Terraform as Infrastructure-as-Code (IaC) tool to set up Cloud environment
## Data Pipeline Architecture
TBD

## Data Dashboard
TBD
## Future Improvements

#### Data Ingestion (API to S3)
- Allow Airflow to use execution_date to pull data for dates not executed
    - Reddit API either allows for Past 24 hours or Past week. Data pipeline must ingest data that are delayed
- Get raw data to S3 and transform and decide to store transformed data in S3 or Redshift (AWS Lambda?)

#### Data Storage (S3 to Redshift)


## Reproduce It Yourself

1. Register to use the [Reddit API](https://www.reddit.com/prefs/apps) under *create application*. You will need the application client id and secret key to access the API by clicking "are you a developer? create an app...".

https://www.youtube.com/watch?v=FdjVoOf9HN4&t=6s&ab_channel=JamesBriggs

2. Fork this repo, and clone it to your local environment.

```bash
# Create REDDIT_WSB_DATAPIPELINE folder

# Set directory to REDDIT_WSB_DATAPIPELINE
docker-compose up -d

docker ps # See if all items were fired up correctly

# activate fernet key
# save sensitive variables in webserver
```