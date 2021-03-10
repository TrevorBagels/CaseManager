import os, time, random, sys, discord, JSON4JSON
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
		self.add_cog(MainCmds(self))
		self.CM = CaseManager(self.config)
		self.server: discord.Guild = None
		self.drive = GDrive(self)
	
	async def on_ready(self):
		print("Ready!")
		guilds = await self.fetch_guilds().flatten()
		self.server = guilds[0]
		if self.CM.firstTime:
			self.CM.data['server']['serverID'] = self.server.id	
			caseCategory = await self.server.create_category("Cases")
			archiveCategory = await self.server.create_category("Case Archive")
			self.CM.data['server']['caseCategoryID'] = caseCategory.id
			self.CM.data['server']['archiveCategoryID'] = archiveCategory.id
			caseManagerRole = await self.server.create_role(name="Case Manager")
			self.CM.data['server']['roles'][str(caseManagerRole.id)] = "manage"
		
		self.CM.save()
	
	def has_permission(self, user, perm="use"):#whether or not this user has a certain permission level
		highestLevel = 0 #0 = none, 1 = view, 2 = use, 3 = manage
		levels = {'view': 1, 'use': 2, 'create': 3, 'manage': 4}
		for x in user.roles:
			if str(x.id) in self.CM.data['server']['roles']:
				level = levels[self.CM.data['server']['roles'][str(x.id)]]
				if level > highestLevel:
					highestLevel = level
		return highestLevel >= levels[perm]
		


if __name__ == "__main__":
	from maincmds import MainCmds
	from casemanager import CaseManager
	bot = CaseBot()
	bot.run(bot.config['token'])