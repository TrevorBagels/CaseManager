from collections import UserDict
import os, time, random, sys, discord, JSON4JSON, traceback, json, importlib
from discord.ext import commands
from discord.ext.commands.core import command
from discord.utils import get
from ..Core import data as d
from bson import json_util
from ..GoogleDrive import googledrive

class CaseBotSpine(commands.Bot):
	data:			d.SaveData
	first_time:		bool
	config:			d.Config
	guild:			discord.Guild
	everyone:		discord.Role
	drive:			googledrive.GDrive
	loaded_modules:	list
	def __init__(self):
		self.loaded_modules = []
		self.load_config("./config.json")
		self.first_time = False
		self.load_data()
		commands.Bot.__init__(self, command_prefix=self.config.prefix)
		self.drive = googledrive.GDrive(self)

	
	def add_module(self, name):
		module = importlib.import_module(f".", f"program.Bot.cogs.{name}").Module

		module_instance = module(self)
		module_instance.data = self.data
		self.loaded_modules.append(module_instance)
		self.add_cog(module_instance)
		return module_instance


	async def on_ready(self):
		self.guild = (await self.fetch_guilds().flatten())[0]

		self.everyone = await self.get_role(self.guild.id)
		if self.first_time:
			await self.first_init()
		
		self.save()
		print("Ready!")
	
	async def first_init(self):
		print("First initialization")
		self.first_time = False
		self.data.server_id = self.guild.id
		
		case_manager = await self.guild.create_role(name="Case Manager", reason="Initialization")
		self.set_perm(case_manager.id, level=d.Perm.MANAGE)
		# Create channels
		cases = await self.guild.create_category("Cases", reason="Initialization")
		archive = await self.guild.create_category("Archive", reason="Initialization")
		divisions = await self.guild.create_category("Divisions", reason="Initialization")
		dashboard = await self.guild.create_text_channel("Dashboard", reason="Initialization")
		self.data.channels.cases = cases.id
		self.data.channels.archive = archive.id
		self.data.channels.divisions = divisions.id
		self.data.channels.dashboard = dashboard.id

		# Secure channels
		await self.lock_channel(cases, self.everyone, reason="Initialization")
		await self.lock_channel(archive, self.everyone, reason="Initialization")
		await self.lock_channel(divisions, self.everyone, reason="Initialization")
		
		await self.lock_channel(divisions, case_manager, send=True, read=True, reason="Initialization")
		await self.lock_channel(cases, case_manager, send=True, read=True, reason="Initialization")
		await self.lock_channel(archive, case_manager, send=True, read=True, reason="Initialization")
		#TODO: Create Dashboard
	

	def load_data(self):
		dta = {}
		try:
			with open(self.config.data_file, "r") as f:
				dta = json.loads(f.read(), object_hook=json_util.object_hook)
		except:
			self.first_time = True
		if dta['server_id'] == 0: self.first_time = True
		self.data:d.SaveData = d.SaveData.from_dict(dta)
		for x in self.loaded_modules:
			x.data = self.data
	

	def load_config(self, file):
		j4j = JSON4JSON.JSON4JSON()
		j4j.load(file, "./program/rules.json")
		cfg = j4j.data
		self.config:d.Config = d.Config.from_dict(cfg)

	def save(self):
		with open(self.config.data_file, 'w+') as f:
			f.write(json.dumps(self.data.to_dict(is_recursive=True), default=json_util.default, indent=4))
	
	async def on_command_error(self, ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.channel.send(f'Usage: ``{self.config["prefix"]}{ctx.command.__original_kwargs__["usage"]}``')
		else:
			traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
	
	#region----------COMMAND STUFF------------

	async def lock_channel(self, channel:discord.TextChannel, target, send=False, read=False, reason=""):
		"""Locks a channel to the target (role or member)
		"""
		overwrite = discord.PermissionOverwrite()
		overwrite.send_messages = send
		overwrite.read_messages = read
		await channel.set_permissions(target, overwrite=overwrite, reason=reason)
		
	
	async def update_managers(self):
		managers = []
		for i, p in self.data.perms: 
			if p >= d.Perm.MANAGE:
				role = await self.guild.get_role(int(i))
				managers.append(role)
		for x in [self.data.channels.archive, self.data.channels.cases, self.data.channels.divisions]:
			channel = await self.fetch_channel(x)
			for m in managers: await self.lock_channel(channel, m, send=True, read=True, reason="Manager")
		
				
	def set_perm(self, role_id, level=d.Perm.NONE):
		self.data.perms[str(role_id)] = level

	def share_case(self, case:d.Case, user_id:int):
		email = self.data.get_user(user_id).email
		if self.is_email(email):
			self.drive.share(case.drive_id, email, access="writer")
			return True
		return False
	#endregion
	#region--------HELPER METHODS-----------
	async def get_role(self, id):
		roles = await self.guild.fetch_roles()
		for x in roles:
			if x.id == int(id): return x
		print("Failed to get role", id)
	
	def has_permission(self, member, level=d.Perm.USE):
		highest_level = d.Perm.NONE
		for x in member.roles:
			if x != None and str(x.id) in self.data.perms:
				this_level = self.data.perms[str(x.id)]
				if this_level > highest_level: highest_level = this_level
		return highest_level >= level

	def pluralize(self, word, value, plural=None) -> str:
		if plural == None: plural = word + "s"
		if value == 1: return word
		return plural

	def mention(self, id, t='u') -> str:
		types = {'u': '@!', 'r': '@&'}
		return f"<{types[t[0]]}{id}>"

	def is_email(self, email:str) -> bool:
		return (len(email) > 5 and "." in email and email.count("@") == 1 and
			email[-1:] not in "@."
			and email[0] not in "@.")

	async def permission(self, ctx, level=d.Perm.MANAGE) -> bool:
		is_manager = self.has_permission(ctx.author, level=level)
		if is_manager == False:
			await ctx.send("Insufficient privileges")
		return is_manager
	#endregion
	#region--------OTHER EVENTS----------

	async def on_message(self, ctx: discord.Message):
		self.data.process_user(ctx.author.id)

		if str(ctx.channel.id) not in self.data.bot_messages:
			self.data.bot_messages[str(ctx.channel.id)] = []
		
		#embeds happen in the permanent type of things, like dashboard and case overviews. 
		# only consider removal if there is no embed
		if len(ctx.embeds) == 0: 
			if ctx.content.startswith(self.config.prefix) or ctx.author.id == self.user.id:
				self.data.bot_messages[str(ctx.channel.id)].append(ctx.id)
		
		return await super().on_message(ctx)

	#endregion