import discord
import table2ascii

from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View
import typing


class Poll():
    def __init__(self,name,options,author,channel: discord.TextChannel):
        self.name = name
        self.options = options
        self.author = author
        self.voters = {}
        self.channel = channel
            
    def changeVote(self,option: str,voter_id: int):
        if self.voters.get(voter_id) == option:
            self.voters.pop(voter_id)
        else:
            self.voters.update({voter_id:option})
            
    def getVotes(self,option):
        return list(self.voters.values()).count(option)
            
    def getEmbed(self):
        embed = discord.Embed(title=self.name,color=0x3399ff)
        for i in self.options:
            embed.add_field(name=f"{i}:",value="🗳️"+"🟩"*self.getVotes(i),inline=False)
        return embed.set_footer(text=f'Poll started by {self.author.name}',icon_url=self.author.display_avatar.url)
        
    def getVotesEmbed(self):
        embed = discord.Embed(title=self.name,color=0x3399ff)
        for id in self.voters:
            embed.add_field(name=f"{self.channel.guild.get_member(id)}:",value=f"{self.voters[id]}",inline=False)
        return embed


class OptionButton(Button):
    def __init__(self,option,poll: Poll):
        super().__init__(label=option,style=discord.ButtonStyle.green)
        self.option = option
        self.poll = poll
    async def callback(self,interaction):
        self.poll.changeVote(self.option,interaction.user.id)
        await interaction.response.edit_message(embed=self.poll.getEmbed())

class ShowVotesButton(Button):
    def __init__(self,poll: Poll):
        super().__init__(label='Show votes',style=discord.ButtonStyle.blurple)
        self.poll = poll
    async def callback(self,interaction):
        await interaction.response.send_message(embed=self.poll.getVotesEmbed(),ephemeral=True)

class PollCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.polls = {}
    @app_commands.command(name="poll",description="Start a poll with up to 10 options")
    @app_commands.guilds(1063080970091249664)
    @app_commands.guild_only()
    @app_commands.describe(name='Name of the poll')
    async def startpoll(
            self, interaction: discord.Interaction,
            name: str,option1: str, option2: str,
            option3: typing.Optional[str], option4: typing.Optional[str],
            option5: typing.Optional[str], option6: typing.Optional[str],
            option7: typing.Optional[str], option8: typing.Optional[str],
            option9: typing.Optional[str], option10: typing.Optional[str]):
        options = [x for x in [option1,option2,option3,option4,option5,option6,option7,option8,option9,option10] if x is not None]
        options = [x.strip() for x in options]
        newPoll = Poll(name, options,interaction.user,interaction.channel)
        view = View(timeout=None)
        for i in options:
            view.add_item(OptionButton(i,newPoll))
        view.add_item(ShowVotesButton(newPoll))
        await interaction.response.send_message(embed=newPoll.getEmbed(),view=view)
        msg = await interaction.original_message()
        self.polls.update({msg.id: newPoll})

    @commands.command(name="embed", aliases=['e'])
    async def _embed(self, ctx):
        e = discord.Embed(color=discord.Color.dark_gold())
        e.set_footer(text='im a footer')
        e.set_author(name='im the author')
        #e.add_field(name='Phasmophobia', value='❌: 0  ✅: 100')
        #e.add_field(name='Team Fortress 2', value='❌: 999  ✅: 0')
        #for i in range(3):
        #    e.add_field(name='Hoi4 minecraft', value='❌: 1e69  ✅: -7')
        e.add_field(name='A',value='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',inline=True)
        e.set_image(url='https://cdn.discordapp.com/attachments/1126052272015683625/1181361802148327534/image.png')
        await ctx.send(embed=e)

async def setup(bot):
    await bot.add_cog(PollCog(bot))
