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


from discord.app_commands import guilds
from discord import Interaction, User, Member, Attachment, Embed, TextStyle, SelectOption, ButtonStyle, TextChannel
from discord.ui import View, button, Button, Select, Modal, TextInput


class BaseView(View):
	def __init__(self, author: Member, base_embed: Embed, target_channel: TextChannel) -> None:
		self.author = author
		self.base_embed = base_embed
		self.target_channel = target_channel

		super().__init__(timeout=1800)

	async def interaction_check(self, inter: Interaction) -> bool:
		return inter.user.id == self.author.id

	async def on_timeout(self) -> bool:
		await self.target_channel.send(embed=self.base_embed)

		return await super().on_timeout()

	@button(label="Publish", style=ButtonStyle.red, row=1)
	async def publish_button(self, inter: Interaction, _button: Button) -> None:
		await inter.response.edit_message(view=None)
		
		await self.target_channel.send(embed=self.base_embed)

		self.stop()


class FieldModal(Modal, title="Field"):
	name = TextInput(label="Name", style=TextStyle.short, min_length=1, max_length=256)
	value = TextInput(label="Value", style=TextStyle.long, min_length=1, max_length=1024)
	inline = TextInput(label="Inline", style=TextStyle.short, min_length=4, max_length=5, default="True", placeholder="True / False")

	def __init__(self, base_embed: Embed, field_index: int, base_view: BaseView) -> None:
		self.base_embed = base_embed
		self.field_index = field_index
		self.base_view = base_view

		super().__init__()

	async def on_submit(self, inter: Interaction) -> None:
		error_message: str = ""

		field_index: int = int(self.field_index)

		name: str = self.name.value
		value: str = self.value.value
		
		if len(name) > 256:
			error_message += f"`field {field_index + 1} name` can't be longer than `256`!\n"

		if len(value) > 1024:
			error_message += f"`field {field_index + 1} value` can't be longer than `1024`!\n"

		if error_message != "":
			await inter.response.send_message(error_message, ephemeral=True)

			return

		field_data: dict = {
			"name": name,
			"value": value,
			"inline": True if self.inline.value.lower() == "true" else False
		}

		embed_data: dict = self.base_embed.to_dict()

		embed_data["fields"].insert(field_index, field_data)
		embed_data["fields"].pop(field_index + 1)

		embed = Embed.from_dict(embed_data)

		if len(embed) > 6000:
			await inter.response.send_message("Embed content length is too big! (Maximum `6000` characters).", ephemeral=True)

			return

		await inter.response.edit_message(embed=embed, view=self.base_view)



class FieldsSelect(Select):
	def __init__(self, options: list[SelectOption]) -> None:
		super().__init__(placeholder="Fields", options=options, row=0)

	async def callback(self, inter: Interaction) -> None:
		await inter.response.send_modal(FieldModal(self.view.base_embed, self.values[0], self.view))


@bot.tree.command(description="Create an embeded message")
@guilds(Default.test_server)
async def embed(inter: Interaction, channel: TextChannel, title: str = "", url: str | None = "", description: str = "", color: str | None = None, author_name: str = "", author_url: str | None = None, author_icon: User | Member | None = None, thumbnail: Attachment | None = None, image: Attachment | None = None, footer_text: str = "", footer_icon: User | Member | None = None, timestamp: bool = False, video_url: str = "", fields: int = 0) -> None:
	error_message: str = ""
	
	if (title == "") and (description == ""):
		error_message += "Either `title` or `description` must be present!\n"

	if len(title) > 256:
		error_message += "`title` can't be longer than `256` characters!\n"

	if len(description) > 4096:
		error_message += "`description` can't be longer than `4096` characters!\n"

	if len(footer_text) > 2048:
		error_message += "`footer_text` can't be longer than `2048` characters!\n"

	if len(author_name) > 256:
		error_message += "`author_name` can't be longer than `256` characters!\n"

	author_data: dict = {"name": author_name}
	if author_icon != None:
		author_data["icon_url"] = author_icon.avatar.url

	if author_url != None:
		author_data["url"] = author_url

	footer_data: dict = {"text": footer_text}
	if footer_icon != None:
		footer_data["icon_url"] = footer_icon.avatar.url

	embed_data: dict = {
		"title": title, "description": description,
		"author": author_data, "footer": footer_data,
		"timestamp": timestamp,
	}

	if url != None:
		embed_data["url"] = url

	if color != None:
		try:
			color = int(color.replace('#', ''), 16)
		except ValueError:
			error_message += "Invalid `color` value!\n"
		else:
			embed_data["color"] = color

	if thumbnail != None:
		embed_data["thumbnail"] = {"url": thumbnail.url}

	if image != None:
		embed_data["image"] = {"url": image.url}

	if video_url != None:
		embed_data["video"] = {"url": video_url}

	if error_message != "":
		await inter.response.send_message(error_message, ephemeral=True)

		return

	base_embed = Embed.from_dict(embed_data)

	base_view = BaseView(inter.user, base_embed, channel)

	if fields >= 1:
		fields_data = []
		fields_select_options = []

		for field in range(fields):
			if field > 20:
				break

			field_text: str = f"field {field + 1}"

			fields_data.append({"name": field_text, "value": field_text, "inline": True})

			fields_select_options.append(SelectOption(label=field_text.capitalize(), value=field))

		embed_data["fields"] = fields_data

		base_embed = Embed.from_dict(embed_data)
		base_view.base_embed = base_embed

		base_view.add_item(FieldsSelect(fields_select_options))

	if len(base_embed.to_dict()) > 6000:
		await inter.response.send_message("Embed content length is too big! (Maximum `6000` characters).", ephemeral=True)

		return

	await inter.response.send_message(embed=base_embed, view=base_view, ephemeral=True)

	await base_view.wait()


if __name__ == '__main__':
	bot.run(environ.get("TOKEN"))
