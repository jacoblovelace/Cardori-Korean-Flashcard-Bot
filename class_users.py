# class_users.py

import logging
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class Users:
    """Encapsulates an Amazon DynamoDB table of Discord channel user data."""

    def __init__(self, dyn_resource):
        """
        :param dyn_resource: A Boto3 DynamoDB resource.
        """
        self.dyn_resource = dyn_resource
        self.table = None

    def exists(self, table_name):
        """
        Determines whether a table exists. As a side effect, stores the table in
        a member variable.

        :param table_name: The name of the table to check.
        :return: True when the table exists; otherwise, False.
        """

        try:
            table = self.dyn_resource.Table(table_name)
            table.load()
            exists = True
        except ClientError as err:
            if err.response["Error"]["Code"] == "ResourceNotFoundException":
                exists = False
            else:
                logger.error(
                    "Couldn't check for existence of %s. Here's why: %s: %s",
                    table_name,
                    err.response["Error"]["Code"],
                    err.response["Error"]["Message"],
                )
                raise
        else:
            self.table = table
        
        return exists
    
    def create_table(self, table_name):
        """
        Creates an Amazon DynamoDB table that can be used to store user data.
        The table uses the id of the user as the partition key and the
        coins as the sort key.

        :param table_name: The name of the table to create.
        :return: The newly created table.
        """
        
        try:
            self.table = self.dyn_resource.create_table(
                TableName=table_name,
                KeySchema=[
                    {"AttributeName": "id", "KeyType": "HASH"},  # Partition key
                    {"AttributeName": "name", "KeyType": "RANGE"},  # Sort key
                ],
                AttributeDefinitions=[
                    {"AttributeName": "id", "AttributeType": "N"},
                    {"AttributeName": "name", "AttributeType": "S"},
                ],
                ProvisionedThroughput={
                    "ReadCapacityUnits": 1,
                    "WriteCapacityUnits": 1,
                },
            )
            self.table.wait_until_exists()
            
        except ClientError as err:
            logger.error(
                "Couldn't create table %s. Here's why: %s: %s",
                table_name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise
        else:
            return self.table
        
    def delete_table(self):
        """
        Deletes the table.
        """
        
        try:
            print(f"deleting table {self.table.name}")
            self.table.delete()
            self.table = None
        except ClientError as err:
            logger.error(
                "Couldn't delete table. Here's why: %s: %s",
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise

    def get_user(self, user):
        """
        Gets tabular data entry for a specific user.

        :param user: The user to get.
        :return: The data about the requested user.
        """
        try:
            response = self.table.get_item(
                Key={"id": user.id, "name": user.name},
                TableName=self.table.name
            )
        except ClientError as err:
            logger.error(
                "Couldn't get user %s from table %s. Here's why: %s: %s",
                user.name,
                self.table.name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise
        else:
            item = response.get("Item")
            if item:
                return item
            else:
                print(f"No item found for user {user.id} - {user.name}")
                return None 
        
    def add_user(self, user) -> None:
        """
        Adds a user to the table if not already in table.

        :param user: Discord user object.
        """
        if not self.get_user(user):
            try:
                self.table.put_item(
                    Item={
                        "id": user.id,
                        "name": user.name,
                        "preferences": {
                            "notifications": True
                        },
                        "progress": {
                            "study_points": 0,
                            "words_studied": 0,
                            "quizzes_completed": 0,
                            "badges": []
                        },
                        "working_set": []
                    },
                    TableName=self.table.name
                )
                print(f"added user to table {self.table.name}")
            except ClientError as err:
                logger.error(
                    "Couldn't add user %s to table %s. Here's why: %s: %s",
                    user,
                    self.table.name,
                    err.response["Error"]["Code"],
                    err.response["Error"]["Message"],
                )
                raise
    
    def add_word_to_user_flashcards(self, user, word_obj):
        """
        Adds a word object to the working set for a user in the table.

        :param user: Discord user object.
        :param word_obj: The word object to append to the user's flashcard set.
        """
        
        try:
            response = self.table.update_item(
                Key={"id": user.id, "name": user.name},
                UpdateExpression="SET working_set = list_append(working_set, :val)",
                ExpressionAttributeValues={':val': [word_obj]},
                ReturnValues="UPDATED_NEW"
            )
        except ClientError as err:
            logger.error(
                "Couldn't update user %s in table %s. Here's why: %s: %s",
                user.name,
                self.table.name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise
               
    def update_user_points(self, user, value):
        """
        Given a value to be added, updates the study points field for a user in the table.

        :param user: Discord user object.
        :param amount: The value to add to the user's study points field.
        :return: The field that was updated, with its new value.
        """
        
        try:
            response = self.table.update_item(
                Key={"id": user.id, "name": user.name},
                UpdateExpression="set progress.study_points = progress.study_points + :val",
                ExpressionAttributeValues={":val": value},
                ReturnValues="UPDATED_NEW",
            )
        except ClientError as err:
            logger.error(
                "Couldn't update user %s in table %s. Here's why: %s: %s",
                user.name,
                self.table.name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise
        else:
            return response["Attributes"]


