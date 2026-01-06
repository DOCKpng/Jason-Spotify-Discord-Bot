import discord
from discord.ext import commands
import yt_dlp
from collections import deque
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="S.", intents=intents)
queue = {}

ytdlp_opts = {
    "format": "bestaudio",
    "quiet": True,
    "noplaylist": True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0"
}



ffmpeg_opts = {
    "before_options": "-nostdin -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -rw_timeout 5000000",
    "options" : "-vn"
}

@bot.event
async def  on_ready():
    print("Bot inicializado")

@bot.event
async def on_message(message: discord.Message):
    if bot.user in message.mentions:
        await message.reply("# Meus comandos:\nS.musga: para escolher uma musga.\nS.play: Escolher uma música.\nS.pause: Pausar a música.\nS.resume: Retomar a música.\nS.skip: Pular para a próxima música.")
    await bot.process_commands(message)

@bot.command()
async def musga(ctx:commands.Context):
    await ctx.reply(f"Digite S.play para escolher uma musga.")

def get_audio(query: str):
    with yt_dlp.YoutubeDL(ytdlp_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        if "entries" in info:
            info = info["entries"][0]
        audio_url = info["url"]
        title = info["title"]
        return audio_url, title

@bot.command()
async def play(ctx: commands.Context, *, link):
    if ctx.author.voice is None:
        await ctx.reply("Entre em uma call primeiro.")
        return
    vc = ctx.voice_client
    if vc is None or not vc.is_connected():
        vc = await ctx.author.voice.channel.connect()
    guild_id = ctx.guild.id
    queue.setdefault(guild_id, deque())
    audio, title = get_audio(link)
    queue[guild_id].append((audio, title))
    if vc.is_playing() or vc.is_paused():
        await ctx.reply(f"Música adicionada à fila: {title}.")
        return
    await play_next(ctx)

async def play_next(ctx: commands.Context):
    vc = ctx.voice_client
    guild_id = ctx.guild.id
    if guild_id not in queue or not queue[guild_id]:
        await ctx.send("A fila acabou.")
        return
    audio, title = queue[guild_id].popleft()
    source = discord.FFmpegPCMAudio(audio, **ffmpeg_opts)
    def after_play(error):
        if error:
            print(f"Erro no áudio: {error}")
        bot.loop.create_task(play_next(ctx))
    vc.play(source, after=after_play)
    await ctx.reply(f"Tocando agora: {title}.")

@bot.command()
async def pause(ctx: commands.Context):
    vc = ctx.voice_client
    if vc is None:
        await ctx.reply("Não estou em uma call agora.")
        return
    if not vc.is_playing():
        await ctx.reply("Nenhuma música está tocando.")
        return
    vc.pause()
    await ctx.reply("Música pausada.")

@bot.command()
async def resume(ctx: commands.Context):
    vc = ctx.voice_client
    if vc is None:
        await ctx.reply("Não estou em uma call agora.")
        return
    if not vc.is_paused():
        await ctx.reply("A música está tocando.")
        return
    vc.resume()
    await ctx.reply("Música retomada.")

@bot.command()
async def skip(ctx: commands.Context):
    vc = ctx.voice_client
    if vc is None:
        await ctx.reply("Não estou em uma call agora.")
        return
    if not vc.is_playing():
        await ctx.reply("Nenhuma música está tocando.")
        return
    vc.stop()

bot.run(TOKEN)