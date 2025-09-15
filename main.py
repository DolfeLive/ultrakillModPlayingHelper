import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from gemini import get_gemini_response, KNOWLEDGE_BASE, GEMINI_API_KEY
from cooldownTracking import can_run, update_cooldown, remaining_time, USER_COOLDOWNS

# env vars
load_dotenv('env/.env')

SPECIFIC_CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
BOT_TOKEN = os.getenv('BOT_TOKEN')
GUILD_ID = os.getenv('GUILD_ID')

# make bot instance
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
guild = discord.Object(id=GUILD_ID)

async def send_chunked_response(response_text, interaction=None, message=None):
    chunk_size = 1997
    chunks = [response_text[i:i+chunk_size] for i in range(0, len(response_text), chunk_size)]
    
    prev_message = None
    for chunk in chunks:
        if interaction:
            # for slash command
            if prev_message:
                prev_message = await prev_message.followup.send(chunk)
            else:
                prev_message = await interaction.followup.send(chunk)
        elif message:
            # for regular
            if prev_message:
                prev_message = await prev_message.reply(chunk)
            else:
                prev_message = await message.reply(chunk)

@bot.tree.command(name='question', description='Ask a question', guild=guild)
async def question_command(interaction: discord.Interaction, question: str):
    if interaction.channel.id != SPECIFIC_CHANNEL_ID:
        return
    
    await interaction.response.defer(ephemeral=True)
    
    uid = interaction.user.id
    if not can_run(uid):
        await interaction.response.send_message(
            f"Wait {remaining_time(uid)}s.", ephemeral=True)
        return
    
    
    response = await get_gemini_response(
        question, 
        interaction.user.display_name, 
        "respond appropriately to this question:\n\nQUESTION"
    )
    
    await send_chunked_response(response, interaction=interaction)

@bot.tree.command(name='ask', description='Ask a question', guild=guild)
async def question_command(interaction: discord.Interaction, question: str):
    if interaction.channel.id != SPECIFIC_CHANNEL_ID:
        return
    
    await interaction.response.defer(ephemeral=True)
    
    uid = interaction.user.id
    if not can_run(uid):
        await interaction.response.send_message(
            f"Wait {remaining_time(uid)}s.", ephemeral=True)
        return
    
    response = await get_gemini_response(
        question, 
        interaction.user.display_name, 
        "respond appropriately to this question:\n\nQUESTION"
    )
    
    await send_chunked_response(response, interaction=interaction)
@bot.event
async def on_message(message):
    # ignore bots
    if message.author.bot:
        return
    # in correct channel
    if message.channel.id != SPECIFIC_CHANNEL_ID:
        return

    # check if bot mentioned OR if this is a reply to the bot
    is_mentioned = bot.user.mentioned_in(message)
    is_reply_to_bot = False
    replied_context = None

    if message.reference and message.reference.message_id:
        try:
            replied_message = await message.channel.fetch_message(message.reference.message_id)
            if replied_message.author.id == bot.user.id:
                is_reply_to_bot = True
                replied_context = f"[Previous bot message]: {replied_message.content}"
        except discord.errors.NotFound:
            pass 

    if is_mentioned or is_reply_to_bot:
        uid = message.author.id
        # check cooldown only if replying or mentioning
        if not can_run(uid):
            print(f"Saying wait {remaining_time(uid)}s to {message.author.display_name} because cooldown is {USER_COOLDOWNS[uid]}, on message: {message.content}")
            await message.channel.send(f"Wait {remaining_time(uid)}s.")
            return
        
        update_cooldown(uid)
        
        # typing indicator
        async with message.channel.typing():
            # remove the mention from the message content
            user_message = message.content
            for mention in message.mentions:
                user_message = user_message.replace(f'<@{mention.id}>', '').replace(f'<@!{mention.id}>', '')
            user_message = user_message.strip()
            
            # if message is empty after removing mentions, return
            if not user_message:
                return
            
            # get response
            response = await get_gemini_response(
                user_message, 
                message.author.display_name, 
                replied_context=replied_context
            )
            
            await send_chunked_response(response, message=message)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot ID: {bot.user.id}')
    await bot.tree.sync(guild=guild)
    if KNOWLEDGE_BASE:
        print(f"Knowledge base loaded: {len(KNOWLEDGE_BASE)} characters")
    else:
        print("No knowledge base loaded")

if __name__ == '__main__':
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN not found in .env")
        exit(1)
    if not SPECIFIC_CHANNEL_ID:
        print("Error: CHANNEL_ID not found in .env")
        exit(1)
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY not found in .env")
        exit(1)
    
    print(f"Starting bot...")
    bot.run(BOT_TOKEN)