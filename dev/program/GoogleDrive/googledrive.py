from pydrive.drive import GoogleDrive
from pydrive.auth import GoogleAuth
import os


class GDrive:
	def __init__(self, bot):
		self.bot = bot
		self.gauth = GoogleAuth()
		self.drive : GoogleDrive = None
		if self.bot.config['gdrive']:
			self.authenticate()
	
	def authenticate(self):
		self.gauth.LoadCredentialsFile("./credentials.txt")
		if self.gauth.credentials == None:
			self.gauth.CommandLineAuth()
		elif self.gauth.access_token_expired:
			self.gauth.Refresh()
		else:
			self.gauth.Authorize()
		
		self.gauth.SaveCredentialsFile("./credentials.txt")
		
		self.drive = GoogleDrive(self.gauth)
		print("Google drive initiated.")

	def new_folder(self, name):
		body = {'title': name, "mimeType": "application/vnd.google-apps.folder", "parents": [{"id": self.bot.config.parent_folder_id}]}
		f = self.drive.CreateFile(body)
		f.Upload()
		values = list(f.values())
		link = values[7]
		id = values[4]
		f = None
		return {'url': link, 'id': id}
	def share(self, id, email, access='writer'):
		"""access = writer | owner | reader
		"""
		f = self.drive.CreateFile({"id": id})
		permission = {"type": "user", "role": access, "value": email}
		permName = f.InsertPermission(permission)['name']
		print(f"added {access} permission to {id} for {email}")
		f = None
		return permName
	
	def unshare(self, id, email):
		f = self.drive.CreateFile({"id": id})
		permIDs = []
		for p in f.GetPermissions():
			if email.lower() == p['emailAddress'].lower():
				permIDs.append(p['id'])
		for id in permIDs:
			try:
				f.DeletePermission(id)
				print(f"unshared with {email}")
			except:
				print("Failed to delete perm")
		
		



