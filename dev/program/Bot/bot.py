import os, time, random, sys, discord, JSON4JSON, traceback, json, importlib
from discord.ext import commands
from discord.ext.commands.core import command
from discord.utils import get
from ..Core import data as d
from bson import json_util
from . import botguts
from .cogs.casecmds import Cases
from .cogs.main import Main
from .cogs.divisions import Divisions
from .cogs.dashboard import Dashboard


class CaseBot(botguts.CaseBotSpine):
	def __init__(self):
		super().__init__()
		if self.config.dev:
			self.Dev = self.add_module("dev") #This is for testing purposes only, using this makes the bot extremely 
			# insecure, and allows anyone to use ?poof and make the bot nuke the server (only channels and roles)
		self.Main:Main = self.add_module("main")
		self.Cases:Cases = self.add_module("casecmds")
		self.Divisions:Divisions = self.add_module("divisions")
		self.Dashboard:Dashboard = self.add_module("dashboard")

	async def on_ready(self):
		await super().on_ready()
		await self.Dashboard.get_dashboard_channels()
		if self.Dashboard.loop_started == False:
			self.Dashboard.loop_started = True
			self.Dashboard.update_dashboard.start() #start the dashboard update loop
		#await self.restore_missing_channels() #in case anything was removed.
		
	
	async def first_init(self):
		await super().first_init()
		await self.Dashboard.create_dashboard()
		