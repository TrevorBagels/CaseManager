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
from difflib import SequenceMatcher

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
		await self.Divisions.restore_missing_roles_and_channels()
		if self.Dashboard.loop_started == False:
			self.Dashboard.loop_started = True
			self.Dashboard.update_dashboard.start() #start the dashboard update loop
		#await self.restore_missing_channels() #in case anything was removed.

	def similar(self, a, b) -> bool:
		return SequenceMatcher(None, a.lower(), b.lower()).ratio() > .5	
	def similarity(self, a, b) -> float:
		a = str(a).lower()
		b = str(b).lower()
		if len(a) > len(b):
			a = a[:len(b)]
		elif len(b) > len(a):
			b = b[:len(a)]
		return SequenceMatcher(None, a.lower(), b.lower()).ratio()
		
	async def first_init(self):
		await super().first_init()
		await self.Dashboard.create_dashboard()
		