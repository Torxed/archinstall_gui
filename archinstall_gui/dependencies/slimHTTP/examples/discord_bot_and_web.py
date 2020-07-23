import slimHTTP
import discord

import aiohttp, asyncio, json
import urllib.parse
import urllib.request


DISCORD_TOKEN = 'AverYlOng.TokeN.fROm:' # https://discord.com/developers/applications/<your application>/bot

bot_info = {
	'server_name' : 'slimHTTP',
	'_guild_obj' : None,
	'_members' : {},
	'_roles' : {},
	'_channels' : {}
}

class slimHTTP_Bot(discord.Client):
	async def on_ready(self):
		print(f'{client.user} has connected.')
		# Iterate members, roles and channels in the server 'server_name'
		# Cache those results for usage later.
		for guild in client.guilds:
			if guild.name == bot_info['server_name']:
				bot_info['_guild_obj'] = guild

				for member in guild.members:
					bot_info['_members'][member.id] = member

				for role in bot_info['_guild_obj'].roles:
					bot_info['_roles'][role.id] = role

				for channel in guild.channels:
					bot_info['_channels'][channel.name] = channel

	async def on_member_join(self, member):
		# Keep updating members.
		bot_info['_members'][member.id] = member

	async def on_message(self, message):
		# If a message is recieved, and it's for a server (guild)
		# Check if the user is requesting a !link and if so, supply a link.

		if message.guild:# and message.channel.name == 'help':
			if message.content == '!link':
				print(f'Sending GitHub link: {message.author.name}')
				github_link = f"https://github.com/Torxed/slimHTTP"

				github_link_message = discord.Embed(title="GitHub repo link!",
												type="rich",
												description="Here's the link to the official GitHub repo for slimHTTP.", url=github_link)
				await message.delete() # Delete the !link message
				await message.author.send(embed=github_link_message)

# Create a async friendly functions that can be called
# as a task with asyncio.create_task() from a *non*-asyncio function/class.
async def send_message(target, message):
	await target.send(embed=message)

# Lets set up the webserver on port 80
# (port needs to be given before @http.configuration hook because it's used at startup)
http = slimHTTP.host(slimHTTP.HTTP, port=80, web_root='./web_root', index='index.html')

# And add a route to /repo/index.html
# We can then set up a GitHub webhook to it, which will update the discord channel each commit.
@http.route('/repo/index.html')
def repo_change(request):
	repo_info = json.loads(request.request_payload.decode('UTF-8'))

	prev_commit_id = repo_info['before']
	new_commit_id = repo_info['after']

	sender = repo_info['sender']['login']
	avatar = repo_info['sender']['avatar_url'] # or 'gravatar_id'

	to_announcement_channel = 'general'
	if 'announcements' in repo_info['_channels']:
		to_announcement_channel = 'announcements'

	head_commit_url = repo_info['head_commit']['url']
	commit_message = repo_info['head_commit']['message']
	commit_message = discord.Embed(title="A new commit has been submitted!",
									type="rich",
									description=commit_message, url=head_commit_url)
	client.loop.create_task(send_message(repo_info['_channels'][to_announcement_channel], commit_message))

# Create the slimHTTP main loop to poll the events
# We create it in a async function so we can use it with create_task()
async def loop_http():
	while 1:
		for event, *event_data in http.poll():
			pass
		await asyncio.sleep(0.25)

# Set up the discord bot, and use it's main asyncio thread
# to spawn a sub-task with our slimHTTP main loop.
client = slimHTTP_Bot()
client.loop.create_task(loop_http())
client.run(DISCORD_TOKEN)

