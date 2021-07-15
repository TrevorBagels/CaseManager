import math
import os, time, random, sys, discord, JSON4JSON, datetime
from typing import final
from discord.ext import commands
from discord.ext.commands.core import command
from discord.utils import get
from ...Core import data as d



class Cases(commands.Cog):
	data:	d.SaveData
	def __init__(self, bot):
		from ..bot import CaseBot
		self.bot:CaseBot = bot

	@commands.command(brief="creates a custom case field", usage="createcasefield [name] [default value] [description] [order (integer)]")
	async def createcasefield(self, ctx, name, *parameters):
		if await self.bot.permission(ctx, level=d.Perm.MANAGE) == False: return
		parameters = list(parameters)
		for i in range(4): parameters.append(None)
		default = parameters[0] or ""
		desc = parameters[1] or ""
		order = parameters[2] or 0
		try: order = int(order)
		except: pass
		ccf = d.CustomCaseField(name=name)
		ccf.default = default
		ccf.description = desc
		ccf.order = order
		self.data.custom_case_fields[ccf.name] = ccf
		await ctx.channel.send("Created a new custom case field.")
		self.bot.save()
	
	@commands.command(brief="sets options for a case field.", usage="setoptions [field name] [options]")
	async def setoptions(self, ctx, name, *options):
		if await self.bot.permission(ctx, level=d.Perm.MANAGE) == False: return
		ccf:d.CustomCaseField = self.data.custom_case_fields[name]
		if ccf != None and len(options) > 0:
			ccf.options = list(options)
			await ctx.channel.send(f"Case field `{name}` new options: `{'` | `'.join(options)}`")
			self.bot.save()
		else:
			await ctx.channel.send(f"Case field `{name}` doesn't exist!")

	@commands.command(brief="removes a custom case field", usage="removecasefield [name]")
	async def removecasefield(self, ctx, name):
		if await self.bot.permission(ctx, level=d.Perm.MANAGE) == False: return
		if name in self.data.custom_case_fields:
			del self.data.custom_case_fields[name]
			await ctx.channel.send("Removed the custom case field.")
			self.bot.save()
		else:
			await ctx.channel.send(f"Case field `{name}` doesn't exist!")

	@commands.command(brief="shows custom case fields", usage="casefields")
	async def casefields(self, ctx):
		if await self.bot.permission(ctx, level=d.Perm.USE) == False: return
		e = discord.Embed(title="Custom Case Fields", description="Use `createcasefield` to create new case fields, and use `removecasefield` to delete custom case fields.")
		for _, x in self.data.custom_case_fields.items():
			o = ""
			if len(x.options) > 0: o = f"\nOptions: `{'` | `'.join(x.options)}`"
			e.add_field(name=x.name, value=f"{x.description}\nDefault: {x.default}{o}", inline=o=="")
		await ctx.channel.send(embed=e)
		self.bot.save()

	def add_custom_fields_to_case(self, case:d.Case):
		for _, f in self.data.custom_case_fields.items():
			if f.name not in case.custom_fields:
				case.custom_fields[f.name] = f.default
		
	@commands.command(brief="sets a custom field for the case", usage='setfield [field name] [value]')
	async def setfield(self, ctx, fieldname, *, value):
		case, perms, manager = await self.case_command_info(ctx)
		self.add_custom_fields_to_case(case)
		if manager == False:
			await ctx.channel.send("You do not have the required permissions to do this.")
			return
		chosen_field:d.CustomCaseField = None
		for _, x in self.data.custom_case_fields.items():
			if self.bot.similar(x.name, fieldname):
				chosen_field = x
				break
		if chosen_field == None:
			await ctx.channel.send("This field doesn't exist!")
		else:
			final_value = value
			if len(chosen_field.options) > 0:
				#choose the best match
				best_match = (None, 0)
				for x in chosen_field.options:
					v = self.bot.similarity(value, x)
					if v > best_match[1] and v > .5:
						best_match = (x, v)
				final_value = best_match[0]
			if final_value == None:
				await ctx.channel.send(f"Invallid option. Please choose from the following: `{'` | `'.join(chosen_field.options)}`")
				return
			else:
				case.custom_fields[chosen_field.name] = final_value
				await self.update_case_info(case)
				await ctx.channel.send(f"Set `{chosen_field.name}` to `{final_value}`")
				self.bot.save()
		


	@commands.command(brief='creates a case', usage='create [case name]')
	async def create(self, ctx, *, name):
		if await self.bot.permission(ctx, level=d.Perm.CREATE) == False: return

		await ctx.channel.send(f"Making new case called `\"{name}\"`. Please wait, this could take a few seconds.")
		case = d.Case(name=name)
		case.create(ctx.author, len(self.data.cases))
		self.data.cases[case.id] = case
		self.add_custom_fields_to_case(case)
		#make a google drive folder
		if self.bot.config.gdrive:
			caseFolder = self.bot.drive.new_folder(name)
			case.url = caseFolder['url']
			case.drive_id = caseFolder['id']
			#attempt to share with this user
			if self.bot.share_case(case, ctx.author.id) == False:
				await ctx.channel.send(f"It is recommended that you link your email to gain access to the case's Google Drive folder. Use `{self.bot.config.prefix}setemail [email]` to set your email address.")
		
		category = await self.bot.fetch_channel(self.data.channels.cases)
		caseChannel = await self.bot.guild.create_text_channel(case.id, category=category)
		case.channel = caseChannel.id
		msg = await caseChannel.send(embed=await self.get_case_embed(case))
		await msg.pin()
		case.message = msg.id

		await self.set_security(case, d.Security.STRICT)
		self.bot.save()

	@commands.command(brief="sets the security of a case", usage='security [open | strict]')
	async def security(self, ctx, level):
		case, perms, manager = await self.case_command_info(ctx)
		if manager == False:
			await ctx.channel.send("You do not have the required permissions to do this.")
			return
		if case == None: return
		levels = d.enum_options(d.Security)
		if level.upper() in levels:
			response = await self.set_security(case, d.Security[level.upper()])
			await ctx.channel.send(response)
		else:
			await ctx.channel.send(f"Invallid option. Must be one of the following: `{'` | `'.join(levels)}`")
			
		
	async def set_security(self, case:d.Case, level:d.Security) -> str:
		lastLevel = case.security.name
		case.security = level
		channel = await self.bot.fetch_channel(case.channel)


		await self.bot.lock_channel(channel, self.bot.user, send=True, read=True)
		
		for role_id, perm in self.data.perms.items():
			role = await self.bot.get_role(int(role_id))

			overwrite = discord.PermissionOverwrite()
			overwrite.read_messages = True
			overwrite.send_messages = False
			if perm == d.Perm.MANAGE:
				overwrite.send_messages = True
				overwrite.read_messages = True
			if perm == d.Perm.NONE:
				overwrite.send_messages = False
				overwrite.read_messages = False
			
			await channel.set_permissions(role, overwrite=overwrite)
		
		await self.update_case_info(case)
		self.bot.save()
		return (f"`{lastLevel}` -> `{level.name}`")

	@commands.command(brief='assigns/unassigns a division to the case', usage='assign [@division]')
	async def assign(self, ctx, division: discord.Role):
		case, perms, manager = await self.case_command_info(ctx)
		if not manager:
			await ctx.channel.send("You do not have the required permissions to do this.")
			return
		
		if case == None: return
		
		if str(division.id) not in self.data.divisions:
			await ctx.channel.send("The role you mentioned is not a valid division.")
			return
		else:
			await self._assign(self.data.divisions[str(division.id)], case, channel=ctx.channel)

	async def _assign(self, div:d.Division, case:d.Case, channel=None):
		if div.name not in case.divisions:
			case.divisions.append(div.name)
			await self.set_security(case, d.Security.OPEN)
			if channel != None: await channel.send(f"Assigned case to {self.bot.mention(div.role_id, t='r')}")
		else:
			case.divisions.remove(div.name)
			if len(case.divisions) == 0:
				await self.set_security(case, d.Security.STRICT)
			if channel != None: await channel.send(f"Unassigned case from {self.bot.mention(div.role_id, t='r')}")
		self.bot.save()
		await self.update_case_info(case)

	@commands.command(brief="joins a case (if the case is open)", usage='join [case ID]')
	async def join(self, ctx, caseID:str):
		if self.bot.has_permission(ctx.author):
			if caseID in self.data.cases:
				case = self.data.cases[caseID]
				if case.status == d.Status.CLOSED:
					await ctx.channel.send("This case is closed.")
					return
				if case.security == d.Security.OPEN:
					hasMatchingDivision:bool = len(case.divisions) == 0 #only true if the case has no divisions. then, it's open to anyone with 'use' perms
					for x in ctx.author.roles:
						if str(x.id) in self.data.divisions and self.data.divisions[str(x.id)].name in case.divisions:
							hasMatchingDivision = True
					
					if hasMatchingDivision:
						await self._add_to_case(ctx, case, ctx.author.id, member=ctx.author)
					self.bot.save()
				else:
					await ctx.channel.send("Case security is strict, you cannot add yourself to this case.")
			else:
				await ctx.channel.send("Case does not exist. Did you enter the wrong ID?")
		else:
			await ctx.channel.send("You do not have permission to join cases.")

	async def case_command_info(self, ctx) -> tuple[d.Case, bool, bool]:
		case = None
		#get the case
		for _, c in self.data.cases.items():
			if c.channel == ctx.channel.id:
				case = c
				break
		if case == None:
			await ctx.channel.send("You must use this command in a channel associated with a case.")
			return None, None, None
		#check if the user has perms to run this command
		perms = False
		for x in case.members:
			if x == ctx.author.id:
				perms = True
				break
		manager = self.bot.has_permission(ctx.author, level=d.Perm.MANAGE) or case.manager == ctx.author.id
		return case, perms, manager
	
	@commands.command(brief="transfers case responsibility to another user", usage='transfer [@new_manager]')
	async def transfer(self, ctx, target: discord.Member):
		case, perms, manager = await self.case_command_info(ctx)
		self.data.process_user(target.id)
		if case == None: return
		if not manager:
			await ctx.channel.send("You cannot do this.")
			return
		
		if case.manager == target.id:
			await ctx.channel.send("Already the manager of this case")
			return
		
		if self.bot.has_permission(target, level=d.Perm.USE):
			case.manager = target.id
			if target.id not in case.members:
				await self._add_to_case(ctx, case, target.id, member=target)
				user = self.data.get_user(target.id)
				shared = self.bot.share_case(case, user.id)
				if shared == False: await ctx.channel.send("**Note: the new manager does not have an email.**")
			await ctx.channel.send("Manager updated.")
			self.bot.save()
			await self.update_case_info(case)
		else:
			await ctx.channel.send("This target member does not have the right permissions to take ownership of a case.")
	
	@commands.command(brief="closes a case")
	async def close(self, ctx):
		case, perms, manager = await self.case_command_info(ctx)
		if case == None: return
		if not manager: await ctx.channel.send("You cannot close this case.")
		else: await self._close_case(case)
			
	
	async def _close_case(self, case:d.Case):
		case.status = d.Status.CLOSED
		case.closed = d.now()
		channel = await self.bot.fetch_channel(case.channel)
		await channel.send("Case closed.")
		archiveCategory = await self.bot.fetch_channel(self.data.channels.archive)
		await channel.edit(category=archiveCategory)
		await self.update_case_info(case)
		self.bot.save()
	async def _open_case(self, case:d.Case):
		case.status = d.Status.OPEN
		case.opened = d.now()
		channel = await self.bot.fetch_channel(case.channel)
		await channel.send("Case re-opened")
		cases_category = await self.bot.fetch_channel(self.data.channels.cases)
		await channel.edit(category=cases_category)
		await self.update_case_info(case)
		self.bot.save()

	@commands.command(brief="opens a case back up")
	async def reopen(self, ctx):
		case, perms, manager = await self.case_command_info(ctx)
		if case == None: return
		if not manager: await ctx.channel.send("You cannot reopen this case.")
		else: await self._open_case(case)
		
	@commands.command(brief="adds a member to a case", usage='add [@member]')
	async def add(self, ctx, member: discord.Member):
		case, perms, manager = await self.case_command_info(ctx)
		if not manager:
			await ctx.channel.send("You cannot add people to this case because you are not a manager.")
		else:
			await self._add_to_case(ctx, case, member.id, member=member)
			
	
	async def _add_to_case(self, ctx, case:d.Case, memberID:int, member:discord.Member=None):
		if member == None: member = await self.bot.fetch_user(memberID)

		if memberID not in case.members:
			case.members.append(memberID)
			user = self.data.get_user(memberID)
			if self.bot.config.gdrive:
				if self.bot.share_case(case, user.id) == False:
					await ctx.channel.send("Note: This user does not have an email set, so they won't have Google Drive access.")
			#assign channel permission
			channel = await self.bot.fetch_channel(case.channel)
			if member != None: 
				await self.bot.lock_channel(channel, member, send=True, read=True)
			
			await ctx.channel.send(f"Added {member.name} to the case.")
			await self.update_case_info(case)
			self.bot.save()
		else:
			await ctx.channel.send(f"{member.name} is already added to this case. Use `{self.bot.config.prefix}remove` to remove them.")
	
		
	@commands.command(brief="removes a member from a case", usage='remove [@member]')
	async def remove(self, ctx, member: discord.Member):
		case, perms, manager = await self.case_command_info(ctx)
		if not manager:
			await ctx.channel.send("You cannot remove people from this case because you are not a manager.")
		else:
			await self._remove_from_case(ctx, case, member.id, member=member)
		
	async def _remove_from_case(self, ctx, case:d.Case, memberID, member=None):
		if member == None: member = await self.bot.fetch_user(memberID)
		if memberID in case.members:
			case.members.remove(memberID)
			await ctx.channel.send(f"Removed {member.name} from the case.")
			#now find their email perms
			user = self.data.get_user(memberID)
			if self.bot.is_email(user.email):
				self.bot.drive.unshare(case.drive_id, user.email)
			#revoke access to the channel 
			channel = await self.bot.fetch_channel(case.channel)
			await self.bot.lock_channel(channel, member)
			self.bot.save()
			await self.update_case_info(case)
		else:
			await ctx.channel.send(f"This member is not added to the case.")
	
	async def update_case_info(self, case:d.Case):
		channel = await self.bot.fetch_channel(case.channel)
		msg = None
		try:
			msg = await channel.fetch_message(case.message)
		except:
			pass
		if msg == None:
			msg = await channel.send(embed = await self.get_case_embed(case))
			await msg.pin()
			case.message = msg.id
		else:
			await msg.edit(embed= await self.get_case_embed(case))

	async def get_case_embed(self, case:d.Case) -> discord.Embed:
		self.add_custom_fields_to_case(case)
		colors = {"OPEN": 0x00ff00, "CLOSED": 0xff0000}
		color = discord.Color.blue
		if case.status.name in colors: color = colors[case.status.name]
		embed = discord.Embed(title=case.name, description=f"""
		Opened by {self.bot.mention(case.creator)} on 
		{case.created.strftime('%m/%d%/%Y, at %H:%M')} UTC
		""",
		color=color
		)
		embed.add_field(name="Status", value=case.status.name)
		embed.add_field(name="Manager", value=self.bot.mention(case.manager))
		members = ""
		for x in case.members:
			members += self.bot.mention(x) + "\n"
		members = members[:-1] #get rid of the last comma
		embed.add_field(name="Members", value=members)
		embed.add_field(name="Security", value=self.bot.Dashboard.get_case_security_string(case))
		if case.status == d.Status.CLOSED:
			embed.add_field(name="Closed",value= f"{case.created.strftime('%m/%d%/%Y, at %H:%M')} UTC")

		def custom_field_sort(item):
			print(item)
			return self.data.custom_case_fields[item[0]].order
		
		custom_fields = list(case.custom_fields.items())
		custom_fields.sort(key=custom_field_sort)
		for x in custom_fields:
			v = x[1]
			if v == "": v = "\u200B"
			embed.add_field(name=x[0], value=x[1])
		
		if self.bot.config.gdrive:
			embed.add_field(name="Google Drive", value=case.url, inline=False)
		return embed
	
	



Module = Cases