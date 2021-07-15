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
	
	@commands.group(pass_context=True, brief="create | add | remove | list | members | info | setinfo")
	async def division(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.channel.send("`create` | `add` | `remove` | `list` | `members` | `info` | `setinfo` ")
		pass
	

	async def get_division(self, ctx, division):
		if type(division) == discord.Role:
			if str(division.id) in self.data.divisions:
				return self.data.divisions[str(division.id)]
			else:
				await ctx.channel.send("This role is not part of a division.")
		if type(division) == str:
			for k, d in self.data.divisions.items():
				if d.name.lower() == division or d.description.lower() == division:
					return d
		await ctx.channel.send("Could not find this division. ")
			


	@division.command(brief='shows info about a division', usage='division info [@division]')
	async def info(self, ctx, division: discord.Role):
		div = await self.get_division(ctx, division)
		if div.info != None and div.info != "":
			await ctx.channel.send(div.info)
		elif div.description != None and div.description != "":
			await ctx.channel.send(div.description)
		else:
			await ctx.channel.send("No further info for this division. ")
	
	@division.command(brief='sets info for  a division', usage='division setinfo [@division]')
	async def setinfo(self, ctx, division: discord.Role, *info):
		
		if len(info) > 0: info = " ".join(info)
		
		if self.bot.has_permission(ctx.author) == False:
			return
		div = await self.get_division(ctx, division)
		e = discord.Embed(title="result of setinfo", description="\u200B")
		oi = "no info set"
		if div.info != None and div.info != "":
			oi = div.info
		e.add_field(name="original info",value=oi)
		e.add_field(name="new info", value=str(info))
		div.info = info
		await ctx.channel.send(embed=e)
		self.bot.save()

	@division.command(brief='shows members of a division', usage='division members [@division]')
	async def members(self, ctx, division: discord.Role):
		if self.bot.has_permission(ctx.author) == False:
			return
		txt = ""
		#div = self.data.divisions[str(division.id)]
		div = await self.get_division(ctx, division)
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
		e = discord.Embed(title="Divisions", description="\u200B")
		
		for rid, div in self.data.divisions.items():
			desc = div.description or "no description found"
			e.add_field(name=div.name, value=desc)
		if len(self.data.divisions) == 0: await ctx.channel.send("No divisons to list.")
		else: await ctx.channel.send(embed=e)
	
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