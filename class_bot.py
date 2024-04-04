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
from discord.ext import commands, tasks
import korean_dictionary
from dotenv import load_dotenv
from class_interaction_objects import FlashcardObject

class Bot:
    """Encapsulates a discord.ext commands Bot."""

    _instance = None
    _bot = commands.Bot(
        command_prefix='!', 
        intents=discord.Intents(messages=True, guilds=True, members=True, message_content=True, reactions=True)
        )
    _guild = None
    _table = None

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
        if embed.footer.text.startswith('S'):
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
                error_embed = discord.Embed.from_dict(
                    {
                        "type": "rich",
                        "title": "Error",
                        "description": f"Cannot add flashcard. Maximum capacity of {Bot._table.max_capacity} reached.",
                        "color": 0xFF6347,
                    }
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
        if reminder_packet:
            user_id = user_entry['id']
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

@Bot._bot.command(aliases=['s', '검색', 'ㄱ'])
async def search(ctx, word):
    """
    Searches for the given word in the Korean dictionary and displays the search results.

    :param ctx (discord.ext.commands.Context): The context of the command.
    :param word (str): The word to search for in the Korean dictionary.
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
        
@Bot._bot.command(aliases=['f', '플래시카드', 'ㅍ'])
async def flashcards(ctx):
    """
    Displays the flashcard set belonging to the user.

    :param ctx (discord.ext.commands.Context): The context of the command.
    """
    user_flashcard_set = Bot._table.get_flashcard_set(ctx.author)
    
    flashcard_list = []
    for i, flashcard in enumerate(user_flashcard_set.values()):
        flashcard_list.append(f'[{i}]\t{flashcard["front"]["word"]} / {flashcard["back"]["word"]}')
    
    flashcard_set_embed = discord.Embed.from_dict(
        {
            "type": "rich",
            "title": f"{ctx.author}'s Flashcard Set",
            "description": '\n'.join(flashcard_list),
            "color": 0x5865f2,
            "footer": {
                "text": f'{len(flashcard_list)} flashcard{"" if len(flashcard_list) == 1 else "s"}'
            }
        }
    )
    await ctx.send(embed=flashcard_set_embed)

@Bot._bot.command(aliases=['q', 'ㅋ', '퀴즈'])
async def quiz(ctx, *args):
    """
    Initiates a flashcard quiz session for the user.

    :param ctx (discord.ext.commands.Context): The context of the command.
    :param *args (str): Variable arguments:
        - "-i" to invert flashcards.
        - An integer to specify the number of flashcards for the quiz.
    """
    
    # parse variable arguments
    inverted = "-i" in args
    num_cards = 10 
    for arg in args:
        if arg.isdigit():
            num_cards = max(int(arg), 1)
    
    # retrieve random list of flashcards
    flashcard_list = Bot._table.get_random_flashcards(ctx.author, num_cards)
    
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
            # update spaced repetition data for flashcard based on user rating
            flashcard_object.process_rating(reaction_back)
            Bot._table.update_flashcard(ctx.author, flashcard_object.to_dict())
            
            # increment to next flashcard in quiz
            index += 1
            await asyncio.sleep(1)
            
    # end of quiz message
    await ctx.send(
        embed=discord.Embed(
            type="rich",
            title='Flashcard Quiz Ended',
            description=f'{index} flashcard{"" if index == 1 else "s"} studied\n{points_earned} point{"" if points_earned == 1 else "s"} earned',
            color=0x5865f2,
        )
    )
