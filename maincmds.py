import os, time, random, sys, discord, JSON4JSON
from discord.ext import commands
from discord.ext.commands.core import command
from discord.utils import get
from bot import CaseBot

def mention(id):
	return f"<@!{id}>"


class MainCmds(commands.Cog):
	def __init__(self, bot: CaseBot):
		self.bot = bot
	@commands.command(brief='wipes everything')
	async def wipe(self, ctx):
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
	
	@commands.command(brief='sets the role privilleges')
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
				txt += f"<@&{x}>: {self.bot.CM.data['server']['roles'][x]}\n"
			await ctx.channel.send(txt)
		else:
			await ctx.channel.send("You are not a manager.")
	
	@commands.command(brief='creates a case')
	async def create(self, ctx, *, name):
		if self.bot.has_permission(ctx.author, perm='create'):
			if name in self.bot.CM.cases:
				existingCase = self.bot.CM.cases[name]
				existingChannel = None
				try:
					existingChannel = (await self.bot.fetch_channel(existingCase['channelID']))
				except:
					pass
				if existingChannel == None:
					await ctx.channel.send("Restoring case (channel messages have been wiped).")
					category = await self.bot.fetch_channel(self.bot.CM.data['server']['caseCategoryID'])
					caseChannel = await self.bot.server.create_text_channel(existingCase['name'], category=category)
					existingCase['channelID'] = caseChannel.id
					await self.update_case_info(existingCase)
				else:
					await ctx.channel.send("This case already exists!")
			else:
				await ctx.channel.send(f"making new case called {name}")
				case = self.bot.CM.create_case(name, ctx.author.id)
				category = await self.bot.fetch_channel(self.bot.CM.data['server']['caseCategoryID'])
				caseChannel = await self.bot.server.create_text_channel(case['name'], category=category)
				case['channelID'] = caseChannel.id
				msg = await caseChannel.send(embed= await self.get_case_embed(case))
				await msg.pin()
				case['messageID'] = msg.id
			self.bot.CM.save()
		else:
			await ctx.channel.send("You do not have the required permissions to do this.")
	

	#region-----------CASE SPECIFIC---------------

	async def case_command_info(self, ctx):
		case = None
		#get the case
		for x in self.bot.CM.cases:
			if self.bot.CM.cases[x]['channelID'] == ctx.channel.id:
				case = self.bot.CM.cases[x]
				break
		if case == None:
			await ctx.channel.send("You must use this command in a channel associated with a case.")
			return None, None, None
		#check if the user has perms to run this command
		perms = False
		for x in case['members']:
			if x == ctx.author.id:
				perms = True
				break
		manager = self.bot.has_permission(ctx.author, perm='manage') or case['manager'] == ctx.author.id
		return case, perms, manager
	
	@commands.command(brief="closes a case")
	async def close(self, ctx):
		case, perms, manager = await self.case_command_info(ctx)
		if not manager:
			await ctx.channel.send("You cannot close this case.")
		else:
			archiveCategory = await self.bot.fetch_channel(self.bot.CM.data['server']['archiveCategoryID'])
			case['status'] = "Closed"
			await ctx.channel.edit(category=archiveCategory)
			await self.update_case_info(case)
	@commands.command(brief="opens a case back up")
	async def reopen(self, ctx):
		case, perms, manager = await self.case_command_info(ctx)
		if not manager:
			await ctx.channel.send("You cannot close this case.")
		else:
			casesCategory = await self.bot.fetch_channel(self.bot.CM.data['server']['caseCategoryID'])
			case['status'] = "Open"
			await ctx.channel.edit(category=casesCategory)
			await self.update_case_info(case)
		
	@commands.command(brief="adds a member to a case")
	async def add(self, ctx, member):
		case, perms, manager = await self.case_command_info(ctx)
		if not manager:
			await ctx.channel.send("You cannot add people to this case because you are not a manager.")
		else:
			memberID = int(member.split("!")[1].replace(">", ""))
			member = await self.bot.fetch_user(memberID)
			if memberID not in case['members']:
				case['members'].append(memberID)
				await ctx.channel.send(f"Added {member.name} to the case.")
				await self.update_case_info(case)
				self.bot.CM.save()
			else:
				await ctx.channel.send(f"This member is already added to this case. Use `{self.bot.config['prefix']}remove` to remove them.")
	@commands.command(brief="adds a member to a case")
	async def remove(self, ctx, member):
		case, perms, manager = await self.case_command_info(ctx)
		if not manager:
			await ctx.channel.send("You cannot add people to this case because you are not a manager.")
		else:
			memberID = int(member.split("!")[1].replace(">", ""))
			member = await self.bot.fetch_user(memberID)
			if memberID in case['members']:
				case['members'].remove(memberID)
				await ctx.channel.send(f"Removed {member.name} from the case.")
				self.bot.CM.save()
			else:
				await ctx.channel.send(f"This member is not added to the case.")
	
			


	async def update_case_info(self, case):
		channel = await self.bot.fetch_channel(case['channelID'])
		msg = None
		try:
			msg = await channel.fetch_message(case['messageID'])
		except:
			pass
		if msg == None:
			msg = await channel.send(embed= await self.get_case_embed(case))
			await msg.pin()
			case['messageID'] = msg.id
		else:
			await msg.edit(embed= await self.get_case_embed(case))

	async def get_case_embed(self, case):
		creator = await self.bot.fetch_user(case['creator'])
		embed = discord.Embed(title=case['name'], description=f"""
		Opened by {creator} on {case['created'].strftime('%m/%d%/%Y, at %H:%M')} {self.bot.config['timezone']}
		"""
		)
		embed.add_field(name="Status", value=case['status'])
		members = ""
		for x in case['members']:
			members += mention(x) + "\n"
		members = members[:-1] #get rid of the last comma
		embed.add_field(name="Members", value=members)
		return embed
	#endregion