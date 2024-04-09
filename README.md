# Cardori
**The Discord Bot who helps you study Korean**

## Overview
Meet *Cardori* (카돌이), a combination of "card" (카드) and "dori" (돌이), roughly translating to "Flashcard Buddy".

Cardori gives you access to the full Korean dictionary, allowing you search for any Korean word within Discord. 
In the click of a button, you can add a word along with its English translation to your flashcard set. 

To study your flashcards, just start a quiz session with Cardori. 
After every flashcard, simply provide a rating based on your recall ability.
Cardori uses these ratings and spaced-repetition technology to intelligently schedule reminders so you can stay on top of your studying.
This personalized approach ensures efficient learning and retention of Korean vocabulary over time.

## Commands

`!help` - Displays an overview of Cardori's commands

`!help <command>` - Provides a detailed description of a specified command

`!search <Korean word>` - Searches the Korean dictionary for a specified word and displays the results
* 📝 Add Reaction - Saves the search result information as a flashcard to the user's flashcard set

`!flashcards` - Displays a user's flashcard set
* 🏷️ Label Reaction - Assign a label to specified cards
* 🗑️ Delete Reaction - Remove specified cards from the user's flashcard set
* ❌ Cancel Reaction -  Cancels a labelling or delete action

`!quiz` - Starts a flashcard quiz session
* 🔄 Flip Reaction - "Flips" a flashcard over to reveal full information
* ❌ Cancel Reaction -  Ends the flashcard quiz early
* Flashcard Rating Reactions:
  * 🟥 Poor/No Recall
  * 🟨 Okay Recall
  * 🟩 Good/Perfect Recall

`!stats` - Displays a user's stats, study points, and badges

## Software and Libraries

Written in Python using the [Discord.py](https://discordpy.readthedocs.io/en/latest/index.html#) wrapper for Discord API.

Korean dictionary integration using the [Korean Basic Dictionary Open API](https://krdict.korean.go.kr/openApi/openApiInfo).

Database operations managed using [Amazon DynamoDB](https://aws.amazon.com/dynamodb/) and the AWS [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) library for Python.

