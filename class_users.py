"""
This module defines a class `Users` that encapsulates an Amazon DynamoDB table of Discord channel user data.

Classes:
    Users: Represents a DynamoDB table of Discord channel user data.

Methods:
    __init__: Initializes the Users instance with a Boto3 DynamoDB resource.
    exists: Determines whether a table exists.
    create_table: Creates a new DynamoDB table for storing user data.
    delete_table: Deletes the DynamoDB table.
    get_all_users: Fetchesall user entries from the DynamoDB table.
    get_user: Retrieves data entry for a specific user from the DynamoDB table.
    add_user: Adds a user to the DynamoDB table if not already in table.
    get_flashcard_by_id: Retrieves a flashcard by its ID for a specific user.
    get_flashcard_set: Retrieves the flashcard set for a specific user.
    get_random_flashcards: Retrieves a specified number of random flashcards for a user.
    add_flashcard_to_set: Adds a word object to the flashcard set for a user in the table.
    update_flashcard: Updates a flashcard in the user's flashcard set.
    update_user_points: Updates the study points for a specific user.
"""

import logging
import random
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
        self.max_capacity = 100

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
            self.table.delete()
            self.table = None
        except ClientError as err:
            logger.error(
                "Couldn't delete table. Here's why: %s: %s",
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise
        
    def get_all_users(self):
        """
        Fetch all user entries from the DynamoDB table.
        """
        response = self.table.scan()
        return response.get('Items', [])

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
                return None 
        
    def add_user(self, user):
        """
        Adds a user to the table if not already in table.

        :param user: Discord user object.
        """
        if not self.get_user(user):
            try:
                # user schema
                self.table.put_item(
                    Item={
                        "id": user.id,
                        "name": user.name,
                        "preferences": {
                            "notifications": True
                        },
                        "progress": {
                            "study_points": 0,
                            "flashcards_studied": 0,
                            "quizzes_completed": 0,
                            "last_quiz_completion": None,
                            "current_streak": 0,
                            "longest_streak": 0,
                            "badges": []
                        },
                        "flashcard_set": {}
                    },
                    TableName=self.table.name
                )
            
            except ClientError as err:
                logger.error(
                    "Couldn't add user %s to table %s. Here's why: %s: %s",
                    user,
                    self.table.name,
                    err.response["Error"]["Code"],
                    err.response["Error"]["Message"],
                )
                raise
            
    def get_flashcard_by_id(self, user, id):
        """
        Retrieves a flashcard from the user's flashcard set by its ID.

        :param user: The user whose flashcard set is being accessed.
        :param id: The ID of the flashcard to retrieve.
        :return: The flashcard with the provided ID, or None if not found.
        """
        
        # get the user's flashcard set
        user_flashcard_set = self.get_flashcard_set(user)
        
        # return the flashcard with the provided id
        return user_flashcard_set.get(id)
    
    def get_flashcard_set(self, user):
        """
        Retrieves the flashcard set belonging to the specified user.

        :param user: The user whose flashcard set is being retrieved.
        :return: The flashcard set of the user.
        """
        
        return self.table.get_item(
            Key={"id": user.id, "name": user.name}
        )["Item"]["flashcard_set"]
    
    def get_random_flashcards(self, user, num_flashcards, filters=[]):
        """
        Retrieves a specified number of random flashcards from the user's flashcard set.

        :param user: The user whose flashcard set is being accessed.
        :param num_flashcards: The number of random flashcards to retrieve.
        :param filters: Optional. A list of filter objects to apply to the flashcards.
        :return: A list of randomly selected flashcards.
        """
        
        # get the user's flashcard set and convert to a list
        user_flashcard_list = list(self.get_flashcard_set(user).values())
        
        # apply filters if any
        for filter_obj in filters:
            user_flashcard_list = filter_obj.apply(user_flashcard_list)
            
        # ensure that you cannot request more flashcards than available
        num_flashcards = min(num_flashcards, len(user_flashcard_list))
        
        # select num_flashcards unique items at random
        random_flashcards = random.sample(user_flashcard_list, num_flashcards)
        
        return random_flashcards

    def add_flashcard_to_set(self, user, flashcard_dict):
        """
        Adds a word object to the flashcard set for a user in the table.

        :param user: Discord user object.
        :param search_obj: The search object to add to the user's flashcard set dictionary.
        """
        
        try:
            # retrieve the user's flashcard_set
            user_flashcard_set = self.get_flashcard_set(user)
            
            if len(user_flashcard_set) >= self.max_capacity:
                return False

            # update the flashcard_set dictionary with the new key-value pair
            user_flashcard_set[flashcard_dict["id"]] = flashcard_dict

            # update the item with the modified flashcard_set
            self.table.update_item(
                Key={"id": user.id, "name": user.name},
                UpdateExpression="SET flashcard_set = :val",
                ExpressionAttributeValues={':val': user_flashcard_set},
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
        else:
            return True
        
    def update_flashcard(self, user, flashcard_dict):
        """
        Updates a flashcard in the user's flashcard set.
        
        :param user: Discord user object.
        :param flashcard_dict (dict): A dictionary representing the flashcard to be updated.
        """
        
        # retrieve the user's flashcard_set
        user_flashcard_set = self.get_flashcard_set(user)
                
        # update the flashcard_set dictionary with the new key-value pair
        user_flashcard_set[flashcard_dict["id"]] = flashcard_dict

        # update the item with the modified flashcard_set
        self.table.update_item(
            Key={"id": user.id, "name": user.name},
            UpdateExpression="SET flashcard_set = :val",
            ExpressionAttributeValues={':val': user_flashcard_set},
            ReturnValues="UPDATED_NEW"
        )
               
    def update_user_number_progress(self, user, field, value):
        """
        Updates a specified Number field of a user's progress data with a specified value.
        """
        try:
            self.table.update_item(
                Key={"id": user.id, "name": user.name},
                UpdateExpression=f"set progress.{field} = progress.{field} + :val",
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

    def label_flashcards(self, user, label, flashcards_to_label):
        user_flashcard_set = self.get_flashcard_set(user)
    
        for i in flashcards_to_label:
            # get the flashcard ID using index, then update its label
            flashcard_id = list(user_flashcard_set.keys())[i] 
            user_flashcard_set[flashcard_id]["label"] = label
        
        # update the user's flashcard list
        self.table.update_item(
            Key={"id": user.id, "name": user.name},
            UpdateExpression="SET flashcard_set = :val",
            ExpressionAttributeValues={':val': user_flashcard_set},
            ReturnValues="UPDATED_NEW"
        )
        