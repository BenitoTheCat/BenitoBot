import asyncio
import discord
from discord.ext import commands, tasks
import os
import sys
from dotenv import load_dotenv
import time

# import youtube_dl
import yt_dlp as youtube_dl

load_dotenv()
DISCORD_API = os.getenv("DISCORD_API")
DISCORD_KEY = os.getenv("DISCORD_KEY")

intens = discord.Intents().all()
client = discord.Client(intents=intens)

bot = commands.Bot(command_prefix=DISCORD_KEY, intents=intens)

youtube_dl.utils.bug_reports_message = lambda: ""

ytdl_format_options = {
    "format": "m4a/bestaudio/best",
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

queue = []


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
        video["url"] = data["webpage_url"]
        video["thumbnail"] = data["thumbnail"]

        print("url: ", video["url"])
        print("thumbnail: ", video["thumbnail"])

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
            pass

    print("ctx limpio", ctx.message.content.replace(DISCORD_KEY + "p ", ""))
    search = ctx.message.content.replace(DISCORD_KEY + "p ", "")

    await ctx.send(f"**Buscando:** {search}")
    server = ctx.message.guild
    voice_channel = server.voice_client
    # print de id of voice channel
    print(voice_channel.channel.id)
    async with ctx.typing():
        filename = await YTDLSource.from_url(search, loop=bot.loop)
        print(filename)
        if len(queue) == 0:
            print("llamo a cola")
            queue.append(filename)
            await playing(ctx)
        else:
            queue.append(filename)
            await ctx.send(f"**Ahora encole:** {filename['title']}")


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
        queue.clear()
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


# command restart that restart pm2 bot
@bot.command("restart")
async def restart(ctx):
    await ctx.send("Reiniciando bot")
    try:
        os.system("pm2 restart BenitoBot")
    except:
        await ctx.send("No se pudo reiniciar el bot")
        return


async def playing(ctx):
    print("entro a cola")
    i = 0

    filename = queue[0]
    print("trato de tocar")
    try:
        ctx.voice_client.play(
            discord.FFmpegPCMAudio(executable="ffmpeg", source=filename["filename"]),
            after=lambda x=None, check_queue=check_queue(
                ctx
            ): asyncio.run_coroutine_threadsafe(check_queue, bot.loop).result(),
        )
        embed = discord.Embed(
            title=filename["title"],
            description=filename["url"],
            color=discord.Color.pink(),
        )
        embed.set_thumbnail(url=filename["thumbnail"])
        embed.set_author(name="**Ahora tocandote 🎧:**")
        await ctx.send(embed=embed)
        # await ctx.send(f"**Ahora tocandote:** {filename['title']}")
    except:
        pass


async def check_queue(ctx):
    if len(queue) > 0:
        queue.pop(0)
        if len(queue) > 0:
            await playing(ctx)
        else:
            await ctx.send("No hay canciones pa tocar")
            time.sleep(5)
            if len(queue) == 0:
                voice_channel = ctx.message.guild.voice_client
                await voice_channel.disconnect()


@bot.command("next")
async def next(ctx):
    try:
        voice_channel = ctx.message.guild.voice_client
        voice_channel.stop()
    except:
        await ctx.send("No hay musica sonando CTM!")

    if len(queue) == 0:
        await ctx.send("No hay canciones en cola aweonao!")
        return

    if len(queue) > 0:
        await ctx.send("Cancion saltada")
        print(queue)
        await playing(ctx)


@bot.command("cola")
async def cola(ctx):
    if len(queue) == 0:
        await ctx.send("No hay canciones en cola")
    else:
        i = 0
        while i < len(queue):
            await ctx.send(f"{i+1} - {queue[i]['title']}")
            i += 1


# bot command to disconnect bot from voice channel
@bot.command("disconnect")
async def disconnect(ctx):
    try:
        voice_channel = ctx.message.guild.voice_client
        await voice_channel.disconnect()
    except:
        await ctx.send("No estoy en ningun canal de voz")
        return


# bot command to display all commands and descriptions, say that this is auto generated by AI
@bot.command("helpme")
async def helpme(ctx):
    await ctx.send(
        "```Comandos:\n"
        + "j - Unirse a un canal de voz\n"
        + "p - Reproducir una cancion\n"
        + "pause - Pausar la cancion\n"
        + "resume - Resumir la cancion\n"
        + "stop - Detener la cancion\n"
        + "leave - Salir del canal de voz\n"
        + "clear - Limpiar archivos temporales\n"
        + "next - Siguiente cancion\n"
        + "cola - Mostrar cola de canciones\n"
        + "disconnect - Desconectar al bot del canal de voz\n"
        + "```"
    )


bot.run(DISCORD_API)
