# CaseManager
A discord bot for creating/managing cases


## Installation

1. Download the repository (`git clone https://github.com/TrevorBagels/CaseManager.git`)
2. Navigate to the directory (`cd CaseManager`)
3. Install dependencies (`pip3 install -r requirements.txt`)
4. Create a bot
  1. Go to the [discord developer portal](https://discord.com/developers/applications)
  2. Click "Create a New Application"
  3. Go to the bot tab, click "Add Bot"
  4. Go to the "OAuth2" tab, click the "bot" checkbox
  5. Give the bot as many permissions as you want, make sure to enable all of the text permissions, and things related to role/channel management. Hit administrator if you're willing to take that risk.
  6. Copy the link that shows up above "BOT PERMISSIONS" and go to it. Use this to add it to your server.
  7. Copy the bot's token (Bot tab -> "TOKEN" area -> click "Copy"
5. Configure
  1. In the directory for the repository, create a new file called "config.json". Make the content of that file look like this:
  ```
  {
    "token": "ODE5Mjk2OTI0Nzk5NzI5NzQ1.YEkjuA.VyZaIT9TkTlv2xids-XpnMrHU7A",
    "gdrive": true,
    "parentFolderID": "id_goes_here"
  }
  ```
  2. Replace the long string with the token you copied. 
6. Set up google drive
  1. Go to the [google developer console](https://console.cloud.google.com/apis/dashboard)
  2. Create a project, call it whatever you want
  3. Click enable APIs and services after you wait a long time for stuff to load
  4. Search for "google drive api", click "google drive api"
  5. Click enable, wait forever for more stuff to load
  6. Click "credentials" (on the left sidebar), if it tries to take you to a credentials wizard, click it again
  7. Click "CREATE CREDENTIALS" (near the top left), select the OAuth one, then click "configure consent screen" when it asks you to do that.
  8. Select external, go to the next page
  9. Fill out all the required fields, go to the next page
  10. Skip the scopes page
  11. Add your email as a test user, hit "save and continue"
  12. **Go back to the credentials tab**
  13. Click create credentials, OAuth client ID
  14. Set application type to desktop app
  15. Save and continue
  16. Click the download button when you're taken back to the credentials tab. Save the file as `client_secrets.json` in the path of the repository.
7. Create a folder in google drive. Call it something like "Cases". Navigate to that folder, and copy it's ID. You can get the ID from the link to the folder, it usually looks like this: `https://drive.google.com/drive/u/7/folders/`**`reallyLongFileID`**. Go back to `config.json` and set the `parentFolderID` property to the ID you just copied.
## Usage

**Great, now run the bot** ``python3 bot.py``

When running, go to the link that is prompted, and sign into the google account you're using with the Google Drive API. It'll tell you to copy a code and paste it into the console. Do that, press enter, and the bot should work now.

When the bot first starts up, you won't have any permissions to do anything with it. Give yourself the "case manager role" that is automatically generated when initializing the bot for the first time. This will give you full access to the bot. You can add permissions to other roles using `?perm @role [permission]`. Valid permissions are: `none`, `use`, `create`, and `manage`. `use` gives access to the basic usage of the bot. `create` lets people with the role create cases with `?create [case name]`. `manage` is the highest permission, it lets people manage everything related to the bot.

#### Setting your email for google drive
Use `?setemail [email_address]` to set your email address. Cases that you are a part of will automatically share their folders with you.
