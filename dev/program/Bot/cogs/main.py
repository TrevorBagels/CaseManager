import math
import os, time, random, sys, discord, JSON4JSON, datetime
from discord.ext import commands
from discord.ext.commands.core import command
from discord.utils import get
from ...Core import data as d


class Main(commands.Cog):
	data:	d.SaveData #automatically gets referenced to self.bot.data
	def __init__(self, bot):
		from ..bot import CaseBot
		self.bot : CaseBot = bot
	

	@commands.command(brief='turns off the bot')
	async def shutdown(self, ctx):
		if self.bot.has_permission(ctx.author, level=d.Perm.MANAGE):
			self.bot.save()
			await ctx.channel.send("Shutting down...")
			await self.bot.logout()
		pass
	
	

	@commands.command(brief='purges all bot related stuff.')
	async def purgecommands(self, ctx):
		if self.bot.has_permission(ctx.author, level=d.Perm.MANAGE) == False: return
		for mID in self.data.bot_messages[str(ctx.channel.id)]:
			try:
				message = await ctx.channel.fetch_message(int(mID))
				await message.delete()
			except:
				pass
		self.data.bot_messages = {}
		self.bot.save()
	
	@commands.command(brief='sets the role privilleges', usage='perm [@role] [restricted | none | use | create | manage')
	async def perm(self, ctx, role:discord.Role, level):
		if await self.bot.permission(ctx) == False: return
		if level.upper() not in dir(d.Perm) or level.startswith("_"):
			await ctx.channel.send("Level must be one of the following: `restricted`, `none`, `view`, `use`, `create`, `manage`.")
		else:
			roleID = str(role.id)
			self.data.perms[roleID] = d.Perm[level.upper()]
			await ctx.channel.send(f"`{role.name}` now has `{level.upper()}` permissions.")
			for c in self.data.cases:
				case = self.data.cases[c]
				await self.bot.Cases.set_security(case, case.security) #update security
			self.bot.save()

	@commands.command(brief='shows all permissions for roles')
	async def perms(self, ctx):
		if await self.bot.permission(ctx) == False: return
		txt = ""
		for x, p in self.data.perms.items():
			txt += f"<@&{x}>: `{p.name}`\n"
		await ctx.channel.send(txt)
	@commands.command(brief='shows all permissions for a member')
	async def permsof(self, ctx, member:discord.Member):
		if await self.bot.permission(ctx) == False: return
		txt = ""
		perms = []
		for role in member.roles:
			if str(role.id) in self.data.perms and self.data.perms[str(role.id)].name not in perms:
				perms.append(self.data.perms[str(role.id)].name)
		if len(perms) > 0: await ctx.channel.send(", ".join(perms))
		else: await ctx.channel.send("This user has no perms.")


	@commands.command(brief="sets your email. necessary for google drive access. ", usage="setemail [name@domain.com]")
	async def setemail(self, ctx, email):
		prev_email = self.data.get_user(ctx.author.id).email
		if self.bot.is_email(email) == False:
			await ctx.channel.send("Invallid email")
			return
		
		self.data.get_user(ctx.author.id).email = email

		await ctx.channel.send(f"Your email address has been set to `{email}`")
		
		#go through and give access to google drive things
		for c, case in self.data.cases.items():
			#unshare things from the previous email
			if ctx.author.id in case.members:
				if prev_email != None: self.bot.drive.unshare(case.drive_id, prev_email)
				self.bot.drive.share(case.drive_id, email)
		self.bot.save()



Module = Main