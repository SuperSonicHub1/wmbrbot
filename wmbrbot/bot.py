"""
As always, much code is "stollen" from Stack Overflow:
- https://stackoverflow.com/questions/66115216/discord-py-play-audio-from-url
- https://stackoverflow.com/questions/71165431/how-do-i-make-a-working-slash-command-in-discord-py
- https://www.reddit.com/r/Discord_Bots/comments/g76ax6/discordpy_schedule_daily_tasks/
"""

from typing import Optional
import discord
from discord import app_commands
from discord import FFmpegPCMAudio
from discord.channel import VocalGuildChannel
from discord.ext import tasks

from . import wmbr

FFMPEG_OPTIONS = dict(
	before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
	options='-vn',
)

def get_voice_channel(member: discord.Member) -> Optional[VocalGuildChannel]:
	if member.voice and member.voice.channel:
		return member.voice.channel
	else:
		return None

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.voice_states = True

class WMBRBot(discord.Client):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	@tasks.loop(minutes=1)
	async def change_status(self):
		song, _ = await wmbr.get_current_song()
		await client.change_presence(
			activity=discord.Activity(type=discord.ActivityType.listening, name=f'{song.song!r} by {song.artist}')
		)

	async def on_ready(self):
		await tree.sync()
		# Sync with Kiera's test server
		await tree.sync(guild=discord.Object(id=1069259006285201489))
		self.change_status.start()
		print(f"{self.user} is now running!")


client = WMBRBot(intents=intents)
tree = app_commands.CommandTree(client)


@tree.command(name="play", description="Play WMBR's livestream in your voice channel.")
async def play(ctx: discord.Interaction):
	channel = get_voice_channel(ctx.user)

	if not channel:
		await ctx.response.send_message("You're currently not part of a voice channel; join one and run this slash command.", ephemeral=True)
		return
	
	voice_client = discord.utils.get(client.voice_clients, guild=ctx.guild)
	if voice_client == None:
		voice_client = await channel.connect()
	# You can also now disconnect the bot from Discord and connect it again without issue.
	# Weird edge cases are fun.
	elif not voice_client.is_connected():
		voice_client.stop()
		await voice_client.disconnect()

		voice_client = await channel.connect()
	
	if voice_client.channel != channel:
		await voice_client.move_to(channel)
		await ctx.response.send_message("Moved bot to your channel.", ephemeral=True)
		return

	source = FFmpegPCMAudio(wmbr.LIVE_STREAM, **FFMPEG_OPTIONS)

	if voice_client.is_playing():
		await ctx.response.send_message("You're listening to WMBR.", ephemeral=True)
		return

	voice_client.play(source)

	await ctx.response.send_message("You're listening to WMBR.", ephemeral=True)


@tree.command(name="stop", description="Stop playing the livestream.")
async def stop(ctx: discord.Interaction):
	voice_client = discord.utils.get(client.voice_clients, guild=ctx.guild)

	if voice_client == None:
		await ctx.response.send_message("WMBR is not playing.", ephemeral=True)
		return

	voice_client.stop()
	await voice_client.disconnect()

	await ctx.response.send_message("Stopped.", ephemeral=True)

@tree.command(name="currently-playing", description="Get information about what's playing on the radio.")
async def currently_playing(ctx: discord.Interaction):
	song, playlist = await wmbr.get_current_song()
	embed = (
		discord.Embed(title=f'{song.song!r} by {song.artist}',)
		.set_author(name=playlist.dj)
		.add_field(name="Show", value=playlist.show)
	)

	await ctx.response.send_message(embed=embed)

@tree.command(name="schedule", description="Learn about upcoming shows.")
async def schedule(ctx: discord.Interaction):
	song, playlist = await wmbr.get_current_song()
	embed = discord.Embed(title=f'Coming Up on WMBR', description=await wmbr.upcoming_shows())

	await ctx.response.send_message(embed=embed)
