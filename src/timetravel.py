from discord.ext import commands
from datetime import date, time, datetime
import pytz
import sqlite3
import geopy.geocoders
from timezonefinder import TimezoneFinder
import re


def parse_time(time_string: str) -> tuple[int, int]:
    """Parses a string representing a time, which can be in 12-hour or 24-hour format, into a tuple of hours and
    minutes.
    :param time_string: A string representing a time. It can have between one and four digits, followed by an optional
    AM or PM. It can have any number of whitespaces.
    :return: A tuple of two numbers, the first one representing the hour (24-hour format) and the minute.
    """

    # Get rid of all whitespace and set to lowercase
    time_string = ''.join(time_string.split()).lower()

    # Build a match with a regex for the required format, separated in groups
    match = re.fullmatch('^([0-9]{1,2}?)([0-9]{0,2})([ap]m)?$', time_string)

    # Check if the string matches the required format
    if not match:
        raise ValueError("This time isn't valid")

    hour, minute = match.group(1, 2)
    am_or_pm = match.group(3)

    if hour > 23:
        raise ValueError("Hour is above 23")

    if minute > 59:
        raise ValueError("Minute is above 59")

    if hour > 12:
        return hour, minute
    if hour == 12:
        return hour + (12 if am_or_pm == 'am' else 0), minute
    if hour < 12:
        return hour + (12 if am_or_pm == 'pm' else 0), minute


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
            hours, minutes = parse_time(time_str)
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
