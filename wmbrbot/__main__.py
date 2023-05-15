try:
	from dotenv import load_dotenv
	load_dotenv()
except ModuleNotFoundError:
	pass

from os import getenv
from .bot import client
from .keep_alive import keep_alive

token = getenv("DISCORD_CLIENT_TOKEN")

if not token:
	print("Set `DISCORD_CLIENT_TOKEN` as an environment var.")
	exit()

keep_alive()
client.run(token)
