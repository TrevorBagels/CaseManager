import math
import os, time, random, sys, discord, JSON4JSON, datetime
from discord.ext import commands
from discord.ext.commands.core import command
from discord.utils import get
from bot import CaseBot
from utilities import pluralize, mention



class Main(commands.Cog):
	def __init__(self, bot: CaseBot):
		self.bot = bot
	@commands.command(brief='wipes everything')
	async def wipe(self, ctx):
		if self.bot.config['dev'] == True:
			for x in self.bot.CM.cases:
				channelID = self.bot.CM.cases[x]['channelID']
				try:
					channel = await self.bot.fetch_channel(channelID)
					await channel.delete(reason='wiped')
				except:
					pass
			self.bot.CM.data['cases'] = {}
			self.bot.CM.cases = self.bot.CM.data['cases']
			self.bot.CM.save()
		else:
			await ctx.channel.send("Not in developer mode.")
	
	@commands.command(brief='sets the role privilleges', usage='perm [@role] [none | use | create | manage]')
	async def perm(self, ctx, role, level):
		if self.bot.has_permission(ctx.author, perm='manage'):
			if level.lower() not in ['view', 'use', 'create', 'manage', 'none']:
				await ctx.channel.send("Level must be one of the following: `none`, `view`, `use`, `create`, `manage`.")
			else:
				roleID = role.split("<@&")[1].split(">")[0]
				self.bot.CM.data['server']['roles'][roleID] = level.lower()
				await ctx.channel.send("Updated permissions for this role.")
				self.bot.CM.save()
		else:
			await ctx.channel.send("You are not a manager.")
	@commands.command(brief='shows all permissions for roles')
	async def perms(self, ctx):
		if self.bot.has_permission(ctx.author, perm='manage'):
			txt = ""
			for x in self.bot.CM.data['server']['roles']:
				txt += f"<@&{x}>: `{self.bot.CM.data['server']['roles'][x]}`\n"
			await ctx.channel.send(txt)
		else:
			await ctx.channel.send("You are not a manager.")
	
	@commands.command(brief='creates a division', usage='division [name] [description]')
	async def division(self, ctx, name, *, description):
		if self.bot.has_permission(ctx.author, perm='manage') == False:
			await ctx.channel.send("You do not have permissions to do this.")
			return
		divRole = await self.bot.server.create_role(name=name)
		div = self.bot.CM.create_division(name, description, divRole.id)
		await ctx.channel.send(f"Created division {mention(divRole.id, t='role')}.")
		self.bot.CM.save()

	@commands.command(brief="sets your email", usage="setemail [your_email]")
	async def setemail(self, ctx, email):
		previousEmail = None
		if str(ctx.author.id) not in self.bot.CM.data['server']['members']:
			self.bot.CM.data['server']['members'][str(ctx.author.id)] = {"email": ""}
		else:
			previousEmail = self.bot.get_email(ctx.author.id)
		self.bot.CM.data['server']['members'][str(ctx.author.id)]['email'] = email
		await ctx.channel.send(f"Your email address has been set to `{email}`")
		#go through and give access to google drive things
		for c in self.bot.CM.cases:
			case = self.bot.CM.cases[c]
			if ctx.author.id in case['members']:
				if previousEmail != None: self.bot.drive.unshare(case['driveID'], previousEmail)
				self.bot.drive.share(case['driveID'], email)
		self.bot.CM.save()

