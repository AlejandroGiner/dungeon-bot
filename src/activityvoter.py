import discord
from discord.ext import commands
from discord.ui import Button, View, Select

import sqlite3


def getCategoryID(cat, cur):
	cur.execute('SELECT categoryID FROM category WHERE name=?', (cat,))
	result = cur.fetchone()
	if not result:
		return None
	return result[0]


def getActivity(cat, act, cur, *, full = False):
	category_id = getCategoryID(cat, cur)
	cur.execute('SELECT * FROM activity a JOIN category c ON(a.categoryID=c.categoryID) WHERE a.name=? AND c.categoryID=?',(act, category_id))
	result = cur.fetchone()
	if not result:
		return None
	if full:
		return result
	return result[0]


class ListView(View):
	def __init__(self, cursor):
		super().__init__()
		self.page = 0
		self.cursor = cursor

	@discord.ui.button(label="", style=discord.ButtonStyle.secondary, emoji="⬅")
	async def left_button_callback(self, interaction, button):
		if self.page > 0:
			self.page -= 1

		e = await pageEmbedBuilder(self.cursor, self.page)
		await interaction.response.edit_message(embed=e)

	@discord.ui.button(label="", style=discord.ButtonStyle.secondary, emoji="➡")
	async def right_button_callback(self, interaction, button):
		self.page += 1
		e = await pageEmbedBuilder(self.cursor, self.page)
		if len(e.fields) == 0:
			self.page = 0
			e = await pageEmbedBuilder(self.cursor, self.page)
		await interaction.response.edit_message(embed=e)


async def pageEmbedBuilder(cur, page):
	offset_value = page * 25
	cur.execute('SELECT name FROM category LIMIT 25 OFFSET ?', (offset_value,))
	result = cur.fetchall()
	result = [row[0] for row in result]

	e = discord.Embed(color=discord.Color.dark_gold(), title=f'List of All Categories')
	e.set_footer(text=f'Page {page + 1}')
	for category in result:
		e.add_field(name=category, value='')
	return e


class ActivityVoter(commands.Cog):
	db_file = '../activities.db'

	def __init__(self, bot):
		self.bot = bot
		self.conn = sqlite3.connect(self.db_file)
		self.conn.execute('PRAGMA foreign_keys = 1')
		cur = self.conn.cursor()
		cur.execute("""
			CREATE TABLE IF NOT EXISTS category(
				categoryID INTEGER PRIMARY KEY,
				name TEXT
			);
		""")

		cur.execute("""
			CREATE TABLE IF NOT EXISTS activity(
				activityID INTEGER PRIMARY KEY,
				name TEXT,
				categoryID INTEGER,
				dateAdded TEXT,
				authorID INTEGER,
				
				CONSTRAINT activitycolumn
					FOREIGN KEY(categoryID) 
					REFERENCES category(categoryID) 
					ON DELETE SET NULL
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

	@commands.command(name='createCategory')
	async def _createCategory(self, ctx, cat):
		cur = self.conn.cursor()

		if getCategoryID(cat, cur):
			await ctx.send(f'Category "{cat}" already exists!')
			return
		try:
			cur.execute('INSERT INTO category(name) VALUES(?)', (cat,))
			await ctx.send(f'Created category "{cat}"')
			self.conn.commit()
		except Exception as e:
			await ctx.send(f'Error: {e}')

	@commands.command(name='editCategory')
	async def _editCategory(self, ctx, cat, new):
		cur = self.conn.cursor()

		category_id = getCategoryID(cat, cur)
		if not category_id:
			await ctx.send(f'Category "{cat}" does not exist!')
			return

		if getCategoryID(new, cur):
			await ctx.send(f'Category with name "{new}" already exists!')
			return

		try:
			cur.execute('UPDATE category SET name=? WHERE categoryID=?',(new, category_id))
			await ctx.send(f'Changed category name from "{cat}" to "{new}"')
			self.conn.commit()
		except Exception as e:
			await ctx.send(f'Error: {e}')

	@commands.command(name='deleteCategory')
	async def _deleteCategory(self, ctx, cat):
		cur = self.conn.cursor()

		if not getCategoryID(cat, cur):
			await ctx.send(f'Category "{cat}" does not exist!')
			return

		try:
			cur.execute('DELETE FROM category WHERE name=?', (cat,))
			await ctx.send(f'Category "{cat}" has been deleted')
			self.conn.commit()
		except Exception as e:
			await ctx.send(f'Error: {e}')

	@commands.command(name='listCategories')
	async def _listCategories(self, ctx):
		cur = self.conn.cursor()

		embed = await pageEmbedBuilder(cur, 0)

		if not len(embed.fields):
			await ctx.send('No categories exist!')
			return

		view = ListView(cur)

		await ctx.send(embed=embed, view=view)

	@commands.command(name='createActivity')
	async def _createActivity(self, ctx, cat, act):
		cur = self.conn.cursor()

		category_id = getCategoryID(cat, cur)
		if not category_id:
			await ctx.send(f'Category "{cat}" does not exist!')
			return
		if getActivity(cat, act, cur):
			await ctx.send(f'Activity "{act}" already exists!')
			return

		try:
			cur.execute('INSERT INTO activity(name, categoryID, dateAdded, authorID) VALUES(?,?,?,?)', (act, category_id, ctx.message.created_at, ctx.author.id))
			await ctx.send(f'Created activity "{act}" in category "{cat}"')
			self.conn.commit()
		except Exception as e:
			await ctx.send(f'Error: {e}')

	@commands.command(name='editAct')
	async def _editAct(self, ctx, cat, act, new):
		cur = self.conn.cursor()

		category_id = getCategoryID(cat, cur)
		if not category_id:
			await ctx.send(f'Category "{cat}" does not exist!')
			return

		if getActivity(cat, new, cur):
			await ctx.send(f'Activity with name "{act}" in category "{cat}" already exists!')
			return

		try:
			cur.execute("UPDATE activity SET name=? WHERE categoryID=? AND name=?",(new, category_id, act))
			await ctx.send(f'Changed activity name from "{act}" to "{new}"')
			self.conn.commit()
		except Exception as e:
			await ctx.send(f'Error: {e}')

	@commands.command(name='deleteAct')
	async def _deleteAct(self, ctx, cat, act):
		cur = self.conn.cursor()

		category_id = getCategoryID(cat, cur)
		if not category_id:
			await ctx.send(f'Category "{cat}" does not exist!')
			return

		try:
			cur.execute('DELETE FROM activity WHERE categoryID=? AND name=?', (category_id,act))
			self.conn.commit()
		except Exception as e:
			await ctx.send(f'Error: {e}')

	@commands.command(name='listActs')
	async def _listActs(self, ctx, cat):
		cur = self.conn.cursor()

		category_id = getCategoryID(cat, cur)

		if not category_id:
			await ctx.send(f'Category "{cat}" does not exist!')
			return

		cur.execute('SELECT name FROM activity WHERE categoryID=?', (category_id,))

		result = cur.fetchall()
		if not result:
			await ctx.send(f'No activities exist in category "{cat}"')
			return

		e = discord.Embed(color=discord.Color.dark_gold(), title=f'List of activites in category "{cat}"')

		result = [row[0] for row in result]

		for activity in result:
			e.add_field(name=activity, value='✅: 0 ❌: 0')
		await ctx.send(embed=e)

	@commands.command(name='viewAct')
	async def _viewAct(self, ctx, cat, act):
		cur = self.conn.cursor()

		category_id = getCategoryID(cat, cur)
		if not category_id:
			await ctx.send(f'Category "{cat}" does not exist!')
			return

		actTuple = getActivity(cat, act, cur, full=True)
		if actTuple:
			e = discord.Embed(color=discord.Color.dark_gold(), title=f'{act}')
			try:
				cur.execute('SELECT COUNT(*) FROM vote WHERE activityID=? AND value=?', (actTuple[0], 0))
			except Exception as exc:
				await ctx.send(exc)
			poop = cur.fetchone()
			no = poop[0]

			try:
				cur.execute('SELECT COUNT(*) FROM vote WHERE activityID=? AND value=?', (actTuple[0], 1))
			except Exception as exc:
				await ctx.send(exc)
			poop = cur.fetchone()
			yes = poop[0]

			e.add_field(name='', value=f'✅: {yes} ❌: {no}')
			await ctx.send(embed=e)
		else:
			await ctx.send(f'Activity "{act}" does not exist!')
		self.conn.commit()

	@commands.command(name='placeVote')
	async def _placeVote(self, ctx, cat, act, vote: int):
		cur = self.conn.cursor()

		if not getCategoryID(cat, cur):
			await ctx.send(f'Category "{cat}" does not exist!')
			return

		activity_id = getActivity(cat, act, cur)
		if not activity_id:
			await ctx.send(f'Activity "{act}" does not exist!')
			return

		vote = 1 if vote else 0

		try:
			cur.execute('REPLACE INTO vote (value, userID, activityID) VALUES(?,?,?)',(vote, ctx.author.id, activity_id))
			self.conn.commit()
		except Exception as e:
			await ctx.send(f'Error: {e}')

	@commands.command(name='fieldtest', aliases=['f'])
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
