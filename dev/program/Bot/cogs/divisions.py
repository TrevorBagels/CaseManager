import math
import os, time, random, sys, discord, JSON4JSON, datetime
from discord.ext import commands
from discord.ext.commands.core import command
from discord.utils import get
from ...Core import data as d


class Divisions(commands.Cog):
	data:	d.SaveData
	def __init__(self, bot):
		from ..bot import CaseBot
		self.bot:CaseBot = bot
	
	@commands.group(pass_context=True)
	async def division(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.channel.send("`create` | `add` | `remove | list | members` ")
		pass
	
	@division.command(brief='shows members of a division', usage='division members [@division]')
	async def members(self, ctx, division: discord.Role):
		if self.bot.has_permission(ctx.author) == False:
			return
		txt = ""
		div = self.data.divisions[str(division.id)]
		for x in div.members:
			txt += " " + self.bot.mention(x) + ","
		if txt != "":
			txt = f"Members of {self.bot.mention(division.id, t='r')}:" + txt[:-1]
		else:
			txt = "This division has no members."
		await ctx.channel.send(txt)
		
	@division.command(brief='shows all divisions')
	async def list(self, ctx):
		if self.bot.has_permission(ctx.author) == False:
			return
		
		txt = ""
		for rid, div in self.data.divisions.items():
			txt += self.bot.mention(rid, t='role') + "\n"
		if txt == "": await ctx.channel.send("No divisons to list.")
		else: await ctx.channel.send(txt)
	
	@division.command(brief='creates a division', usage='division create [name] [(optional) description]')
	async def create(self, ctx, name, *description):
		if await self.bot.permission(ctx) == False: return
		desc = ""
		if len(description) > 0: desc = " ".join(description)
		
		if d.get(self.data.divisions, name=name) != None:
			await ctx.channel.send("This division already exists!")
			return
		divisions_category = await self.bot.fetch_channel(self.data.channels.divisions)
		div_channel = await self.bot.guild.create_text_channel(name=name, category=divisions_category)
		divRole = await self.bot.guild.create_role(name=name)
		await self.bot.lock_channel(div_channel, self.bot.everyone)
		await self.bot.lock_channel(div_channel, divRole, send=True, read=True)
		div = d.Division(name=name, description=desc, role_id=divRole.id, channel_id=div_channel.id)
		self.data.divisions[str(divRole.id)] = div
		await ctx.channel.send(f"Created division {self.bot.mention(divRole.id, t='role')}.")
		self.bot.save()
	
	@division.command(brief='deletes a division', usage='division delete [@division]')
	async def delete(self, ctx, division:discord.Role):
		if await self.bot.permission(ctx) == False: return

		if d.get(self.data.divisions, role_id=division.id) == None:
			await ctx.channel.send("This division doesn't exist.")
			return
		
		div = self.data.divisions[str(division.id)]
		for _, case in self.data.cases.items():
			if div.name in case.divisions:
				await self.bot.Cases._assign(div, case)
		channel = await self.bot.fetch_channel(div.channel_id)
		del self.data.divisions[str(division.id)]
		await division.delete(reason=f"{div.name} Removed by {ctx.author.id} ({ctx.author.name})")
		await ctx.channel.send(f"Deleted division {div.name}")
		await channel.delete()
		self.bot.save()
	@division.command(brief='adds a member to a division', usage='division add [@member] [@division]')
	async def add(self, ctx, member: discord.Member, division: discord.Role,):
		if str(division.id) not in self.data.divisions:
			await ctx.channel.send("Not a division.")
			return
		div = self.data.divisions[str(division.id)]
		if ctx.author.id in div.leaders or await self.bot.permission(ctx):
			if member.id in div.members:
				await ctx.channel.send("This member is already in this division.")
				return
			
			div.members.append(member.id)
			await member.add_roles(division)
			await ctx.channel.send(f"Added {self.bot.mention(member.id)} to {div.name}.")
			self.bot.save()
		
	@division.command(brief='removes a member from a division', usage='division remove [@member] [@division]')
	async def remove(self, ctx, member: discord.Member, division: discord.Role,):
		if str(division.id) not in self.data.divisions:
			await ctx.channel.send("Invallid division")
			return
		
		div = self.data.divisions[str(division.id)]
		if ctx.author.id in div.leaders or await self.bot.permission(ctx):
			if member.id not in div.members:
				await ctx.channel.send("This member is not in this division.")
				return
			
			div.members.remove(member.id)
			await member.remove_roles(division)
			await ctx.channel.send(f"Removed {member.display_name} from {div.name}.")
			self.bot.save()



Module = Divisions