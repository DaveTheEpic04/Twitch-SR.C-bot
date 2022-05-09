This twitch bot is hosted through heroku and is ran on the twitch account SRdotCbot.

The three main sections of the bot comprise of the Speedrun.com side, the Twitch side and the Amazon S3 side.
  SrcSide handles getting information about the runs being requested
  TwitchSide handles accessing the Twitch IRC and sending messages
  S3Side handles getting the file containing details on twitch channels and their associated speedrun.com accounts
  
S3Side is required for heroku due to the use of an ephimeral file system, meaning all files are reset.
As new channels need to be able to join during runtime, the file needs to be stored somewhere else.

If you want to use this code yourself, the required config variables are:
  AWS_ACCESS_KEY_ID:      An access key given by Amazon S3, required for S3Side
  AWS_SECRET_ACCESS_KEY:  A secret access key given by Amazon S3, required for S3Side
  BOT_NAME:               The name of the account that the bot will use to send messages, required for TwitchSide
  CLIENT_ID:              An ID from Twitch Developers, required for SrcSide
  OAUTH:                  An authorization code required to send messages through the IRC, required for TwitchSide
  S3_BUCKET_NAME:         The name of the bucket that Streamers.json is being stored in, required for S3Side
  SECRET_ID:              A secret ID from Twitch Developers, required for ScSide
