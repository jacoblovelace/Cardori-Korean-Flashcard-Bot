# class_bot.py

import os
import logging
import discord
import asyncio
from discord.ext import commands
import korean_dictionary
from dotenv import load_dotenv
from class_interaction_objects import FlashcardObject

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
                await reaction.message.channel.send(f"Cannot add flashcard. Maximum capacity of {Bot._table.max_capacity} reached.")

# COMMANDS

@Bot._bot.command(aliases=['s', '검색', 'ㄱ'])
async def search(ctx, word): 
    search_objects = korean_dictionary.get_search_results(word)
    
    # if an error string
    if isinstance(search_objects, str):
        logging.error(f"Error occurred while searching for '{word}': {search_objects}")
        await ctx.send("Oops! Something went wrong. Please try again later.")
    
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
        await ctx.send("No dictionary information found.")

@Bot._bot.command(aliases=['q', 'ㅋ', '퀴즈'])
async def quiz(ctx, num_cards=10):
    
    # prevent negative numbers
    num_cards = max(num_cards, 1)
    
    flashcard_list = Bot._table.get_random_flashcards(ctx.author, num_cards)
    
    # start of quiz message
    quiz_start = discord.Embed.from_dict(
        {
            "type": "rich",
            "title": 'Flashcard Quiz',
            "description": f'{len(flashcard_list)} flashcards',
            "color": 0x5865f2,
        }
    )
    await ctx.send(embed=quiz_start)
    
    points_earned = 0
    index = 0
    while index < len(flashcard_list):
        flashcard = flashcard_list[index]
        
        flashcard_front = discord.Embed.from_dict(
            {
                "type": "rich",
                "title": f'Flashcard - Front',
                "color": 0x5865f2,
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
                "color": 0x5865f2,
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
            if reaction_back.emoji == '🟥':
                Bot._table.update_user_points(ctx.author, 1)
                points_earned += 1
            elif reaction_back.emoji == '🟨':
                Bot._table.update_user_points(ctx.author, 2)
                points_earned += 2
            else:
                Bot._table.update_user_points(ctx.author, 3)
                points_earned += 3
                            
            index += 1
            await asyncio.sleep(1)
            
    # end of quiz message
    quiz_end = discord.Embed.from_dict(
        {
            "type": "rich",
            "title": 'Flashcard Quiz Ended',
            "description": f'{index} flashcards studied\n{points_earned} points earned',
            "color": 0x5865f2,
        }
    )
    await ctx.send(embed=quiz_end)
