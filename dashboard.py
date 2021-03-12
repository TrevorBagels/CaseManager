import math
import os, time, random, sys, discord, JSON4JSON, datetime
from discord.ext import tasks
from discord.ext import commands
from discord.ext.commands.core import command
from discord.utils import get
from bot import CaseBot
from utilities import pluralize, mention



class Dashboard(commands.Cog):
	def __init__(self, bot: CaseBot):
		self.bot = bot
		self.CM = self.bot.CM
		self.dashboardChannel = None
		self.main = None
		self.cases = None
	
	async def get_dashboard_channels(self):
		self.dashboardChannel = await self.bot.fetch_channel(self.CM.data['server']['dashboard']['category'])
		self.main =  await self.dashboardChannel.fetch_message(self.CM.data['server']['dashboard']['main'])
		self.cases = await self.dashboardChannel.fetch_message(self.CM.data['server']['dashboard']['cases'])
		print("Dashboard loaded")
		self.update_dashboard.start()
	async def create_dashboard(self):
		self.main = await self.dashboardChannel.send(embed=discord.Embed(title="\u200B", description="\u200B"))
		self.cases = await self.dashboardChannel.send(embed=discord.Embed())
		self.CM.data['server']['dashboard']['main'] = self.main.id
		self.CM.data['server']['dashboard']['cases'] = self.cases.id
		self.get_dashboard_channels()
		
	@tasks.loop(seconds=10)
	async def update_dashboard(self):
		await self.main.edit(embed=await self.get_main_embed())
		await self.cases.edit(embed=await self.get_cases_embed())


	async def get_main_embed(self):	
		openCases = []
		closedCases = []
		for x in self.bot.CM.cases:
			case = self.bot.CM.cases[x]
			if case['status'] == "Open": openCases.append(case)
			else: closedCases.append(case)
		embed = discord.Embed(title="Dashboard", description="\u200B")
		embed.add_field(name="\u200B",value=f"{len(openCases)} {pluralize('case', len(openCases))} open.")
		embed.add_field(name="\u200B",value=f"{len(closedCases)} {pluralize('case', len(closedCases))} closed.")
		divisions = ""
		for d in self.CM.data['server']['divisions']:
			div = self.CM.data['server']['divisions'][d]
			divisions += f"{mention(d, t='role')}: {len(div['members'])} {pluralize('member', len(div['members']))}\n"
		if divisions == "": divisions = "No divisions."
		embed.add_field(name="\u200B", value="\u200B", inline=False)
		embed.add_field(name=f"Divisions", value=divisions)
		return embed
	
	def get_case_security_string(self, case):
		security = case['security']
		if security == 'open':
			security = "open to all divisions"
			if len(case['divisions']) > 0:
				security = "open to"
				for d in case['divisions']:
					security += f" {mention(self.CM.get_division(d)['id'], t='role')},"
				security = security[:-1]
		return security.capitalize()

	async def get_cases_embed(self):
		openCases = []
		closedCases = []
		for x in self.bot.CM.cases:
			case = self.bot.CM.cases[x]
			if case['status'] == "Open": openCases.append(case)
			else: closedCases.append(case)
		embed = discord.Embed(title="Cases", description=f"\u200B")
		for x in openCases:
			timeOpened = datetime.datetime.now(datetime.timezone.utc) - x['opened']
			days = timeOpened.days
			timeOpened = f"{days} {pluralize('day', days)}"
			security = self.get_case_security_string(x)
			embed.add_field(name=x['id'], value=f"""
			\"{x['name']}\"
			Currently managed by {mention(x['manager'])}
			Security: {security}
			Open for {timeOpened}
			{len(x['members'])} {pluralize('member', len(x['members']))} assigned
			""")
		return embed