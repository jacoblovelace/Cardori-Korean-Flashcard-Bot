"""
This module defines a class `Bot` that encapsulates a `discord.ext` commands Bot along with event handlers and commands for Discord interaction.

Classes:
    Bot: Represents a discord.ext commands Bot.

Attributes:
    _instance: Class attribute representing the existence of a singleton instance.
    _bot: Class attribute representing the Bot instance.
    _guild: Class attribute representing the Discord guild.
    _table: Class attribute representing the table for storing user data.

Methods:
    __new__: Singleton pattern "constructor" to create Bot instance if none exists and return it.
    run: Runs the Bot instance using the token.

Events:
    on_ready: Called when the client is done preparing the data received from Discord.
    on_member_join: Called when a Member joins a Guild.
    on_reaction_add: Called when a Member joins a Guild.
    
Tasks:
    check_review: This task runs every 30 minutes to check if users have flashcards ready for review. It sends reminders to users via direct message for the flashcards that need review.

Commands:
    search: Command to search for Korean words in the dictionary.
    flashcards: Command to view the flashcard set of the user.
    quiz: Command to start a flashcard quiz session.
"""

import os
import logging
import discord
import asyncio
import datetime
import re
import json
from discord.ext import commands, tasks
import korean_dictionary
import class_badge
from dotenv import load_dotenv
from class_interaction_objects import FlashcardObject, FlashcardFilter

class CustomHelpCommand(commands.DefaultHelpCommand):
    """
    Override behavior of Discord.py default help command
    """
    
    async def send_bot_help(self, mapping):
        embed = self.get_bot_help_embed(mapping)
        await self.get_destination().send(embed=embed)

    def get_bot_help_embed(self, mapping):
        embed = discord.Embed(title="Help", color=0x5865f2)
        for _, commands in mapping.items():
            command_list = [f'`{command.name}` - {command.short_doc}' for command in commands]
            embed.add_field(name="Commands", value="\n".join(command_list), inline=False)
        embed.set_footer(text="Type !help command for more info on a command.")
        return embed

class Bot:
    """Encapsulates a discord.ext commands Bot."""

    _instance = None
    _bot = commands.Bot(
        command_prefix='!', 
        intents=discord.Intents(messages=True, guilds=True, members=True, message_content=True, reactions=True),
        help_command=CustomHelpCommand(show_parameter_descriptions=False)
    )
    _guild = None
    _table = None
    _help_data = None
    _badge_data = None

    def __new__(cls, table):
        """
        Singleton pattern "constructor" to create Bot instance if none exists and return it.

        :return: Bot._instance: Class attribute representing existence of singleton instance.
        """
        
        load_dotenv()
        
        if cls._instance is None:
            print('Creating a Bot instance...')
            cls._instance = super(Bot, cls).__new__(cls)
            cls._guild = None
            cls._table = table

        return cls._instance
    
    def run(cls):
        """
        Runs _bot class attribute using token.
        """
        
        print("Running the Bot instance bot...")
        cls._bot.run(os.getenv('DISCORD_TOKEN'))
    

def parse_label_input(input_string, max_num_flashcards):
    """
    Parse a string containing flashcard numbers and a label in various formats.

    Valid formats:
    - Label and single number: "label 4"
    - Label and comma-separated list: "label 4, 15, 20"
    - Label and range of numbers: "label 6-13"
    - Mix of the above: "label 4, 15, 20, 6-13"

    :param input_string: The string containing flashcard numbers and a label.
    :return: 
        - If valid: A tuple containing the label (string) and a list of integers representing the flashcard numbers.
        - else: None representing the label and an empty list representing the flashcard numbers.
    
    """
    
    match = re.match(r'^([^\d]+)(\d+(-\d+)?(,\s*\d+(-\d+)?)*?)$', input_string)
    if not match:
        return None, []

    label = match.group(1).strip()
    flashcard_numbers = []
    numbers_str = match.group(2)
    flashcard_numbers = []
    for part in numbers_str.split(','):
        if '-' in part:
            start, end = map(int, part.split('-'))
            if not (1 <= start <= max_num_flashcards and 1 <= end <= max_num_flashcards):
                return None, []
            
            flashcard_numbers.extend(range(start, end + 1))
        else:
            num = int(part)
            if not 1 <= num <= max_num_flashcards:
                return None, []
            
            flashcard_numbers.append(num)
            
    return label, flashcard_numbers

def parse_delete_input(input_string, max_num_flashcards):
    """
    Parse a string containing flashcard numbers in various formats.

    Valid formats:
    - Single number: "4"
    - Comma-separated list: "4, 15, 20"
    - Range of numbers: "6-13"
    - Mix of the above: "4, 15, 20, 6-13"

    :param input_string: The string containing flashcard numbers and a label.
    :return: 
        - If valid: A list of integers representing the flashcard numbers.
        - else: An empty list representing the flashcard numbers.
    
    """
    
    flashcard_numbers = []
    for part in input_string.split(','):
        if '-' in part:
            start, end = map(int, part.split('-'))
            if not (1 <= start <= max_num_flashcards and 1 <= end <= max_num_flashcards):
                return None, []
            
            flashcard_numbers.extend(range(start, end + 1))
        else:
            num = int(part)
            if not 1 <= num <= max_num_flashcards:
                return None, []
            
            flashcard_numbers.append(num)
            
    return flashcard_numbers


async def wait_for_cancel_reaction(ctx, label_prompt):
    return await Bot._bot.wait_for(
        'reaction_add', 
        check=lambda reaction, user: user == ctx.author and reaction.message.id == label_prompt.id and str(reaction.emoji) == '❌'
    )

async def wait_for_message(ctx, user):
    return await Bot._bot.wait_for(
        'message',
        check=lambda m: m.author == user and m.channel == ctx.channel
    )

async def wait_for_cancel_reaction_or_message(ctx, user, label_prompt):
    done, _ = await asyncio.wait(
        [asyncio.create_task(wait_for_cancel_reaction(ctx, label_prompt)), asyncio.create_task(wait_for_message(ctx, user))],
        return_when=asyncio.FIRST_COMPLETED,
        timeout=60
    )
    return done


# EVENTS

@Bot._bot.event
async def on_ready():
    """
    Called when the client is done preparing the data received from Discord.
    """
    
    Bot._guild = discord.utils.get(Bot._bot.guilds, name=os.getenv('DISCORD_GUILD'))

    print(
        f'\n{Bot._bot.user.name} is connected to the following guild:\n'
        f'{Bot._guild.name} (id: {Bot._guild.id})\n'
    )

    # get and print members in this guild
    members = '\n - '.join([member.name for member in Bot._guild.members])
    print(f'Guild Members:\n - {members}')
    
    # add any members to users table that are not already added
    for member in Bot._guild.members:
        if not member.bot:
            Bot._table.add_user(member)
            
    # start the review loop task
    check_cards_for_review.start()
    
    # load badge objects from json file
    Bot._badge_data = class_badge.load_badges_from_json("badges.json")
    

@Bot._bot.event
async def on_member_join(member):
    """
    Called when a Member joins a Guild.

    :param member: The member who joined.
    """
    # add member to users table (if already exists, nothing happens)
    if not member.bot:
        Bot._table.add_user(member)

@Bot._bot.event
async def on_reaction_add(reaction, user):
    """
    Called when a Member joins a Guild.

    :param reaction: The reaction added to the message.
    :param user: The user who reacted.
    """

    # if non-bot member reacts and message contains embeds
    if not user.bot and reaction.message.embeds:
        embed = reaction.message.embeds[0]
        
        # SEARCH RESULT EMBED
        if embed.footer and embed.footer.text.startswith('S'):
            # create a flashcard from embed data
            flashcard_obj = FlashcardObject( 
                embed.footer.text[1:],
                embed.title, 
                embed.description,
                embed.fields[0].name,
                embed.fields[0].value
            )
            # add newly created flashcard as dict to flashcard set
            if not Bot._table.add_flashcard_to_set(user, flashcard_obj.to_dict()):

                error_embed = discord.Embed(
                    embed=discord.Embed(
                        type="rich",
                        title="Error",
                        description=f"Cannot add flashcard. Maximum capacity of {Bot._table.max_capacity} reached.",
                        color=0xFF6347
                    )
                )
                await reaction.message.channel.send(embed=error_embed)

# TASKS

@tasks.loop(minutes=30)
async def check_cards_for_review():
    """
    Checks user flashcards for review at regular intervals and sends reminders to users.
    """
    
    current_time = datetime.datetime.now()

    # loop through all users in users table
    all_users = Bot._table.get_all_users()
    for user_entry in all_users:
        reminder_packet = []

        # access the flashcard set for the current user as a list
        for flashcard_dict in user_entry["flashcard_set"].values():
            
            if not flashcard_dict["spaced_repetition"]["to_review"]:
                last_reviewed_str = flashcard_dict["spaced_repetition"].get("last_reviewed")
                if last_reviewed_str is None:
                    continue
                
                last_reviewed = datetime.datetime.fromisoformat(last_reviewed_str)
                interval_minutes = int(flashcard_dict["spaced_repetition"]["interval"])  # Convert to integer

                if (current_time - last_reviewed >= datetime.timedelta(minutes=interval_minutes)):
                    flashcard_dict["spaced_repetition"]["to_review"] = True
                    flashcard_dict["spaced_repetition"]["last_reminded"] = current_time.isoformat()
                    reminder_packet.append(flashcard_dict)
            else:
                last_reminded_str = flashcard_dict["spaced_repetition"].get("last_reminded")
                if last_reminded_str is None:
                    continue
                
                last_reminded = datetime.datetime.fromisoformat(last_reminded_str)
            
                if (current_time - last_reminded >= datetime.timedelta(days=1)):
                    flashcard_dict["spaced_repetition"]["last_reminded"] = current_time.isoformat()
                    reminder_packet.append(flashcard_dict)
        
        # send packet of cards to review if not empty
        if not user_entry["preferences"]["notifications"]:
            continue
        
        if reminder_packet:
            user_id = user_entry["id"]
            user = Bot._bot.get_user(user_id)
            user_dm_channel = await user.create_dm()
            
            flashcard_list = []
            for flashcard_dict in reminder_packet:
                flashcard_list.append(f'• {flashcard_dict["front"]["word"]} / {flashcard_dict["back"]["word"]}')
    
            reminder_embed = discord.Embed.from_dict(
                {
                    "type": "rich",
                    "title": "It's time to review these flashcards!",
                    "description": '\n'.join(flashcard_list),
                    "color": 0x5865f2,
                    "footer": {
                        "text": f'{len(flashcard_list)} flashcard{"" if len(flashcard_list) == 1 else "s"}'
                    }
                }
            )
            await user_dm_channel.send(embed=reminder_embed)
            
            # update the flashcard data in the database
            for flashcard_dict in reminder_packet:
                Bot._table.update_flashcard(user, flashcard_dict)


# COMMANDS

@Bot._bot.command(aliases=['s', '검색', 'ㄱ'], category="Search")
async def search(ctx, word):
    """
    Searches for the given word in the Korean dictionary and displays the search results.
    
    Arguments:
        <word>: A Korean word in hangul

    Actions:
        Add word to flashcard set

    Example:
        !search 나무
    """
    
    search_objects = korean_dictionary.get_search_results(word)
    
    # if an error string
    if isinstance(search_objects, str):
        await ctx.send(
            embed=discord.Embed(
                type="rich",
                title="Error",
                description="Something went wrong",
                color=0xFF6347
            )
        )
        logging.error(f"Error occurred while searching for '{word}': {search_objects}")
    
    # else if non-empty list of search objects
    elif search_objects:
        embeds = []
        for search_obj in search_objects:
            response_embed = discord.Embed.from_dict(
                {
                    "type": "rich",
                    "title": f'{search_obj.korean_word}',
                    "description": f'{search_obj.korean_dfn}',
                    "color": 0x5865f2,
                    "fields": [
                        {
                        "name": f'{search_obj.trans_word}',
                        "value": f'{search_obj.trans_dfn}'
                        }
                    ],
                    "footer": {
                        "text": f'S{search_obj.id}'
                    }
                }
            )
            embeds.append(response_embed)
                  
        for embed in embeds:
            message = await ctx.send(embed=embed)
            await message.add_reaction("📝")
            
    else:
        await ctx.send(
            embed=discord.Embed(
                type="rich",
                title="Error",
                description="No search results found",
                color=0xFF6347
            )
        )
        
@Bot._bot.command(aliases=['f', '플래시카드', 'ㅍ'], category="Flashcards")
async def flashcards(ctx, *args):
    """
    Displays the flashcard set belonging to the user.
            
    Arguments (Optional):
        -r: filter for cards that need to be reviewed
        (<label>) to filter on <label>
        !(<label>) to filter on NOT <label>

    Actions:
        Label specified cards
        Delete specified cards

    Examples:
        !flashcards
        !flashcards -r
        !flashcards (animals)
    """
    
    user_flashcard_list = list(Bot._table.get_flashcard_set(ctx.author).values())
    
    # PARSE ARGUMENTS
    filters = []
    if "-r" in args:
        filters.append(FlashcardFilter(["spaced_repetition", "to_review"], True))
    
    for arg in args:
        if arg.startswith("(") and arg.endswith(")"):
            label = arg[1:-1]
            if label.startswith("!"):
                filters.append(FlashcardFilter(["label"], label[1:], operation="!="))
            else:
                filters.append(FlashcardFilter(["label"], label))
        
    # apply filters
    for filter in filters:
        user_flashcard_list = filter.apply(user_flashcard_list)
        
    if not user_flashcard_list:
        await ctx.send(
            embed=discord.Embed(
                type="rich",
                title="Error",
                description="No flashcards to display",
                color=0xFF6347
            )
        )
        return
    
    # generate list (String Builder) of flashcards
    flashcard_display_list = []
    for i, flashcard in enumerate(user_flashcard_list):
        flashcard_display_list.append(f'[{i+1}]\t{flashcard["front"]["word"]} / {flashcard["back"]["word"]}')
    
    flashcard_set_embed = discord.Embed.from_dict(
        {
            "type": "rich",
            "title": f"{ctx.author}'s Flashcard Set",
            "description": '\n'.join(flashcard_display_list),
            "color": 0x5865f2,
            "footer": {
                "text": f'{len(flashcard_display_list)} flashcard{"" if len(flashcard_display_list) == 1 else "s"}'
            }
        }
    )
    flashcard_list_message = await ctx.send(embed=flashcard_set_embed)
    
    # add reactions for labeling and deleting
    await flashcard_list_message.add_reaction('🏷️')
    await flashcard_list_message.add_reaction('🗑️')
    
    try:
        reaction, user = await Bot._bot.wait_for(
            'reaction_add', 
            timeout=60, 
            check=lambda reaction, user: user == ctx.author and reaction.message.id == flashcard_list_message.id and str(reaction.emoji) in ['🏷️', '🗑️']
        )
        
        # LABEL LOGIC
        if str(reaction.emoji) == '🏷️':
            label_prompt = await ctx.send(
                embed=discord.Embed(
                    type="rich",
                    title="Enter the label and the flashcards to label",
                    description="Example: label 2 / label 1, 3, 5 / label 4-8",
                    color=0xEED464
                )
            )
            await label_prompt.add_reaction('❌')
           
            # handle result
            result = await wait_for_cancel_reaction_or_message(ctx, user, label_prompt)
            result = result.pop().result()
            await label_prompt.delete()
            
            # cancel reaction received
            if isinstance(result, tuple):
                return
                            
            # parse label response
            label, flashcards_to_label = parse_label_input(result.content, len(user_flashcard_list))
            
            
            if label and flashcards_to_label:
                Bot._table.label_flashcards(user, label, flashcards_to_label)
                flashcards_to_label_str = ", ".join(map(str, flashcards_to_label))
                
                await ctx.send(
                    embed=discord.Embed(
                        type="rich",
                        title="Success",
                        description=f'Labeled flashcard{"" if len(flashcards_to_label) == 1 else "s"} {flashcards_to_label_str} with the label \"{label}\"',
                        color=0x5865f2
                    )
                )
            else:
                await ctx.send(
                    embed=discord.Embed(
                        type="rich",
                        title="Error",
                        description="Error labeling flashcards",
                        color=0xFF6347
                    )
                )
        
        # DELETE LOGIC
        elif str(reaction.emoji) == '🗑️':  # Delete reaction
            label_prompt = await ctx.send(
                embed=discord.Embed(
                    type="rich",
                    title="Enter the flashcards to delete",
                    description="Example: 2 / 1, 3, 5 / 4-8",
                    color=0xEED464
                )
            )
            await label_prompt.add_reaction('❌')
            
            # handle result
            result = await wait_for_cancel_reaction_or_message(ctx, user, label_prompt)
            result = result.pop().result()
            await label_prompt.delete()
            
            # cancel reaction received
            if isinstance(result, tuple):
                return
                            
            # parse label response
            flashcards_to_delete = parse_delete_input(result.content, len(user_flashcard_list))
            
            if flashcards_to_delete:
                Bot._table.delete_flashcards(user, flashcards_to_delete)
                flashcards_to_delete_str = ", ".join(map(str, flashcards_to_delete))
                
                await ctx.send(
                    embed=discord.Embed(
                        type="rich",
                        title="Success",
                        description=f'Deleted flashcard{"" if len(flashcards_to_delete) == 1 else "s"} {flashcards_to_delete_str}',
                        color=0x5865f2
                    )
                )
            else:
                await ctx.send(
                    embed=discord.Embed(
                        type="rich",
                        title="Error",
                        description="Error deleting flashcards",
                        color=0xFF6347
                    )
                )
            
    except asyncio.TimeoutError:
        return
      

@Bot._bot.command(aliases=['q', 'ㅋ', '퀴즈'], category="Quiz")
async def quiz(ctx, *args):
    """
    Start a flashcard quiz session with optional filters.

    Arguments (Optional):
        <number>: specify the number of flashcards in the quiz
        -i: invert the front and back of all flashcards
        -r: filter cards that need to be reviewed
        (<label>): filter cards with given label
        !(<label>): filter cards without given label
        
    Actions:
        Flip flashcard
        Rate card after flipping (Poor, Okay, Good)
        End quiz early
        
    Examples:
        !quiz
        !quiz 8
        !quiz -i (food)
        !quiz -r !(animals) 10
    """
    
    # PARSING ARGUMENTS
    num_cards = 10
    inverted = "-i" in args
    filters = []
  
    for arg in args:
        # number of flashcards specifier
        if arg.isdigit():
            num_cards = max(int(arg), 1)
        # filter for review option
        elif arg == "-r":
            filters.append(FlashcardFilter(["spaced_repetition", "to_review"], True))
        # filter on label option
        elif arg.startswith("(") and arg.endswith(")"):
            label = arg[2:-1] if arg.startswith("!(") else arg[1:-1]
            filters.append(FlashcardFilter(["label"], label, operation="!=" if arg.startswith("!(") else "=="))
    
    # retrieve random list of flashcards
    flashcard_list = Bot._table.get_random_flashcards(ctx.author, num_cards, filters=filters)
    
    # if no flashcards in set, send error
    if not flashcard_list:
        await ctx.send(
            embed=discord.Embed(
                type="rich",
                title="Error",
                description="No flashcards in this set",
                color=0xFF6347
            )
        )
        return
    
    # start of quiz message
    await ctx.send(
        embed=discord.Embed(
            type="rich",
            title="Flashcard Quiz",
            description=f"{len(flashcard_list)} flashcards",
            color=0x5865f2
        )
    )
    
    points_earned = 0
    index = 0
    completed = False
    
    # begin iteration through flashcard list
    while index < len(flashcard_list):
        flashcard = flashcard_list[index]
        flashcard_object = FlashcardObject.from_dict(flashcard)

        # switch front and back if inverted
        if inverted:
            flashcard_object.invert()
            flashcard = flashcard_object.to_dict()
            flashcard_object.invert()
        
        flashcard_front = discord.Embed.from_dict(
            {
                "type": "rich",
                "title": f'Flashcard - Front',
                "color": 0xcccccc,
                "fields": [
                    {
                        "name": f'{flashcard["front"]["word"]}',
                        "value": f'{flashcard["front"]["dfn"]}'
                    }
                ],
                "footer": {
                    "text": f'F{flashcard["id"]}'
                }
            }
        )
        
        # send flashcard front
        message = await ctx.send(embed=flashcard_front)
        await message.add_reaction("🔄")
        await message.add_reaction("❌")
        
        # wait for reaction
        try:
            reaction_front, _ = await Bot._bot.wait_for(
                "reaction_add",
                check=lambda r, u: not u.bot and r.message.id == message.id and str(r.emoji) in ['🔄', '❌'] and u.id == ctx.author.id,
                timeout=60
            ) 
        except asyncio.TimeoutError:
            break

        # end flashcard quiz option
        if str(reaction_front.emoji) == '❌':
            break
        
        flashcard_back = discord.Embed.from_dict(
            {
                "type": "rich",
                "title": f'Flashcard - Back',
                "color": 0xcccccc,
                "fields": [
                    {
                        "name": f'{flashcard["front"]["word"]}',
                        "value": f'{flashcard["front"]["dfn"]}'
                    },
                    {
                        "name": f'{flashcard["back"]["word"]}',
                        "value": f'{flashcard["back"]["dfn"]}'
                    }
                ],
                "footer": {
                    "text": f'B{flashcard["id"]}'
                }
            }
        )
        
        # flip the flashcard
        await message.clear_reactions()
        await asyncio.sleep(1)
        await message.edit(embed=flashcard_back)
        await message.add_reaction("🟥")  
        await message.add_reaction("🟨")  
        await message.add_reaction("🟩") 
        
        # wait for reaction
        try:
            reaction_back, _ = await Bot._bot.wait_for(
                "reaction_add",
                check=lambda r, u: not u.bot and r.message.id == message.id and str(r.emoji) in ['🟥', '🟨', '🟩'] and u.id == ctx.author.id,
                timeout=60
            )
        except asyncio.TimeoutError:
            break
        
        else:
            # based on user rating, update user points and flashcard spaced repetition data
            points_earned += flashcard_object.process_rating(reaction_back)
            Bot._table.update_flashcard(ctx.author, flashcard_object.to_dict())
            
            # increment to next flashcard in quiz
            index += 1
            
            # check for completion
            if index == len(flashcard_list):
                completed = True 
            await asyncio.sleep(1)
            
    # update user progress fields
    if completed:
        Bot._table.update_user_number_progress(ctx.author, "quizzes_completed", 1)
    Bot._table.update_user_number_progress(ctx.author, "flashcards_studied", index)
    Bot._table.update_user_number_progress(ctx.author, "study_points", points_earned)

    await ctx.send(
        embed=discord.Embed(
            type="rich",
            title='Flashcard Quiz Ended',
            description=f'{index} flashcard{"" if index == 1 else "s"} studied\n{points_earned} point{"" if points_earned == 1 else "s"} earned',
            color=0x5865f2,
        )
    )
    
    # check for appropriate badges
    user_progress = Bot._table.get_user(ctx.author)["progress"]
    
    for badge in Bot._badge_data:
        # check that badge is not already earned
        if badge.name not in [b['name'] for b in user_progress["badges"]] and badge.check_completion(user_progress):
            Bot._table.add_badge_to_badges(ctx.author, badge)
            await ctx.send(
                embed=discord.Embed(
                    type="rich",
                    title=f'{ctx.author.name} earned a new badge: {badge.name}',
                    description=f'{badge.description}',
                    color=0x29c67c,
                )
            )

@Bot._bot.command(aliases=["t", "ㅌ", "통계"])
async def stats(ctx):
    """
    View your stats and badges.

    Example:
        !stats
    """
    
    user_progress_data = Bot._table.get_user(ctx.author)["progress"]
    order = ["study_points", "flashcards_studied", "quizzes_completed", "current_streak", "longest_streak", "badges"]

    
    embed = discord.Embed(title=f"{ctx.author.name}'s Stats", color=0x5865f2)

    for key in order:
        if key == "badges":
            continue
        
        value = user_progress_data[key]
        value = str(value) if value is not None else "None"
        embed.add_field(name=key.capitalize().replace("_", " "), value=value, inline=False)
        
    badges = user_progress_data["badges"]
    if badges:
        badge_descriptions = "\n".join([f"`{badge['name']}`\n{badge['description']}\n" for badge in badges])
        embed.add_field(name="Badges", value=badge_descriptions)
    else:
        embed.add_field(name="Badges", value="No badges earned yet")
    
    await ctx.send(embed=embed)
