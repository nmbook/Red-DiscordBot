
# some Unicode tools

import discord
from discord.ext import commands
from .utils.chat_formatting import escape_mass_mentions
from random import choice, randint
from enum import Enum

class RPS(Enum):
    ROCK     = "\N{MOYAI}"
    PAPER    = "\N{PAGE FACING UP}"
    SCISSORS = "\N{BLACK SCISSORS}"

class RPSChoice:
    def __init__(self, argument):
        for name, member in RPS.__members__.items():
            if argument.upper() == name or argument == member.value:
                self.choice = member.value
                return
        raise

class RandomTools:
    """Commands to do with returning randomized output."""
    def __init__(self, bot):
        self.bot = bot
        self.rps_conditions = {
                (RPS.ROCK,     RPS.PAPER)    : False,
                (RPS.ROCK,     RPS.SCISSORS) : True,
                (RPS.PAPER,    RPS.ROCK)     : True,
                (RPS.PAPER,    RPS.SCISSORS) : False,
                (RPS.SCISSORS, RPS.ROCK)     : False,
                (RPS.SCISSORS, RPS.PAPER)    : True
               }
        self.ball_results = \
                ["As I see it, yes", "It is certain", "It is decidedly so", "Most likely", "Outlook good",
                 "Signs point to yes", "Without a doubt", "Yes", "Yes – definitely", "You may rely on it",
                 "Don't count on it", "My reply is no", "My sources say no", "Outlook not so good", "Very doubtful",
                 "Soon™", "Only if Xanadu Next comes out", "Clearly not truely false", "If you put your mind to it"]
                #"Reply hazy, try again", "Ask again later", "Better not tell you now", "Cannot predict now", "Concentrate and ask again",

    @commands.command(pass_context=True)
    async def choose(self, ctx, *choices):
        """Chooses between multiple choices.

        To denote multiple choices, you should use double quotes.
        """
        author = ctx.message.author
        choices = [escape_mass_mentions(c) for c in choices]
        if len(choices) < 2:
            await self.bot.say('{} Not enough choices to pick from.'.format(author.mention))
        else:
            await self.bot.say('{} I choose: {}'.format(author.mention, choice(choices)))

    @commands.command(pass_context=True)
    async def roll(self, ctx, number : int = 100):
        """Rolls random number (between 1 and user choice)

        Defaults to 100.
        """
        author = ctx.message.author
        if number > 1:
            n = randint(1, number)
            await self.bot.say("{} Between 1 and {}, I choose: {}".format(author.mention, number, n))
        else:
            await self.bot.say("{} Choose a maximum higher than 1.".format(author.mention))

    @commands.command(pass_context=True, name="flipcoin")
    async def _flip(self, ctx):
        """Flips a coin.
        """
        author = ctx.message.author
        await self.bot.say('{} I Choose: ***{}***'.format(author.mention, choice('HEADS', 'TAILS')))

    @commands.command(pass_context=True)
    async def rps(self, ctx, your_choice : RPSChoice):
        """Play rock paper scissors."""
        author = ctx.message.author
        player_choice = your_choice.choice
        red_choice = choice((RPS.rock, RPS.paper, RPS.scissors))

        if red_choice == player_choice:
            outcome = None # Tie
        else:
            outcome = self.rps_conditions[(player_choice, red_choice)]

        if outcome is True:
            await self.bot.say("{1} I chose {0}. You win!".format(red_choice.value, author.mention))
        elif outcome is False:
            await self.bot.say("{1} I chose {0}. You lose!".format(red_choice.value, author.mention))
        else:
            await self.bot.say("{1} I chose {0}. We're square!".format(red_choice.value, author.mention))

    @commands.command(pass_context=True, name="8", aliases=["8ball"])
    async def _8ball(self, ctx, *, question : str):
        """Ask 8 ball a question.
        Question must end with a question mark.
        """
        author = ctx.message.author
        if question.endswith("?") and question != "?":
            await self.bot.say("{} `{}`".format(author.mention, choice(self.ball_results)))
        else:
            await self.bot.say("{} That doesn't look like a question!".format(author.mention))

def setup(bot):
    bot.add_cog(RandomTools(bot))
