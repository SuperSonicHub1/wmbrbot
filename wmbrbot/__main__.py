from dotenv import load_dotenv
load_dotenv()

from os import getenv
from .bot import client

token = getenv("DISCORD_CLIENT_TOKEN")

if not token:
	print("Set `DISCORD_CLIENT_TOKEN` as an environment var.")
	exit()

client.run(token)
