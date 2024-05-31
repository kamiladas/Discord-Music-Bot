import discord
from discord.ext import commands
from discord.ui import Button, View
import asyncio
import uuid
import os
import re
from pytube import YouTube
from ytmusicapi import YTMusic
import glob
SONG_URLS_FILE = "song_urls.txt" 
ytmusic = YTMusic()
pause = False
MAX_QUEUE_SIZE = 20

def is_playlist_url(url):
    return bool(re.search(r'list=([0-9A-Za-z_-]+)', url))

def remove_mp4_files():
    for file in os.listdir('.'):
        if file.endswith('.mp4'):
            os.remove(file)

intents = discord.Intents.default()
intents.typing = True
intents.presences = True
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

queue = asyncio.Queue()

class Track:
    def __init__(self, url):
        self.url = url
        self.id = uuid.uuid4()
        self.filename = None

    async def download(self):
        yt = YouTube(self.url)
        stream = yt.streams.filter(only_audio=True).first()
        self.filename = f"{self.id}.mp4"
        stream.download(filename=self.filename)

async def delete_file(filename):
    if filename and os.path.exists(filename):
        os.remove(filename)



def append_url_to_file(url):
    # Odczytaj wszystkie istniejące URL-e z pliku
    if os.path.exists(SONG_URLS_FILE):
        with open(SONG_URLS_FILE, 'r') as f:
            urls = f.readlines()
    else:
        urls = []

    # Dodaj nowy URL na końcu listy, z dodanym znakiem nowej linii
    urls.append(f"{url}\n")

    # Jeśli liczba URL-i przekracza 20, usuń najstarszy (pierwszy na liście)
    if len(urls) > 20:
        urls.pop(0)

    # Zapisz zaktualizowaną listę URL-i z powrotem do pliku
    with open(SONG_URLS_FILE, 'w') as f:
        f.writelines(urls)


async def play_track(ctx, track):
    if not track.filename:
        await ctx.send("Błąd: Brak pliku do odtworzenia.")
        return

    await ctx.send(f'Odtwarzanie: "{YouTube(track.url).title}"')
    view = ControlButtons(ctx, bot)
    await ctx.send("Kontrolki odtwarzania:", view=view)

    source = discord.FFmpegOpusAudio(track.filename)
    ctx.voice_client.play(source)

    while ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
        await asyncio.sleep(1)
    
    await delete_file(track.filename)
    await play_next(ctx)

async def add_to_queue(ctx, url, prev):
    if queue.qsize() >= MAX_QUEUE_SIZE:
        await ctx.send("Kolejka jest pełna. Spróbuj ponownie później.")
        return False

    if ctx.voice_client is None and ctx.author.voice:
        await ctx.author.voice.channel.connect()
    elif ctx.voice_client is None:
        await ctx.send("Nie jesteś na kanale głosowym!")
        return False

    track = Track(url)
    try:
        await track.download()
    except Exception as e:
        await ctx.send(f"Błąd podczas pobierania: {e}")
        return False

    await queue.put(track)

    # Announce the currently playing track's title if prev is True
    if prev:
        if ctx.voice_client.is_playing():
            current_track = YouTube(ctx.voice_client.source.title)
            await ctx.send(f'Obecnie odtwarzany utwór: "{current_track.title}"')
    else:
        append_url_to_file(url)

    return True


async def play_next(ctx):
    if not queue.empty():
        next_track = await queue.get()
        if not ctx.voice_client.is_playing():
            await play_track(ctx, next_track)
        queue.task_done()

async def process_playback(ctx, url):
    if is_playlist_url(url):
        playlist_id_match = re.search(r'list=([0-9A-Za-z_-]+)', url)
        if not playlist_id_match:
            await ctx.send("Nie udało się odczytać identyfikatora playlisty z URL.")
            return

        playlist_id = playlist_id_match.group(1)
        playlist_info = ytmusic.get_playlist(playlist_id)
        tracks = playlist_info['tracks']
        for track in tracks:
            video_url = f"https://www.youtube.com/watch?v={track['videoId']}"
            success = await add_to_queue(ctx, video_url,False)
            if not success:
                await ctx.send("Kolejka jest pełna. Przerywam dodawanie utworów.")
                break
    else:
        video_id_match = re.search(r'(?:v=|/)([0-9A-Za-z_-]{11}).*', url)
        if video_id_match:
            video_id = video_id_match.group(1)
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            await add_to_queue(ctx, video_url,False)
        else:
            search_results = ytmusic.search(url, filter='songs')
            if search_results:
                first_result = search_results[0]
                video_url = f"https://www.youtube.com/watch?v={first_result['videoId']}"
                await add_to_queue(ctx, video_url ,False)
            else:
                await ctx.send("Nie znaleziono utworu.")

    if not ctx.voice_client.is_playing():        
        await play_next(ctx)

class ControlButtons(View):
    def __init__(self, ctx, bot):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.bot = bot

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        ctx = await self.bot.get_context(interaction.message)
        await interaction.response.defer()
        return True

    @discord.ui.button(label="Odtwórz listę", style=discord.ButtonStyle.success, emoji="▶️", custom_id="play_list")
    async def play_list_button(self, interaction: discord.Interaction, button: Button):
        if interaction.guild.voice_client is None:
            if interaction.user.voice:
                await interaction.user.voice.channel.connect()
            else:
                await interaction.response.send_message("Musisz być na kanale głosowym, aby użyć tej komendy.", ephemeral=True)
                return
        await play_song_file(interaction)
        await interaction.followup.send("Odtwarzanie utworów z pliku.", ephemeral=True)

    @discord.ui.button(label="Pomiń", style=discord.ButtonStyle.primary, emoji="⏭️", custom_id="skip_button")
    async def skip_button(self, interaction: discord.Interaction, button: Button):
        await interaction.followup.send("Pomijanie obecnego utworu.", ephemeral=True)
        ctx = await self.bot.get_context(interaction.message)
        await ctx.invoke(self.bot.get_command("skip"))

    @discord.ui.button(label="Zatrzymaj", style=discord.ButtonStyle.danger, emoji="⏹️", custom_id="stop_button")
    async def stop_button(self, interaction: discord.Interaction, button: Button):
        await interaction.followup.send("Odtwarzacz zatrzymany.", ephemeral=True)
        ctx = await self.bot.get_context(interaction.message)
        await ctx.invoke(self.bot.get_command("stop"))

    @discord.ui.button(label="Kolejka", style=discord.ButtonStyle.secondary, emoji="📋", custom_id="queue_button")
    async def queue_button(self, interaction: discord.Interaction, button: Button):
        await interaction.followup.send("Lista kolejki.", ephemeral=True)
        ctx = await self.bot.get_context(interaction.message)
        await ctx.invoke(self.bot.get_command("queue"))

    @discord.ui.button(label="Lista z pliku", style=discord.ButtonStyle.secondary, emoji="🗒️", custom_id="playlist_queue_button")
    async def playlist_queue_list_button(self, interaction: discord.Interaction, button: Button):
        await interaction.followup.send("Lista kolejki z pliku playlisty.", ephemeral=True)
        ctx = await self.bot.get_context(interaction.message)
        await ctx.invoke(self.bot.get_command("playlist_queue"))

    @discord.ui.button(label="Usuń listę", style=discord.ButtonStyle.danger, emoji="🗑️", custom_id="del_playlist")
    async def del_playlist_button(self, interaction: discord.Interaction, button: Button):
        await interaction.followup.send("Plik playlisty usunięty.", ephemeral=True)
        ctx = await self.bot.get_context(interaction.message)
        await ctx.invoke(self.bot.get_command("del_playlist"))
        
@bot.command(name='p', help='Odtwarza utwór lub playlistę z YouTube')
async def play(ctx, *, url=""):
    if url:
        await process_playback(ctx, url)

@bot.command(name='queue', help='Wyświetla kolejne utwory w kolejce')
async def show_queue(ctx):
    if queue.empty():
        await ctx.send("Kolejka jest pusta.")
    else:
        response = [f"{i+1}. {YouTube(track.url).title}" for i, track in enumerate(queue._queue)]
        await ctx.send("\n".join(response))

@bot.command(name='skip', help='Pomija obecny utwór')
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await asyncio.sleep(1)        
        await play_next(ctx)
   
@bot.command(name='stop', help='Zatrzymuje odtwarzanie i czyści kolejkę')
async def stop(ctx):
    
    global should_continue_adding,pause
    pause=True
    should_continue_adding = False
    if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
        ctx.voice_client.stop()
        await asyncio.sleep(1)
        for mp4_file in glob.glob('*.mp4'):
            os.remove(mp4_file)
    while not queue.empty():
        queue.get_nowait()
    await skip(ctx)
 

@bot.event
async def on_ready():
    print(f'Zalogowano jako {bot.user.name}')

@bot.event
async def on_message(message):
    if message.author == bot.user or not message.content:
        return

    if message.channel.name == "botyjebane":
        ctx = await bot.get_context(message)
        content = message.content.lower()
        if content.startswith("/"):
            command = content[1:]
            if command in ["p", "stop", "skip", "queue", "menu"]:
                await process_command(ctx, command)
                return
        else:
            if message.content in ["p", "stop", "skip", "queue","menu"]:
                command = message.content
                await process_command(ctx, command)
                return
        await process_playback(ctx, message.content)

    await bot.process_commands(message)

async def process_command(ctx, command):
    if command == "p":
        await play(ctx)
    elif command == "stop":
        await stop(ctx)
    elif command == "skip":
        await skip(ctx)
    elif command == "queue":
        await show_queue(ctx)
    elif command == "menu": 
        await menu(ctx)


def read_urls_from_file():
    if not os.path.exists(SONG_URLS_FILE):
        return []
    with open(SONG_URLS_FILE, 'r') as f:
        urls = f.readlines()
    return [url.strip() for url in urls]



@bot.command(name='play_song_file', help='Dodaje utwory z pliku do kolejki i odtwarza od najnowszego')
async def play_song_file_command(ctx):
       await play_song_file(ctx)



async def play_song_file(ctx_or_interaction):
    global pause
    if isinstance(ctx_or_interaction, discord.Interaction):
        ctx = await bot.get_context(ctx_or_interaction.message)
    else:
        ctx = ctx_or_interaction

    if ctx.voice_client is None:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("Musisz być na kanale głosowym, aby użyć tej komendy.")
            return

    urls = read_urls_from_file()

    for url in reversed(urls):  # Start with the newest entries
        if queue.qsize() >= MAX_QUEUE_SIZE:
            await ctx.send("Kolejka osiągnęła maksymalny rozmiar. Przerywam dodawanie utworów.")
            break

        success = await add_to_queue(ctx, url, True)
        if not success:
            break
        if not ctx.voice_client.is_playing() and not queue.empty():
            await play_next(ctx)
        await asyncio.sleep(1)  # Short sleep to allow other tasks to run

        # Check if the playback should continue
        if  pause:
            
            pause = False 
            break


       
@bot.command(name='del_playlist', help='Usuwa plik playlisty')
async def del_playlist(ctx):
    if os.path.exists(SONG_URLS_FILE):
        os.remove(SONG_URLS_FILE)
        await ctx.send("Plik playlisty został usunięty.")
    else:
        await ctx.send("Plik playlisty nie istnieje.")       
    
       
@bot.command(name='playlist_queue', help='Wyświetla listę utworów w pliku playlisty')
async def playlist_queue(ctx):
    
    if not os.path.exists(SONG_URLS_FILE):
        await ctx.send("Plik playlisty nie istnieje.")
        return

    urls = read_urls_from_file()
    if not urls:
        await ctx.send("Plik playlisty jest pusty.")
        return

    titles = []
    for url in urls:
        yt = YouTube(url)
        titles.append(yt.title)

    response = "\n".join(titles)
    await ctx.send(f"Lista utworów w pliku playlisty:\n{response}")
    
@bot.command(name='menu', help='Wyświetla menu z przyciskami sterowania')
async def menu(ctx):
    view = ControlButtons(ctx, bot)
    await ctx.send("Kontrolki odtwarzania:", view=view)

bot.run('YOURTOKEN')
