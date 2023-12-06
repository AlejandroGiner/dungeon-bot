from discord.ext import commands
from datetime import date, time, datetime
import pytz
import sqlite3
import geopy.geocoders
from timezonefinder import TimezoneFinder
import re


def timeparser(time_string):
    time_string = re.sub(r'[\W_]+', '', time_string)

    if not re.match('^[0-9]{1,4}([ap]m)?$', time_string):
        raise ValueError("This time isn't valid")

    num_of_num = sum([c.isdigit() for c in time_string])

    # The hour is either the first number or the first two numbers
    hour = int(time_string[:2]) if num_of_num in (2, 4) else int(time_string[:1])

    if hour > 23:
        raise ValueError("Hour above 23")

    # The minute is either the last two numbers or zero
    minute = int(time_string[num_of_num-2:num_of_num]) if num_of_num in (3, 4) else 0

    if minute > 59:
        raise ValueError("Minute above 59")

    if hour > 12:
        return hour, minute
    if hour == 12:
        return hour + (12 if 'am' in time_string else 0), minute
    if hour < 12:
        return hour + (12 if 'pm' in time_string else 0), minute


def get_time(hours, minutes, tz):
    t = time(hours, minutes)
    d = date.today()
    naive = datetime.combine(d, t)
    aware = pytz.timezone(tz).localize(naive)
    return aware


class TimeTravel(commands.Cog):
    db_file = '../timezones.db'

    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect(self.db_file)
        cur = self.conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS timezones (
                                    user_id TEXT PRIMARY KEY,
                                    timezone TEXT
                                    );              
                """)
        self.conn.commit()

    @commands.command(name='time')
    async def _time(self, ctx, *, time_str, tz_str=None):
        # time_list = list(map(lambda x: int(x), time_str.split(':')))

        try:
            hours, minutes = timeparser(time_str)
        except ValueError:
            await ctx.send(f'Wrong format for time. Time=`{time_str}`')
            return
        hours = hours % 24

        if not tz_str:
            cur = self.conn.cursor()
            cur.execute("SELECT timezone FROM timezones WHERE user_id=?", (ctx.author.id,))
            tz_str = cur.fetchone()[0]

        aware = get_time(hours, minutes, tz_str)

        await ctx.send(f'<t:{int(aware.timestamp())}:t>')

    @commands.command(name='city')
    async def _city(self, ctx, city='Palencia'):
        geolocator = geopy.geocoders.Nominatim(user_agent='timezone_bot')
        location = geolocator.geocode(city)
        tz_finder = TimezoneFinder()
        tz = tz_finder.timezone_at(lng=location.longitude, lat=location.latitude)
        await ctx.send(f'The timezone in {city} is `{tz}`')

    @commands.command(name="timezone", aliases=['set_tz', 'tz'])
    async def _timezone(self, ctx, tz=None):
        print(ctx.author.display_name, tz)
        if not tz:
            cur = self.conn.cursor()
            cur.execute("SELECT timezone FROM timezones WHERE user_id=?", (ctx.author.id,))
            your_tz = cur.fetchone()
            your_tz = your_tz[0] if your_tz else 'not set'
            await ctx.send(f'Your timezone is {your_tz}')
        else:
            cur = self.conn.cursor()
            cur.execute("SELECT timezone FROM timezones WHERE user_id=?", (ctx.author.id,))
            if cur.fetchone():
                cur.execute("UPDATE timezones SET timezone=? WHERE user_id=?", (tz, ctx.author.id))
            else:
                cur.execute("INSERT INTO timezones(user_id,timezone) VALUES(?,?)", (ctx.author.id, tz))
            self.conn.commit()
            await ctx.send(
                f'Your timezone has been set to {tz}. It\'s current time is {get_time(datetime.now().hour, datetime.now().minute, tz).timetz()}')

    @commands.command(name='tzremove')
    async def _tzremove(self, ctx):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM timezones WHERE user_id=?", (ctx.author.id,))
        await ctx.send('Your timezone has been removed')


async def setup(bot):
    await bot.add_cog(TimeTravel(bot))
