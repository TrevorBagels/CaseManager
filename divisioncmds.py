import math
import os, time, random, sys, discord, JSON4JSON, datetime
from discord.ext import commands
from discord.ext.commands.core import command
from discord.utils import get
from bot import CaseBot
from utilities import pluralize, mention



class Division(commands.Cog):
	def __init__(self, bot: CaseBot):
		self.bot = bot
	
	@commands.group(pass_context=True)
	async def division(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.channel.send("`create` | `add` | `remove | list | members` ")
		pass
	@division.command(brief='shows members of a division', usage='division members [@division]')
	async def members(self, ctx, division: discord.Role):
		if self.bot.has_permission(ctx.author):
			txt = ""
			div = self.bot.CM.data['server']['divisions'][str(division.id)]
			for x in div['members']:
				txt += " " + mention(x) + ","
			if txt != "":
				txt = f"Members of {mention(division.id, t='role')}:" + txt[:-1]
			else:
				txt = "This division has no members."
			await ctx.channel.send(txt)
		else:
			await ctx.channel.send("No permission.")
		
	@division.command(brief='shows all divisions')
	async def list(self, ctx):
		if self.bot.has_permission(ctx.author):
			txt = ""
			for x in self.bot.CM.data['server']['divisions']:
				txt += mention(x, t='role') + "\t\t`" + self.bot.CM.data['server']['divisions'][x]['desc'] + "`"
			await ctx.channel.send(txt)
		else:
			await ctx.channel.send("No permission.")
	@division.command(brief='creates a division', usage='division create [name] [description]')
	async def create(self, ctx, name, *, description):
		if self.bot.has_permission(ctx.author, perm='manage') == False:
			await ctx.channel.send("You do not have permissions to do this.")
			return
		divRole = await self.bot.server.create_role(name=name)
		div = self.bot.CM.create_division(name, description, divRole.id)
		await ctx.channel.send(f"Created division {mention(divRole.id, t='role')}.")
		self.bot.CM.save()
	@division.command(brief='adds a member to a division', usage='division add [@member] [@division]')
	async def add(self, ctx, member: discord.Member, division: discord.Role,):
		if str(division.id) not in self.bot.CM.data['server']['divisions']:
			await ctx.channel.send("Invallid division")
			return
		div = self.bot.CM.data['server']['divisions'][str(division.id)]
		if ctx.author.id in div['leaders'] or self.bot.has_permission(ctx.author, perm="manage"):
			if member.id in div['members']:
				await ctx.channel.send("This member is already in this division.")
				return
			div['members'].append(member.id)
			await member.add_roles(division)
			await ctx.channel.send(f"Added {member.display_name} to {div['name']}.")
			self.bot.CM.save()
		else:
			await ctx.channel.send("No permission")
	@division.command(brief='removes a member from a division', usage='division remove [@member] [@division]')
	async def remove(self, ctx, member: discord.Member, division: discord.Role,):
		if str(division.id) not in self.bot.CM.data['server']['divisions']:
			await ctx.channel.send("Invallid division")
			return
		div = self.bot.CM.data['server']['divisions'][str(division.id)]
		if ctx.author.id in div['leaders'] or self.bot.has_permission(ctx.author, perm="manage"):
			if member.id not in div['members']:
				await ctx.channel.send("This member is not in this division.")
				return
			div['members'].remove(member.id)
			await member.remove_roles(division)
			await ctx.channel.send(f"Removed {member.display_name} from {div['name']}.")
			self.bot.CM.save()
		else:
			await ctx.channel.send("No permission")

