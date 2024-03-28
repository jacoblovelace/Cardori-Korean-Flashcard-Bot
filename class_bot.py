import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

class Bot:

    load_dotenv()

    _instance = None
    _bot = commands.Bot(
        command_prefix='!', 
        intents=discord.Intents(messages=True, guilds=True, members=True, message_content=True))
    _guild = os.getenv('DISCORD_GUILD')

    def __new__(cls):
        """
        Singleton pattern to create Bot instance if none exists and return it.

        Returns:
            Bot._instance: Class attribute representing existence of singleton instance.
        """
        
        if cls._instance is None:
            print('Creating a Bot instance...')
            cls._instance = super(Bot, cls).__new__(cls)

        return cls._instance
    
    def run(self):
        """
        Runs _bot class attribute using token.
        """
        
        print("Running the Bot instance bot...")
        self._bot.run(os.getenv('DISCORD_TOKEN'))


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


@Bot._bot.event
async def on_member_join(member):
    """
    Called when a Member joins a Guild.

    Args:
        member (Member): The member who joined.
    """
    
    # send welcome dm to newly joined member
    await member.create_dm()
    await member.dm_channel.send(
        f'Howdy {member.name}, welcome to the server!'
    )

@Bot._bot.command()
async def dig(ctx):
    response = f'{ctx.author} dug 1 space'
    await ctx.send(response)