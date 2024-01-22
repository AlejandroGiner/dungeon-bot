import discord
from discord.ext import commands


import sqlite3

class ActivityVoter(commands.Cog):
	db_file = '../activities.db'

	def __init__(self, bot):
		self.bot = bot
		self.conn = sqlite3.connect(self.db_file)
		cur = self.conn.cursor()
		cur.execute("""
			CREATE TABLE IF NOT EXISTS activityType(
				activityTypeID INTEGER PRIMARY KEY,
				name TEXT
			);
		""")

		cur.execute("""
			CREATE TABLE IF NOT EXISTS activity(
				activityID INTEGER PRIMARY KEY,
				name TEXT,
				activityTypeID INTEGER,
				dateAdded TEXT,
				authorID INTEGER,
				FOREIGN KEY(activityTypeID) REFERENCES activityType(activityTypeID)
			);
		""")

		cur.execute("""
			CREATE TABLE IF NOT EXISTS vote(
				voteID INTEGER PRIMARY KEY,
				value INTEGER,
				userID TEXT,
				activityID INTEGER,
				UNIQUE(userID, activityID)
			);
		""")

		self.conn.commit()

	@commands.command(name='add')
	async def _add(self, ctx):
		poop = ctx.message.content
		await ctx.send(poop)

	@commands.command(name='insert')
	async def _insert(self, ctx):
		message = ctx.message.content
		#await ctx.send(poopy)
		cur = self.conn.cursor()
		#cur.execute("SELECT * FROM activityType")
		#size = cur.execute("SELECT COUNT(*) FROM activityType")
		cur.execute("INSERT INTO activityType(name) VALUES(?)", (message[7:],))
		self.conn.commit()

	@commands.command(name="fieldtest", aliases=['f'])
	async def _embed(self, ctx):
		e = discord.Embed(color=discord.Color.dark_gold())
		e.set_footer(text='Footer')
		e.set_author(name='Author')
		e.add_field(name='7 Days to Die', value='✅: 5  ❌: 1')
		e.add_field(name='Lethal Company', value='✅: 2  ❌: 3')
		e.add_field(name='Rimworld Multiplayer', value='✅: 2  ❌: 3')
		e.add_field(name='Call to Arms Gates of Hell: Ostfront', value='✅: 2  ❌: 3')
		e.add_field(name='a', value='✅ 2  ❌ 3')
		e.add_field(name='b', value='✅ 2  ❌ 3')
		e.add_field(name='c', value='✅ 2  ❌ 3')
		e.add_field(name='d', value='✅ 2  ❌ 3')
		e.add_field(name='e', value='✅ 2  ❌ 3')
		e.add_field(name='f', value='✅ 2  ❌ 3')

		# e.set_image(url='https://static.wikia.nocookie.net/hunterxhunter/images/c/c2/HxH2011_EP63_Binolt_as_a_child.png/revision/latest?cb=20230518010750')
		await ctx.send(embed=e)


async def setup(bot):
	await bot.add_cog(ActivityVoter(bot))
