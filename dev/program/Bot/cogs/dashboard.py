import math
import os, time, random, sys, discord, JSON4JSON, datetime
from discord.ext import tasks
from discord.ext import commands
from discord.ext.commands.core import command
from discord.utils import get
from ...Core import data as d



class Dashboard(commands.Cog):
	data:	d.SaveData
	def __init__(self, bot):
		from ..bot import CaseBot
		self.bot:CaseBot= bot
		self.dashboard:discord.TextChannel = None
		self.loop_started = False
	
	async def get_dashboard_channels(self): #called during on_ready
		self.dashboard 	= await self.bot.fetch_channel(self.data.channels.dashboard)
		self.main 		= await self.dashboard.fetch_message(self.data.channels.dashboard_main)
		self.cases 		= await self.dashboard.fetch_message(self.data.channels.dashboard_cases)
	
	async def create_dashboard(self):
		self.dashboard 	= await self.bot.fetch_channel(self.data.channels.dashboard)
		self.main = await self.dashboard.send(embed=discord.Embed(title="\u200B", description="\u200B"))
		self.cases = await self.dashboard.send(embed=discord.Embed())
		self.data.channels.dashboard_cases 	= self.cases.id
		self.data.channels.dashboard_main 	= self.main.id
		await self.get_dashboard_channels()
		
	@tasks.loop(seconds=10)
	async def update_dashboard(self):
		await self.main.edit(embed 	= await self.get_main_embed())
		await self.cases.edit(embed	= await self.get_cases_embed())


	async def get_main_embed(self):
		opened = []
		closed = []
		for cid, case in self.data.cases.items():
			if case.status == d.Status.OPEN: opened.append(case)
			else: closed.append(case)
		
		embed = discord.Embed(title="Dashboard", description="\u200B")
		
		embed.add_field(name="\u200B",value=f"{len(opened)} {self.bot.pluralize('case', len(opened))} open.")
		embed.add_field(name="\u200B",value=f"{len(closed)} {self.bot.pluralize('case', len(closed))} closed.")

		divisions = ""
		
		for r, div in self.data.divisions.items():
			divisions += f"{self.bot.mention(r, t='r')}: {len(div.members)} {self.bot.pluralize('member', len(div.members))}\n"
		if divisions == "": divisions = "No divisions."

		embed.add_field(name="\u200B", value="\u200B", inline=False)
		embed.add_field(name=f"Divisions", value=divisions)
		return embed
	
	def get_case_security_string(self, case:d.Case) -> str:
		security = case.security.name
		if security == "OPEN":
			security = "open to all divisions"
			if len(case.divisions) > 0:
				security = "open to"
				for dname in case.divisions:
					security += f" {self.bot.mention(d.get(self.data.divisions, name=dname).name, t='r')},"
				security = security[:-1]
		return security.capitalize()

	async def get_cases_embed(self) -> discord.Embed:
		opened:list[d.Case] = []
		closed = []
		for cid, case in self.data.cases.items():
			if case.status == d.Status.OPEN: opened.append(case)
			else: closed.append(case)
		
		embed = discord.Embed(title="Cases", description=f"\u200B")
		for case in opened:
			security = self.get_case_security_string(case)
			embed.add_field(name=case.id, value=f"""
			\"{case.name}\"
			Currently managed by {self.bot.mention(case.manager)}
			Security: {security}
			Open for {self.time_passed(case.opened, d.now())}
			{len(case.members)} {self.bot.pluralize('member', len(case.members))} assigned
			""")
		return embed
	
	def time_passed(self, then:datetime.datetime, now:datetime.datetime) -> str:
		s = ""
		to = now - then
		v = to.days
		if v < 1: v = int(to.seconds / 60 / 60) #hours
		else: return f"{v} {self.bot.pluralize('day', v)}"
		#now we're converted to hours
		if v < 1: v = int(to.seconds / 60) #minutes
		else: return f"{v} {self.bot.pluralize('hour', v)}"
		#now we're converted to minutes
		if v < 1: v = int(to.seconds)
		else: return f"{v} {self.bot.pluralize('minute', v)}"
		#now we're converted to seconds
		return f"{v} {self.bot.pluralize('second', v)}"





Module = Dashboard