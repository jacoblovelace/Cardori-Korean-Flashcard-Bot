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

## Spaced Repetition

Cardori uses a spaced repetition algorithm to calculate intervals between reminders. Inspired by [Anki](https://apps.ankiweb.net/), flashcards can exist in one of two study phases: *Learning* and *Review*. When a card is studied, both its user rating (Poor, Okay, Good) and its study phase are used to determine the factor by which to adjust its interval time. The minimum interval between reminders is 10 minutes, and the maximum interval is 1 week. Below is a breakdown of how this factor is calculated.

#### Table of Interval Factors

|      | Learning | Review |
|------|----------|--------|
| Poor | 0.5      | 0.75   |
| Okay | 1        | 1      |
| Good | 3        | 3.5    |

#### Reminders

When a card's reminder interval has passed, it will be sent out in a reminder message to the user.
Interval reminders are checked for every 30 minutes, and all scheduled card reminders are compiled into one message.
After a reminder is sent out for a card, the next reminder will not be sent out until 1 day has passed or the card has been studied.

## User Progress

Cardori tracks user progress through various metrics:
* Study Points
* Flashcards Studied
* Quizzes Completed
* Current Streak
* Longest Streak
* Badges

#### Study Points

Study points are earned through flashcard quizzes, specifically when a user rates a flashcard. 3 study points are awarded to a "Good" answer, and 1 study point is awarded to an "Okay" answer. Study points aim to encourage users to continually practice cards until a good recall level is reached. Study points cannot be used nor can they be lost. These points are merely one way to track and motivate progress.

#### Badges

Badges are awarded to users based on meeting thresholds relating to various metrics of progress. 

* Study Points Badges
	* You've got a Point - Accumulate 10 study points
 	* Points, Please! - Accumulate 100 study points
  * Points o' Plenty - Accumulate 250 study points
  * Points with a Side of Points - Accumulate 500 study points
  * Study Point Pro - Accumulate 1,000 study points
  * *SECRET BADGE* - Accumulate 10,000 study points

* Flashcard Badges
	* First Flips - Study 10 flashcards
 	* Flip-tastic! - Study 50 flashcards
  * Fervent Flipper - Study 100 flashcards
  * Flip Fanatic - Study 250 flashcards
  * Flip Fever - Study 500 flashcards
  * *SECRET BADGE* - Study 1000 flashcards
 
* Quiz Completion Badges
	* Starter Scholar - Complete 5 quizzes
 	* Quiz Whiz - Complete 20 quizzes
  * Brainiac - Complete 50 quizzes
  * Trivia Champ - Complete 100 quizzes
  * Examiner - Complete 250 quizzes
  * Knowledge is Power - Complete 500 quizzes
  * *SECRET BADGE* - Complete 1000 quizzes

* Streak Badges
	* Streak of the Week - Reach a 7-day streak
 	* Week by Week - Reach a 14-day streak
  * Consistent - Reach a 30-day streak
  * Streak Freak - Reach a 90-day streak
  * Non-Stop Learner - Reach a 180-day streak
  * *SECRET BADGE* - Reach a 365-day streak
   
## Software and Libraries

Written in Python using the [Discord.py](https://discordpy.readthedocs.io/en/latest/index.html#) wrapper for Discord API.

Korean dictionary integration using the [Korean Basic Dictionary Open API](https://krdict.korean.go.kr/openApi/openApiInfo).

Database operations managed using [Amazon DynamoDB](https://aws.amazon.com/dynamodb/) and the AWS [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) library for Python.

