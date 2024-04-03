"""
Main module for running the Discord bot application.

This module initializes the necessary components such as logging, AWS resources,
and Discord bot functionality. It checks for the existence of a DynamoDB table
and creates one if it doesn't exist. Finally, it initializes and runs the Discord bot.
"""

import os
import logging
import boto3
from dotenv import load_dotenv
from class_users import Users
from class_bot import Bot


if __name__ == '__main__':
    
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    load_dotenv()
    
    # init table of users for discord bot
    users = Users(boto3.resource(
        "dynamodb", 
        region_name=os.getenv('AWS_DEFAULT_REGION'), 
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY'), 
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        ))

    # create a table if it doesn't already exist
    table_name = "discord-bot-1"
    users_exists = users.exists(table_name)
    if not users_exists:
        print(f"\nCreating table {table_name}...")
        users.create_table(table_name)
        print(f"\nCreated table {users.table.name}.")
    print(f"Now using Dynamo table: {users.table.name}")
    
    # init discord bot and run it
    bot = Bot(users)
    bot.run()   
