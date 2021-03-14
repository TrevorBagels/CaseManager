import math
import os, time, random, sys, discord, JSON4JSON, datetime
from discord.ext import commands
from discord.ext.commands.core import command
from discord.utils import get
from bot import CaseBot
from utilities import pluralize, mention



class Module(commands.Cog):
	def __init__(self, bot: CaseBot):
		self.bot = bot
		self.CM = self.bot.CM
	@commands.command(brief='purges all bot related stuff.')
	async def purgecommands(self, ctx):
		if self.bot.has_permission(ctx.author, perm='manage') == False: return
		for cID in self.CM.bot_msgs:
			channel = await self.bot.fetch_channel(int(cID))
			for mID in self.CM.bot_msgs[cID]:
				try:
					message = await channel.fetch_message(int(mID))
					await message.delete()
				except:
					pass
		self.CM.data['botMsgs'] = {}
		self.CM.bot_msgs = self.CM.data['botMsgs']
		self.CM.save()
	@commands.command(brief='wipes everything')
	async def wipe(self, ctx):
		if self.bot.config['dev'] == True:
			for x in self.CM.cases:
				channelID = self.CM.cases[x]['channelID']
				try:
					channel = await self.bot.fetch_channel(channelID)
					await channel.delete(reason='wiped')
				except:
					pass
			self.CM.data['cases'] = {}
			self.CM.cases = self.CM.data['cases']
			self.CM.save()
		else:
			await ctx.channel.send("Not in developer mode.")
	
	@commands.command(brief='sets the role privilleges', usage='perm [@role] [none | use | create | manage]')
	async def perm(self, ctx, role:discord.Role, level):
		if self.bot.has_permission(ctx.author, perm='manage'):
			if level.lower() not in ['view', 'use', 'create', 'manage', 'none']:
				await ctx.channel.send("Level must be one of the following: `none`, `view`, `use`, `create`, `manage`.")
			else:
				roleID = role.id
				self.CM.data['server']['roles'][roleID] = level.lower()
				await ctx.channel.send("Updated permissions for this role.")
				for c in self.CM.cases:
					case = self.CM.cases[c]
					await self.bot.Cases.set_security(case, case['security'])
				self.CM.save()
		else:
			await ctx.channel.send("You are not a manager.")

	@commands.command(brief='shows all permissions for roles')
	async def perms(self, ctx):
		if self.bot.has_permission(ctx.author, perm='manage'):
			txt = ""
			for x in self.CM.data['server']['roles']:
				txt += f"<@&{x}>: `{self.CM.data['server']['roles'][x]}`\n"
			await ctx.channel.send(txt)
		else:
			await ctx.channel.send("You are not a manager.")

	@commands.command(brief="sets your email", usage="setemail [your_email]")
	async def setemail(self, ctx, email):
		previousEmail = None
		if str(ctx.author.id) not in self.CM.data['server']['members']:
			self.CM.data['server']['members'][str(ctx.author.id)] = {"email": ""}
		else:
			previousEmail = self.bot.get_email(ctx.author.id)
		self.CM.data['server']['members'][str(ctx.author.id)]['email'] = email
		await ctx.channel.send(f"Your email address has been set to `{email}`")
		#go through and give access to google drive things
		for c in self.CM.cases:
			case = self.CM.cases[c]
			#unshare things from the previous email
			if ctx.author.id in case['members']:
				if previousEmail != None: self.bot.drive.unshare(case['driveID'], previousEmail)
				self.bot.drive.share(case['driveID'], email)
		self.CM.save()

