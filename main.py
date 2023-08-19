import asyncio
import discord
from discord.ext import commands, tasks
import os
import sys
from dotenv import load_dotenv

load_dotenv()
DISCORD_KEY = os.getenv("DISCORD_KEY")


# import youtube_dl
import yt_dlp as youtube_dl

intens = discord.Intents().all()
client = discord.Client(intents=intens)

bot = commands.Bot(command_prefix="!", intents=intens)

youtube_dl.utils.bug_reports_message = lambda: ""

ytdl_format_options = {
    "format": "bestaudio/best",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",
    "outtmpl": "tmp/%(title)s-%(id)s.%(ext)s",
}

ffmpeg_options = {"options": "-vn"}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get("title")
        self.url = ""

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        print(url)
        loop = loop or asyncio.get_event_loop()
        print("paso 2")
        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=not stream)
        )
        if "entries" in data:
            data = data["entries"][0]
        filename = data["title"] if stream else ytdl.prepare_filename(data)
        print(f"titulo: {data['title']}")
        video = {}
        video["title"] = data["title"]
        video["filename"] = filename

        return video


@bot.command(name="j")
async def j(ctx):
    if not ctx.message.author.voice:
        await ctx.send(
            f"{ctx.message.author.name} No estas en un canal de voz, no puedo unirme"
        )
        return
    else:
        channel = ctx.message.author.voice.channel
        await channel.connect()


@bot.command(name="p")
async def p(ctx):
    # esperar a conectar
    if not ctx.message.author.voice:
        await ctx.send(
            f"{ctx.message.author.name} No estas en un canal de voz, no puedo unirme"
        )
        return
    else:
        try:
            channel = ctx.message.author.voice.channel
            await channel.connect()
        except:
            await ctx.send("Ya estoy en un canal de voz")
            return

    print("ctx", ctx.message.content)
    print("ctx limpio", ctx.message.content.replace("!p ", ""))
    search = ctx.message.content.replace("!p ", "")
    server = ctx.message.guild
    voice_channel = server.voice_client
    async with ctx.typing():
        filename = await YTDLSource.from_url(search, loop=bot.loop)
        print(filename)
        # voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg", source=filename))
        ctx.voice_client.play(
            discord.FFmpegPCMAudio(executable="ffmpeg", source=filename["filename"])
        )
        await ctx.send(f"**Ahora tocandote:** {filename['title']}")


@bot.command("pause")
async def pause(ctx):
    voice_channel = ctx.message.guild.voice_client
    if voice_channel.is_playing():
        await ctx.send("Musica pausada my looord")
        voice_channel.pause()
    else:
        await ctx.send("No hay musica sonando CTM!")


@bot.command("resume")
async def resume(ctx):
    voice_channel = ctx.message.guild.voice_client
    if voice_channel.is_paused():
        await ctx.send("Musica resumida my looord")
        voice_channel.resume()
    else:
        await ctx.send("No hay musica pausada CTM!")


@bot.command("stop")
async def stop(ctx):
    voice_channel = ctx.message.guild.voice_client
    if voice_channel.is_playing():
        await ctx.send("Musica detenida my looord")
        voice_channel.stop()
    else:
        await ctx.send("No hay musica sonando CTM!")
    await voice_channel.disconnect()


@bot.command("leave")
async def leave(ctx):
    try:
        voice_channel = ctx.message.guild.voice_client
        await voice_channel.disconnect()
    except:
        await ctx.send("No estoy en ningun canal de voz")
        return


@bot.command("clear")
async def clear(ctx):
    try:
        os.system("rm -rf tmp/*")
        await ctx.send("Archivos temporales eliminados")
    except:
        await ctx.send("No se pudo eliminar los archivos temporales")
        return


@bot.command("helpme")
async def helpme(ctx):
    await ctx.send(
        "Comandos disponibles: \n !j - Unirse a un canal de voz \n !p - Reproducir una cancion \n !pause - Pausar la cancion \n !resume - Resumir la cancion \n !stop - Detener la cancion \n !leave - Salir del canal de voz \n !clear - Limpiar archivos temporales"
    )


bot.run(DISCORD_KEY)
