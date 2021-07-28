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
	
	async def fetch_role(self, role_id) -> discord.Role:
		return get(await self.bot.guild.fetch_roles(), id=role_id)
		

	async def restore_missing_roles_and_channels(self):
		divisions_category = await self.bot.fetch_channel(self.data.channels.divisions)
		for name, dept in self.data.departments.items():
			deptrole = await self.fetch_role(int(dept.role_id))
			if deptrole == None:
				print(f"Role for department {dept.name} ({dept.role_id}) is missing. Restoring...")
				deptrole = await self.bot.guild.create_role(name=dept.name, reason="restored")
				dept.role_id = deptrole.id

		for role_id, div in self.data.divisions.copy().items(): #(no, this copy doesn't also make a copy of the items in the dictionary. it only copies the dictionary, pointers are left untouched.)
			try:
				channel = await self.bot.fetch_channel(div.channel_id)
			except Exception as e:
				print(e)
				print(f"Channel for division {div.name} ({div.channel_id}) was destroyed. Restoring...")
				div_channel = await self.bot.guild.create_text_channel(name=div.name, category=divisions_category, topic=div.description, reason="restored")
				await self.bot.lock_channel(div_channel, self.bot.everyone)
				div.channel_id = div_channel.id
				divRole = await self.fetch_role(int(role_id))
				if divRole != None:
					await self.bot.lock_channel(div_channel, divRole, send=True, read=True)
			divRole = await self.fetch_role(int(role_id))
			if divRole == None:
				print(f"Role for division {div.name} ({div.role_id}) is missing. Restoring...")
				divRole = await self.bot.guild.create_role(name=div.name, reason="restored")
				div.role_id = divRole.id
				self.data.divisions[str(div.role_id)] = div
				del self.data.divisions[role_id] #remove the original but no longer relevant KVP in the dictionary
				channel = await self.bot.fetch_channel(div.channel_id)
				await self.bot.lock_channel(channel, divRole, send=True, read=True)
				self.bot.save()

	@commands.group(pass_context=True, brief="create | add | remove")
	async def department(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.channel.send("`" +  '` | `'.join("create | delete | add | remove".split(" | ")) + "`")
		pass

	@department.command(name="create", brief='creates a department', usage='department create [name] [description]')
	async def createdept(self, ctx, name, *, desc):
		if await self.bot.permission(ctx) == False: return
		
		if name in self.data.departments:
			await ctx.channel.send("This department already exists!")
			return
		
		deptrole = await self.bot.guild.create_role(name=name)
		dept = d.Department(name=name, description=desc, role_id=deptrole.id)
		self.data.departments[name] = dept
		await ctx.channel.send(f"Created department {self.bot.mention(deptrole.id, t='role')}.")
		self.bot.save()

	def get_dept(self, id):
		if type(id) == discord.Role:
			for _, x in self.data.departments.items():
				if int(x.role_id) == int(id.id):
					return x
		else:
			if id in self.data.departments:
				return self.data.departments[id]
		return None
	
	@department.command(name="add", brief="adds a division to a department.", usage="department add [@division] [@department]")
	async def adddept(self, ctx, division:discord.Role, department:discord.Role):
		if await self.bot.permission(ctx) == False: return
		div = await self.get_division(ctx, division)
		dept = self.get_dept(department)
		if div != None and dept != None:
			if div.name not in dept.divisions:
				dept.divisions.append(div.name)
				await ctx.channel.send(f"Division {self.bot.mention(div.role_id, t='r')} added to department {self.bot.mention(dept.role_id, t='r')}!")
			else:
				await ctx.channel.send("This division is already a part of this department.")
		else:
			if div == None: await ctx.channel.send("Division could not be found!")
			elif dept == None: await ctx.channel.send("Department could not be found!")
		self.bot.save()
	
	@department.command(name="remove", brief="removes a division from a department.", usage="department remove [@division] [@department]")
	async def removedept(self, ctx, division:discord.Role, department:discord.Role):
		if await self.bot.permission(ctx) == False: return
		div = await self.get_division(ctx, division)
		dept = self.get_dept(department)
		if div != None and dept != None:
			if div.name in dept.divisions:
				dept.divisions.remove(div.name)
				await ctx.channel.send(f"Division {self.bot.mention(div.role_id, t='r')} removed from department {self.bot.mention(dept.role_id, t='r')}!")
			else:
				await ctx.channel.send("This division is not part of this department!")
		else:
			if div == None: await ctx.channel.send("Division could not be found!")
			elif dept == None: await ctx.channel.send("Department could not be found!")
		self.bot.save()
	
	@department.command(name='delete', brief='removes a department.', usage='department delete [@department]')
	async def deletedept(self, ctx, department:discord.Role):
		if await self.bot.permission(ctx) == False: return
		dept = self.get_dept(department)
		if dept == None:
			await ctx.channel.send("Department does not exist")
			return
		r = await self.fetch_role(dept.role_id)
		await r.delete(reason=f"deleted department by {ctx.author.id} ({ctx.author.display_name})")
		del self.data.departments[dept.name]
		await ctx.channel.send("Department removed!")
		self.bot.save()

	@department.command(name="list", brief="shows a list of departments", usage="department list")
	async def listdepts(self, ctx):
		if await self.bot.permission(ctx, level=d.Perm.USE) == False: return
		if len(self.data.departments) <= 0:
			await ctx.channel.send("No departments to list.")
			return
		e = discord.Embed(title="Departments", description="\u200B")
		for _, dept in self.data.departments.items():
			e.add_field(name=dept.name, value=dept.description)
		await ctx.channel.send(embed=e)

	@commands.group(pass_context=True, brief="create | add | remove | list | members | info | setinfo | addleader | removeleader")
	async def division(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.channel.send("`create` | `add` | `remove` | `list` | `members` | `info` | `setinfo` | `addleader` | `removeleader` ")
		pass
	

	async def get_division(self, ctx, division):
		await self.restore_missing_roles_and_channels()
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

	def get_division_department(self, division:d.Division):
		for _, dept in self.data.departments.items():
			if division.name in dept.divisions:
				return dept
		return None


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
		#div = self.data.divisions[str(division.id)]
		div = await self.get_division(ctx, division)
		leaders = '\u200B'
		if len(div.leaders) > 0:
			leaders = "Division leaders: " + ', '.join([self.bot.mention(x) for x in div.leaders])
		e = discord.Embed(title=f"Members of {div.name}", description=leaders)
		for x in div.members:
			e.add_field(name="\u200B", value=self.bot.mention(x))
		if len(div.members) > 0:
			await ctx.channel.send(embed=e)
		else:
			await ctx.channel.send("This division has no members.")
		
	@division.command(brief='shows all divisions')
	async def list(self, ctx):
		await self.restore_missing_roles_and_channels()
		if self.bot.has_permission(ctx.author) == False:
			return
		e = discord.Embed(title="Divisions", description="\u200B")
		organized = {"No department": []}
		for _, x in self.data.departments.items():
			organized[x.name] = []
		
		for rid, div in self.data.divisions.items():
			dept = self.get_division_department(div)
			if dept == None: 	dept = "No department"
			else:				dept = dept.name
			organized[dept].append(div)
		
		for k, v in organized.items():
			divisionlist = []
			for x in v:
				desc = x.description or "no description found"
				divisionlist.append(f"{self.bot.mention(x.role_id, t='r')}\t - \t{desc}")
			if len(divisionlist) > 0:
				e.add_field(name=k, value='\n'.join(divisionlist))
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
		div_channel = await self.bot.guild.create_text_channel(name=name, category=divisions_category, topic=desc)
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
	
	@division.command(brief='adds a leader to a division. ', usage='division addleader [@member] [@division]')
	async def addleader(self, ctx, member:discord.Member, division:discord.Role):
		if await self.bot.permission(ctx, d.Perm.USE) == False: return
		if str(division.id) not in self.data.divisions:
			await ctx.channel.send("Not a division.")
			return
		div = self.data.divisions[str(division.id)]
		if ctx.author.id in div.leaders or await self.bot.permission(ctx):
			if member.id not in div.members:
				await ctx.channel.send("This member needs to be part of the division before being promoted to a division leader.")
				return
			if member.id in div.leaders:
				await ctx.channel.send("This member is already in this division.")
				return
			
			div.leaders.append(member.id)
			await ctx.channel.send(f"Added {self.bot.mention(member.id)} as a division leader for {div.name}.")
			self.bot.save()
	@division.command(brief='removes a leader from a division. ', usage='division removeleader [@member] [@division]')
	async def removeleader(self, ctx, member:discord.Member, division:discord.Role):
		if await self.bot.permission(ctx, d.Perm.USE) == False: return
		if str(division.id) not in self.data.divisions:
			await ctx.channel.send("Not a division.")
			return
		div = self.data.divisions[str(division.id)]
		if ctx.author.id in div.leaders or await self.bot.permission(ctx):
			if member.id not in div.leaders:
				await ctx.channel.send("Already not a leader!")
				return
			div.leaders.remove(member.id)
			await ctx.channel.send(f"Removed {self.bot.mention(member.id)} from {div.name} leaders.")
			self.bot.save()


	@division.command(brief='adds a member to a division', usage='division add [@member] [@division]')
	async def add(self, ctx, member: discord.Member, division: discord.Role):
		if await self.bot.permission(ctx, d.Perm.USE) == False: return
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
			#give them the relevant department role as well
			dept = self.get_division_department(div)
			await member.add_roles(await self.fetch_role(dept.role_id))
			await ctx.channel.send(f"Added {self.bot.mention(member.id)} to {div.name}.")
			self.bot.save()
		
	@division.command(brief='removes a member from a division', usage='division remove [@member] [@division]')
	async def remove(self, ctx, member: discord.Member, division: discord.Role):
		if await self.bot.permission(ctx, d.Perm.USE) == False: return
		if str(division.id) not in self.data.divisions:
			await ctx.channel.send("Invallid division")
			return
		
		div = self.data.divisions[str(division.id)]
		if ctx.author.id in div.leaders or await self.bot.permission(ctx):
			if member.id not in div.members:
				await ctx.channel.send("This member is not in this division.")
				return
			div.members.remove(member.id)
			dept = self.get_division_department(div)
			await member.remove_roles(division)
			
			#remove any roles that they don't need anymore. specifcally check and make sure all the other divisions this member is a part of aren't part of this department
			keep_department = False
			for r in member.roles:
				if r.id == div.role_id: continue
				if str(r.id) in self.data.divisions: #this is a division the member is part of. is it part of this department?
					dpt = self.get_division_department(self.data.divisions[str(r.id)])
					if dpt == dept:
						keep_department = True
			if keep_department == False:
				try:
					await member.remove_roles(await self.fetch_role(dept.role_id))
				except Exception as e:
					print(e)
					


			await ctx.channel.send(f"Removed {member.display_name} from {div.name}.")
			self.bot.save()



Module = Divisions