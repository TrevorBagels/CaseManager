import os, json, datetime
from bson import json_util
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive



class CaseManager:
	def __init__(self, config):
		self.config = config
		self.data = {"cases": {}, "server": {}}
		self.firstTime = False
		self.version = 1.2
		try:
			with open(self.config['dataFile'], 'r') as f:
				self.data = json.loads(f.read(), object_hook=json_util.object_hook)
			print(self._version_update())
		except:
			self.data['server'] = {
				'serverID': 0, #ID of the server
				'caseCategoryID': 0, #ID of the category in which cases are placed in
				'roles': {
					#'fullAccessExample': 'manage'
				},
				"members": {},#keeps track of member data (like emails for google drive sharing). each key is the str() of their ID
				"version": self.version,
				"divisions": {},
				"dashboard": {}
				}
			self.firstTime = True
		self.cases = self.data['cases']

	def _version_update(self):
		if self.version == self.data['server']['version']:
			return "Up to date"
		self.data['server']['version'] = self.version
		self.save()
		return "Updated"

	def save(self):
		with open(self.config['dataFile'], 'w+') as f:
			f.write(json.dumps(self.data, default=json_util.default, indent=4))
	
	def close_case(self, case):
		case['closed'] = datetime.datetime.now(datetime.timezone.utc)
		case['status'] = "Closed"
	def get_division(self, name):
		for x in self.data['server']['divisions']:
			if self.data['server']['divisions'][x]['name'] == name:
				return self.data['server']['divisions'][x]
		return None
	def create_case(self, name, creator):
		case = {}
		case['created'] = datetime.datetime.now(datetime.timezone.utc)
		case['opened'] = datetime.datetime.now(datetime.timezone.utc)
		case['name'] = name #name of the case
		case['creator'] = creator
		case['manager'] = creator #ID of the creator
		case['members'] = [creator] #people with access to the case
		case['status'] = "Open"
		case['divisions'] = [] #list of division names
		case['notes'] = ""
		#TODO security not implemented yet 
		case['security'] = 'strict' #levels are 0=none (anyone can do anything to the case, including closing it. not implemented), 1=open (anyone can access the case and it's channel) 2=strict (you must be added by the case manager to participate) 3=private (not visible to people other than case managers and active participants)
		case['id'] = f"{str(case['created'].year)[2:]}{formatNumber(case['created'].month, 2)}{formatNumber(case['created'].day, 2)}-{str(creator)[:3]}{str(len(self.cases))}"
		self.data['cases'][case['id']] = case
		return case
	def create_division(self, name, description, roleID):
		div = {}
		div['name'] = name
		div['desc'] = description
		div['id'] = roleID
		div['members'] = []
		div['leaders'] = []
		self.data['server']['divisions'][str(roleID)] = div
		return div
def formatNumber(num, zeros):
	newNum = ""
	for x in range(0, zeros-len(str(num))):
		newNum += "0"
	return newNum + str(num)

