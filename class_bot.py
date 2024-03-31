# class_bot.py

import os
import logging
import discord
from discord.ext import commands
import korean_dictionary
from dotenv import load_dotenv

class Bot:
    """Encapsulates a discord.ext commands Bot."""

    load_dotenv()

    # class attributes
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
        
        if cls._instance is None:
            print('Creating a Bot instance...')
            cls._instance = super(Bot, cls).__new__(cls)
            cls._guild = os.getenv('DISCORD_GUILD')
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
    
    guild = discord.utils.get(Bot._bot.guilds, name=Bot._guild)

    print(
        f'\n{Bot._bot.user.name} is connected to the following guild:\n'
        f'{guild.name} (id: {guild.id})\n'
    )

    # get and print members in this guild
    members = '\n - '.join([member.name for member in guild.members])
    print(f'Guild Members:\n - {members}')
    
    # add any members to users table that are not already added
    for member in guild.members:
        if not member.bot:
            Bot._table.add_user(member)

@Bot._bot.event
async def on_member_join(member):
    """
    Called when a Member joins a Guild.

    :param member: The member who joined.
    """
    
    # add member to users table (if already exists, nothing happens)
    if not member.bot:
        Bot._table.add_user(member)
    
    # send welcome dm to newly joined member
    await member.create_dm()
    await member.dm_channel.send(f'Howdy {member.name}, welcome to the server!')

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
        
        word_obj = {
                'korean_word': embed.title,
                'korean_dfn': embed.description,
                'trans_word': embed.fields[0].name,
                'trans_dfn': embed.fields[0].value
        }
        Bot._table.add_word_to_user_flashcards(user, word_obj)
        
        #FLASHCARD QUESTION EMBED
        
        #FLASHCARD ANSWER EMBED


# COMMANDS

@Bot._bot.command(aliases=['s', '검색', 'ㅅ'])
async def search(ctx, word): 
    words_or_error = korean_dictionary.get_word_info(word)
    
    if isinstance(words_or_error, str):
        # Log the specific error message to the console
        logging.error(f"Error occurred while searching for '{word}': {words_or_error}")
        
        # Send a generic error message to the user
        await ctx.send("Oops! Something went wrong. Please try again later.")
    
    elif words_or_error:
        embeds = []
        for word_obj in words_or_error:
            response_embed = discord.Embed.from_dict(
                {
                    "type": "rich",
                    "title": f'{word_obj["korean_word"]}',
                    "description": f'{word_obj["korean_dfn"]}',
                    "color": 0x5865f2,
                    "fields": [
                        {
                        "name": f'{word_obj["trans_word"]}',
                        "value": f'{word_obj["trans_dfn"]}'
                        }
                    ]
                }
            )
            embeds.append(response_embed)
                  
        for embed in embeds:
            message = await ctx.send(embed=embed)
            await message.add_reaction("📝")
    else:
        await ctx.send("No info found.")
