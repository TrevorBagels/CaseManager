from pydrive.drive import GoogleDrive
from pydrive.auth import GoogleAuth
import os


class GDrive:
	def __init__(self, bot):
		self.bot = bot
		self.gauth = GoogleAuth()
		self.gauth.CommandLineAuth()
		self.drive = GoogleDrive(self.gauth)
	
	def new_folder(self, name):
		body = {'title': name, "mimeType": "application/vnd.google-apps.folder", "parents": [{"id": self.bot.config['parentFolderID']}]}
		f = self.drive.CreateFile(body)
		f.Upload()
		values = list(f.values())
		link = values[7]
		id = values[4]
		f = None
		return {'url': link, 'id': id}
	def share(self, id, email, access='writer'):
		#writer, owner, reader
		f = self.drive.CreateFile({"id": id})
		permission = {"type": "user", "role": access, "value": email}
		permName = f.InsertPermission(permission)['name']
		print(f"added {access} permission to {id} for {email}")
		f = None
		return permName

'''

'''