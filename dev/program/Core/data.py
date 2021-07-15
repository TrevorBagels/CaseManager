from itertools import product
import discord
from prodict import Prodict
from enum import IntEnum
from datetime import datetime, timezone

class FieldType(IntEnum):
	ANY	= 0
	NUMBER = 1
	INTEGER = 2
	OPTIONS = 3
	MULTIOPTIONS = 4

class Status(IntEnum):
	OPEN = 1
	CLOSED = 0

class Security(IntEnum):
	STRICT 	= 2
	OPEN 	= 1
	NONE 	= 0

class Perm(IntEnum):
	RESTRICTED = -1
	NONE = 0
	VIEW = 1
	USE = 2
	CREATE = 3
	MANAGE = 4

def enum_options(enum) -> list[str]:
	o = []
	for x in dir(enum):
		if x.startswith("_") == False: o.append(x)
	return o

def now() -> datetime:
	return datetime.now().astimezone(timezone.utc)



class Case(Prodict):
	id:				str
	name:			str
	creator:		int #user ID. DO NOT MODIFY
	manager:		int #user ID
	members:		list[int] #User IDs
	status:			Status
	created:		datetime
	opened:			datetime
	closed:			datetime
	divisions:		list[str]
	notes:			str
	security:		Security
	drive_id:		str
	url:			str
	channel:		int
	message:		int
	custom_fields:	dict[str, str] #custom field name, custom field value

	def init(self):
		self.members = []
		self.divisions = []
		self.notes = ""
		self.custom_fields = []
	
	def create(self, creator:discord.User, total_cases):
		self.creator = creator.id
		self.manager = creator.id
		self.members.append(creator.id)
		self.status = Status.OPEN
		self.created = now()
		self.opened = now()
		self.security = Security.STRICT
		d = f"{str(self.created.year)[2:]}" + "%02d"%self.created.month + "%02d"%self.created.day
		i = str(creator.id)[-4:] + "-" + str(total_cases)
		self.id = i + "-" + d
		


	

class User(Prodict):
	id:				int
	email:			str
	logs:			list
	def init(self):
		self.id = 0
		self.email = ""
		self.logs = []

class Channels(Prodict):
	"""The channel and category IDs
	"""
	dashboard:		int
	cases:			int
	archive:		int
	divisions:		int
	dashboard_main:	int #overview message id
	dashboard_cases:int #cases message id

	def init(self):
		self.dashboard = 0
		self.cases = 0
		self.archive = 0
		self.divisions = 0


class Division(Prodict):
	name:			str
	description:	str
	info:			str #longer description
	role_id:		int
	members:		list
	leaders:		list
	channel_id:		int #TODO the channel for this division
	
	def init(self):
		self.description = ""
		self.members = []
		self.leaders = []



class CustomCaseField(Prodict):
	name:			str
	description:	str
	default:		any
	order:			int
	hidden:			bool
	fieldtype:		FieldType 
	options:		list[str]

	def init(self):
		self.fieldtype = FieldType.ANY
		self.order = 0
		self.hidden = False
		self.options = []


class SaveData(Prodict):
	server_id:			int
	cases:				dict[str, Case]
	users:				dict[str, User]
	divisions:			dict[str, Division]
	perms:				dict[str, Perm]
	channels:			Channels
	bot_messages:		dict[str, list[int]]
	custom_case_fields:	dict[str, CustomCaseField]
	
	def init(self):
		self.server_id = 0
		self.cases = {}
		self.users = {}
		self.divisions = {}
		self.perms = {}
		self.channels = Channels()
		self.bot_messages = {}
		self.custom_case_fields = []
	
	def process_user(self, user_id:int):
		if str(user_id) in self.users: return self.users[str(user_id)]
		u = User(id=user_id)
		self.users[str(user_id)] = u
		return u
	
	def get_user(self, id) -> User:
		if str(id) not in self.users:
			self.process_user(id)
		return self.users[str(id)]




class Config(Prodict):
	token:				str
	prefix:				str
	data_file:			str
	gdrive:				bool
	parent_folder_id:	str
	timezone:			str
	dev:				bool


def get(iterable:dict, **attrs):
	if type(iterable) == list:
		k1, v1 = attrs.popitem()
		for x in iterable:
			if x[k1] == v1:
				return x
	if len(attrs) == 1:
		k1, v1 = attrs.popitem()
		for _, v in iterable.items():
			if v[k1] == v1 or ( type(v[k1]) == str and v[k1].startswith(v1) ):
				return v
	return None