import os, time, random, sys, discord, JSON4JSON, traceback
from discord import guild
from discord.ext import commands
from discord.ext.commands.core import command
from discord.utils import get
from googledrive import GDrive


class CaseBot(commands.Bot):
	def __init__(self):
		j4j = JSON4JSON.JSON4JSON()
		j4j.load("config.json", "rules.json")
		self.config = j4j.data
		commands.Bot.__init__(self, command_prefix=self.config['prefix'])
		self.CM = CaseManager(self.config)
		self.Main = maincmds.Main(self)
		self.Cases = casecmds.Cases(self)
		self.Division = divisioncmds.Division(self)
		self.Dashboard = dashboard.Dashboard(self)
		self.add_cog(self.Main)
		self.add_cog(self.Cases)
		self.add_cog(self.Division)
		self.add_cog(self.Dashboard)
		self.server: discord.Guild = None
		self.drive = GDrive(self)
	async def get_role(self, id):
		roles = await self.server.fetch_roles()
		for x in roles:
			if x.id == id:
				return x
	async def on_ready(self):
		print("Ready!")
		guilds = await self.fetch_guilds().flatten()
		self.server = guilds[0]
		self.everyone = await self.get_role(self.server.id)
		if self.CM.firstTime:
			self.CM.data['server']['serverID'] = self.server.id	
			caseCategory = await self.server.create_category("Cases")
			archiveCategory = await self.server.create_category("Case Archive")
			self.Dashboard.dashboardChannel = await self.server.create_text_channel("Dashboard")
			self.CM.data['server']['dashboard']['category'] = self.Dashboard.dashboardChannel.id
			self.CM.data['server']['caseCategoryID'] = caseCategory.id
			self.CM.data['server']['archiveCategoryID'] = archiveCategory.id
			await self.lockChannel(caseCategory, self.everyone)
			await self.lockChannel(archiveCategory, self.everyone)
			caseManagerRole = await self.server.create_role(name="Case Manager")
			await self.lockChannel(caseCategory, caseManagerRole, send=True, read=True)
			await self.lockChannel(archiveCategory, caseManagerRole, send=True, read=True)
			self.CM.data['server']['roles'][str(caseManagerRole.id)] = "manage"
			await self.Dashboard.create_dashboard()
		else:
			await self.Dashboard.get_dashboard_channels()
		self.CM.save()
	
	async def lockChannel(self, channel, allowed, send=False, read=False):
		overwrite = discord.PermissionOverwrite()
		overwrite.send_messages = send
		overwrite.read_messages = read
		await channel.set_permissions(allowed, overwrite=overwrite)


	def has_permission(self, user, perm="use"):#whether or not this user has a certain permission level
		highestLevel = 0 #0 = none, 1 = view, 2 = use, 3 = manage
		levels = {'view': 1, 'use': 2, 'create': 3, 'manage': 4}
		for x in user.roles:
			if x != None and str(x.id) in self.CM.data['server']['roles']:
				level = levels[self.CM.data['server']['roles'][str(x.id)]]
				if level > highestLevel:
					highestLevel = level
		return highestLevel >= levels[perm]
	
	async def on_command_error(self, ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.channel.send(f'Usage: ``{self.config["prefix"]}{ctx.command.__original_kwargs__["usage"]}``')
		else:
			traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
	
	def get_email(self, userID):
		if str(userID) in self.CM.data['server']['members']:
			return self.CM.data['server']['members'][str(userID)]['email']
		return ""


if __name__ == "__main__":
	import maincmds, casecmds, divisioncmds, dashboard
	from casemanager import CaseManager
	bot = CaseBot()
	bot.run(bot.config['token'])