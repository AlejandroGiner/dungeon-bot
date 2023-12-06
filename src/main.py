#!/usr/bin/env python3
import discord
import asyncio
from discord.ext import commands
from datetime import datetime

bot = commands.Bot('?', intents=discord.Intents.all())


@bot.command(name="load", hidden=True)
@commands.is_owner()
async def load_cog(ctx, *, cog: str):
    try:
        await bot.load_extension(cog)
    except (commands.ExtensionAlreadyLoaded, commands.ExtensionNotFound, commands.NoEntryPointError,
            commands.ExtensionFailed) as e:
        # await ctx.send(f"**`ERROR:`**{type(e).__name__} - {e}")
        await bot.reload_extension(cog)
    finally:
        await ctx.send("**`SUCCESS`**")


@bot.command(name="unload", hidden=True)
@commands.is_owner()
async def unload_cog(ctx, *, cog: str):
    try:
        await bot.unload_extension('cogs.' + cog)
    except (commands.ExtensionNotLoaded, commands.ExtensionNotFound) as e:
        await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
    else:
        await ctx.send('**`SUCCESS`**')

@bot.command(name='sync',hidden=True)
@commands.is_owner()
async def sync_commands(ctx):
    await bot.tree.sync(guild=ctx.guild)
    await ctx.send("Slash commands synced!")

@bot.command(name='syncglobal',hidden=True)
@commands.is_owner()
async def sync_commands_global(ctx):
    await bot.tree.sync()
    await ctx.send("Slash commands synced!")


@bot.event
async def on_ready():
    print(f'Logged in as: {bot.user.name} - {bot.user.id}')
    print(f'discord.py version: {discord.__version__}')
    print(f'at {datetime.now().strftime("%H:%M:%S")}')
    await bot.change_presence(activity=discord.Game(name='Joe'))
    print(f'Successfully logged in and booted.')

    for extension in ['timetravel', 'poll']:
        await bot.load_extension(extension)


async def main():
    with open('../token.txt') as f:
        token = f.read()
    await bot.start(token)

asyncio.run(main())
