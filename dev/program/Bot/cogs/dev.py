import math
import os, time, random, sys, discord, JSON4JSON, datetime
from discord.ext import commands
from discord.ext.commands.core import command
from discord.utils import get
import discord
from ...Core import data as d


class Dev(commands.Cog):
	data:	d.SaveData
	def __init__(self, bot):
		self.bot = bot
	
	@commands.command(brief='destroys everything')
	async def poof(self, ctx):
		g :discord.Guild = self.bot.guild
		for x in await g.fetch_channels():
			await x.delete()
		for x in await g.fetch_roles():
			if x.permissions.administrator == False and x.id != g.id:
				try:
					await x.delete()
				except:
					continue
		newchannel = await g.create_text_channel("General")
		self.bot.data = d.SaveData()
		self.bot.save()
		self.bot.load_data()
		await newchannel.send("everything just went boom. you're welcome.")


Module = Dev