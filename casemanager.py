import os, json, datetime
from bson import json_util
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive



class CaseManager:
	def __init__(self, config):
		self.config = config
		self.data = {"cases": {}, "server": {}}
		self.firstTime = False
		try:
			with open(self.config['dataFile'], 'r') as f:
				self.data = json.loads(f.read(), object_hook=json_util.object_hook)
		except:
			self.data['server'] = {
				'serverID': 0, #ID of the server
				'caseCategoryID': 0, #ID of the category in which cases are placed in
				'roles': {
					#'fullAccessExample': 'manage'
				},
				"members": {}#keeps track of member data (like emails for google drive sharing). each key is the str() of their ID
			}
			self.firstTime = True
		self.cases = self.data['cases']

	def save(self):
		with open(self.config['dataFile'], 'w+') as f:
			f.write(json.dumps(self.data, default=json_util.default, indent=4))
	
	def close_case(self, case):
		case['closed'] = datetime.datetime.now()
		case['status'] = "Closed"

	def create_case(self, name, creator):
		case = {}
		case['created'] = datetime.datetime.now()
		case['name'] = name #name of the case
		case['creator'] = creator
		case['manager'] = creator #ID of the creator
		case['members'] = [creator] #people with access to the case
		case['status'] = "Open"
		case['notes'] = ""
		#TODO security not implemented yet 
		case['security'] = 'strict' #levels are 0=none (anyone can do anything to the case, including closing it. not implemented), 1=open (anyone can access the case and it's channel) 2=strict (you must be added by the case manager to participate) 3=private (not visible to people other than case managers and active participants)
		self.data['cases'][name] = case
		return case


