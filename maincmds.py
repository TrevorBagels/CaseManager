import math
import os, time, random, sys, discord, JSON4JSON, datetime
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
	@commands.command(brief="sets your email", usage="setemail [your_email]")
	async def setemail(self, ctx, email):
		previousEmail = None
		if str(ctx.author.id) not in self.bot.CM.data['server']['members']:
			self.bot.CM.data['server']['members'][str(ctx.author.id)] = {"email": ""}
		else:
			previousEmail = self.get_email(ctx.author.id)
		self.bot.CM.data['server']['members'][str(ctx.author.id)]['email'] = email
		await ctx.channel.send(f"Your email address has been set to `{email}`")
		#go through and give access to google drive things
		for c in self.bot.CM.cases:
			case = self.bot.CM.cases[c]
			if ctx.author.id in case['members']:
				if previousEmail != None: self.bot.drive.unshare(case['driveID'], previousEmail)
				self.bot.drive.share(case['driveID'], email)
		self.bot.CM.save()
	@commands.command(brief='lists all cases')
	async def cases(self, ctx):
		if self.bot.has_permission(ctx.author, perm='use'):
			openCases = []
			closedCases = []
			for x in self.bot.CM.cases:
				case = self.bot.CM.cases[x]
				if case['status'] == "Open": openCases.append(case)
				else: closedCases.append(case)
			embed = discord.Embed(title="Dashboard", description=f"{len(openCases)} {pluralize('case', len(openCases))} open.")
			for x in openCases:
				timeOpened = datetime.datetime.now(datetime.timezone.utc) - case['opened']
				days = timeOpened.days
				timeOpened = f"{days} {pluralize('day', days)}"
				embed.add_field(name=x['id'], value=f"""
				\"{x['name']}\"
				Currently managed by {mention(x['manager'])}.
				Open for {timeOpened}.
				{len(x['members'])} {pluralize('member', len(x['members']))} assigned.
				""")
			await ctx.channel.send(embed=embed)
	@commands.command(brief='creates a case', usage='create [case name]')
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
					caseChannel = await self.bot.server.create_text_channel(existingCase[self.bot.config['casePropertyForChannelNaming']], category=category)
					existingCase['channelID'] = caseChannel.id
					await self.update_case_info(existingCase)
				else:
					await ctx.channel.send("This case already exists!")
			else:
				await ctx.channel.send(f"Making new case called `\"{name}\"`")
				case = self.bot.CM.create_case(name, ctx.author.id)
				await ctx.channel.send(f"This case's ID is `{case['id']}`")
				#make a google drive folder
				if self.bot.config['gdrive']:
					caseFolder = self.bot.drive.new_folder(name)
					case['url'] = caseFolder['url']
					case['driveID'] = caseFolder['id']
					emailFound = False
					if str(ctx.author.id) in self.bot.CM.data['server']['members']:
						email = self.bot.CM.data['server']['members'][str(ctx.author.id)]['email']
						if "@" in email:
							emailFound = True
							self.bot.drive.share(case['driveID'], email, access="writer")
					if emailFound == False:
						await ctx.channel.send(f"It is recommended that you link your email to gain access to the case's Google Drive folder. Use `{self.bot.config['prefix']}setemail [email]` to set your email address.")
				category = await self.bot.fetch_channel(self.bot.CM.data['server']['caseCategoryID'])
				caseChannel = await self.bot.server.create_text_channel(case[self.bot.config['casePropertyForChannelNaming']], category=category)
				case['channelID'] = caseChannel.id
				msg = await caseChannel.send(embed= await self.get_case_embed(case))
				await msg.pin()
				case['messageID'] = msg.id
			self.bot.CM.save()
		else:
			await ctx.channel.send("You do not have the required permissions to do this.")
	

	#region-----------CASE SPECIFIC---------------

	@commands.command(brief="sets the security of a case", usage='security [open | strict]')
	async def security(self, ctx, level):
		levels = ["open", "strict"]
		case, perms, manager = await self.case_command_info(ctx)
		if manager:
			if level in levels:
				lastLevel = case['security']
				case['security'] = level
				await ctx.channel.send(f"`{lastLevel}` -> `{level}`")
				self.bot.CM.save()
			else:
				slevels = ""
				for x in levels: slevels += f"`{x}`,"
				await ctx.channel.send("Invallid security level. Must be one of the following: " + slevels[:-1])
		else:
			await ctx.channel.send("You do not have the required permissions to do this.")


	@commands.command(brief="joins a case (if the case is open)", usage='join [case ID]')
	async def join(self, ctx, caseID):
		if self.bot.has_permission(ctx.author):
			if caseID in self.bot.CM.cases:
				case = self.bot.CM.cases[caseID]
				if case['status'] == "Open":
					if case['security'] == "open":
						await self._add_to_case(ctx, case, ctx.author.id)
						self.bot.CM.save()
					else:
						await ctx.channel.send("Case security is strict, you cannot add yourself to this case.")
				else:
					await ctx.channel.send("Case is no longer open.")
			else:
				await ctx.channel.send("Case does not exist!")
		else:
			await ctx.channel.send("You do not have permission to join cases.")

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
	@commands.command(brief="transfers case responsibility to another user", usage='transfer [@new_manager]')
	async def transfer(self, ctx, target):
		target = int(target.split("!")[1].replace(">", ""))
		case, perms, manager = await self.case_command_info(ctx)
		if not manager:
			await ctx.channel.send("You cannot do this.")
		else:
			#targetMember = await self.bot.server.fetch_member(target)
			#print('aaaaa', targetMember.roles)
			if True:# or self.bot.has_permission(targetMember, perm='use'):
				case['manager'] = target
				if target not in case['members']:
					case['members'].append(target)
					email = self.get_email(target)
					if "@" in email:
						self.bot.drive.share(case['id'], email)
					else:
						await ctx.channel.send("Note: the new manager does not have an email.")
				await ctx.channel.send("Manager updated.")
				self.bot.CM.save()
				await self.update_case_info(case)
			else:
				await ctx.channel.send("This target member does not have the right permissions to have ownership of a case.")
	
	@commands.command(brief="closes a case")
	async def close(self, ctx):
		case, perms, manager = await self.case_command_info(ctx)
		if not manager:
			await ctx.channel.send("You cannot close this case.")
		else:
			archiveCategory = await self.bot.fetch_channel(self.bot.CM.data['server']['archiveCategoryID'])
			self.bot.CM.close_case(case)
			await ctx.channel.send("Case closed.")
			await ctx.channel.edit(category=archiveCategory)
			await self.update_case_info(case)
			self.bot.CM.save()
	@commands.command(brief="opens a case back up")
	async def reopen(self, ctx):
		case, perms, manager = await self.case_command_info(ctx)
		if not manager:
			await ctx.channel.send("You cannot close this case.")
		else:
			casesCategory = await self.bot.fetch_channel(self.bot.CM.data['server']['caseCategoryID'])
			case['status'] = "Open"
			await ctx.channel.send("Case reopened.")
			await ctx.channel.edit(category=casesCategory)
			await self.update_case_info(case)
			self.bot.CM.save()
		
	@commands.command(brief="adds a member to a case", usage='add [@member]')
	async def add(self, ctx, member):
		case, perms, manager = await self.case_command_info(ctx)
		if not manager:
			await ctx.channel.send("You cannot add people to this case because you are not a manager.")
		else:
			memberID = int(member.split("!")[1].replace(">", ""))
			await self._add_to_case(ctx, case, memberID)
			
	
	async def _add_to_case(self, ctx, case, memberID):
		member = await self.bot.fetch_user(memberID)
		if memberID not in case['members']:
			case['members'].append(memberID)
			if "@" in self.get_email(memberID):
				self.bot.drive.share(case['driveID'], self.get_email(memberID))
			else:
				await ctx.channel.send("Note: This user does not have an email set, so they won't have Google Drive access.")
			await ctx.channel.send(f"Added {member.name} to the case.")
			await self.update_case_info(case)
			self.bot.CM.save()
		else:
			await ctx.channel.send(f"This member is already added to this case. Use `{self.bot.config['prefix']}remove` to remove them.")
		
	@commands.command(brief="removes a member from a case", usage='remove [@member]')
	async def remove(self, ctx, memberID):
		case, perms, manager = await self.case_command_info(ctx)
		if not manager:
			await ctx.channel.send("You cannot remove people from this case because you are not a manager.")
		else:
			memberID = int(memberID.split("!")[1].replace(">", ""))
			member = await self.bot.fetch_user(memberID)
			if memberID in case['members']:
				case['members'].remove(memberID)
				await ctx.channel.send(f"Removed {member.name} from the case.")
				#now find their email perms
				email = self.get_email(memberID)
				if email != "":
					self.bot.drive.unshare(case['driveID'], email)
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
		colors = {"Open": 0x00ff00, "Closed": 0xff0000}
		color = discord.Color.blue
		if case['status'] in colors: color = colors[case['status']]
		embed = discord.Embed(title=case['name'], description=f"""
		Opened by {mention(case['creator'])} on {case['created'].strftime('%m/%d%/%Y, at %H:%M')} {self.bot.config['timezone']}
		""",
		color=color
		)
		embed.add_field(name="Status", value=case['status'])
		embed.add_field(name="Manager", value=mention(case['manager']))
		members = ""
		for x in case['members']:
			members += mention(x) + "\n"
		members = members[:-1] #get rid of the last comma
		embed.add_field(name="Members", value=members)
		embed.add_field(name="Security", value=case['security'])
		if case['status'] == "Closed":
			embed.add_field(name="Closed",value= f"{case['created'].strftime('%m/%d%/%Y, at %H:%M')} {self.bot.config['timezone']}")
		if self.bot.config['gdrive']:
			embed.add_field(name="Google Drive", value=case['url'], inline=False)
		return embed
	#endregion
	def get_email(self, userID):
		if str(userID) in self.bot.CM.data['server']['members']:
			return self.bot.CM.data['server']['members'][str(userID)]['email']
		return ""


def pluralize(word, value, plural=None):
	if plural == None: plural = word + "s"
	if value == 1: return word
	return plural