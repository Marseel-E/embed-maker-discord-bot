from os import environ
from traceback import print_tb

from discord import Status, Game, Intents
from discord.ext.commands import Bot
from dotenv import load_dotenv

load_dotenv('.env')

from utils import Default, log


class EmbedMaker(Bot):
	def __init__(self) -> None:
		super().__init__(
			command_prefix=".",
			case_sensitive=False,
			status=Status.online,
			intents=Intents.default(),
			activity=Game("/embed"),
			application_id=environ.get("APP_ID"),
			description="embed maker"
		)


	async def on_ready(self) -> None:
		log("status", "running")


	async def setup_hook(self) -> None:
		try:
			await self.tree.sync()
			await self.tree.sync(guild=Default.test_server)
		except Exception as e:
			log("error", "failed to sync commands")
			print_tb(e)
		else:
			log("status", "synced commands")

bot = EmbedMaker()


if __name__ == '__main__':
	bot.run(environ.get("TOKEN"))