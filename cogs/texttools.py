# some Unicode tools

import unicodedata
import discord
import codecs
from discord.ext import commands
from .utils.chat_formatting import escape_mass_mentions
from random import choice

class TextTools:
    """Commands to do with modifying the given text."""
    def __init__(self, bot):
        self.bot = bot
        
        self._widemap = dict((i, i + 0xFF00 - 0x20) for i in range(0x21, 0x7F))
        self._widemap[0x20] = 0x3000 # IDEOGRAPHIC SPACE

        # table flip src: http://www.fileformat.info/convert/text/upside-down-map.htm
        self._flipmap = dict()
        self._flipmap[0x0021] = 0x00A1
        self._flipmap[0x0022] = 0x201E
        self._flipmap[0x0026] = 0x214B
        self._flipmap[0x0027] = 0x002C
        self._flipmap[0x0028] = 0x0029
        self._flipmap[0x002E] = 0x02D9
        self._flipmap[0x0033] = 0x0190
        self._flipmap[0x0034] = 0x152D
        self._flipmap[0x0036] = 0x0039
        self._flipmap[0x0037] = 0x2C62
        self._flipmap[0x003B] = 0x061B
        self._flipmap[0x003C] = 0x003E
        self._flipmap[0x003F] = 0x00BF
        self._flipmap[0x0041] = 0x2200
        self._flipmap[0x0042] = 0x10412
        self._flipmap[0x0043] = 0x2183
        self._flipmap[0x0044] = 0x25D6
        self._flipmap[0x0045] = 0x018E
        self._flipmap[0x0046] = 0x2132
        self._flipmap[0x0047] = 0x2141
        self._flipmap[0x004A] = 0x017F
        self._flipmap[0x004B] = 0x22CA
        self._flipmap[0x004C] = 0x2142
        self._flipmap[0x004D] = 0x0057
        self._flipmap[0x004E] = 0x1D0E
        self._flipmap[0x0050] = 0x0500
        self._flipmap[0x0051] = 0x038C
        self._flipmap[0x0052] = 0x1D1A
        self._flipmap[0x0054] = 0x22A5
        self._flipmap[0x0055] = 0x2229
        self._flipmap[0x0056] = 0x1D27
        self._flipmap[0x0059] = 0x2144
        self._flipmap[0x005B] = 0x005D
        self._flipmap[0x005F] = 0x203E
        self._flipmap[0x0061] = 0x0250
        self._flipmap[0x0062] = 0x0071
        self._flipmap[0x0063] = 0x0254
        self._flipmap[0x0064] = 0x0070
        self._flipmap[0x0065] = 0x01DD
        self._flipmap[0x0066] = 0x025F
        self._flipmap[0x0067] = 0x0183
        self._flipmap[0x0068] = 0x0265
        self._flipmap[0x0069] = 0x0131
        self._flipmap[0x006A] = 0x027E
        self._flipmap[0x006B] = 0x029E
        self._flipmap[0x006C] = 0x0283
        self._flipmap[0x006D] = 0x026F
        self._flipmap[0x006E] = 0x0075
        self._flipmap[0x0072] = 0x0279
        self._flipmap[0x0074] = 0x0287a
        for k, v in list(self._flipmap.items()):
            self._flipmap[v] = k

    @commands.command(hidden=True)
    async def ping(self):
        """Pong."""
        await self.bot.say("Pong.")

    @commands.command(pass_context=True)
    async def flip(self, ctx, *, text):
        """Flips a coin... or text/mention.

        Defaults to coin.
        """
        author = ctx.message.author
        server = ctx.message.server
        if text != None and len(text) > 0:
            if len(ctx.message.mentions) > 0:
                member = ctx.message.mentions[0]
            elif len(ctx.message.channel_mentions) > 0:
                channel = ctx.message.channel_mentions[0]
                text = '#' + channel.name
                member = None
            elif len(ctx.message.role_mentions) > 0:
                role = ctx.message.role_mentions[0]
                text = role.name
                member = None
            else:
                member = server.get_member_named(text)
            msg = ""
            if member != None:
                if member.id == self.bot.user.id:
                    member = ctx.message.author
                    msg = "Nice try. You think this is funny? How about *this* instead:\n\n"
                text = member.display_name
            new_text = text.translate(self._flipmap)[::-1]
            await self.bot.say("{}{} (╯°□°）╯︵ {}".format(author.mention, msg, escape_mass_mentions(new_text)))
        else:
            author = ctx.message.author
            await self.bot.say('{} I Choose: ***{}***'.format(author.mention, choice('HEADS', 'TAILS')))

    @commands.command(pass_context=True, aliases=['aesthetic'])
    async def fullwidth(self, ctx, *, arg):
        """Converts narrow characters to wide characters."""

        author = ctx.message.author
        result = arg.translate(self._widemap)
        await self.bot.say('{}: {}'.format(author.mention, escape_mass_mentions(result)))

    @commands.command(pass_context=True)
    async def uninormalize(self, ctx, form, *, arg):
        """Normalizes the given Unicode. 'NFC', 'NFD', 'NFKC', and 'NFKD' are the forms."""

        author = ctx.message.author
        if form != 'NFC' and form != 'NFD' and form != 'NFKC' and form != 'NFKD':
            await self.bot.say('{} Normalization form not supported: `{a}`\nSupported forms: `NFC`, `NFD`, `NFKC`, `NFKD`.'.format(author.mention, form))
        else:
            s = unicodedata.normalize(form, arg)
            await self.bot.say('{} Normalized: {}'.format(author.mention, escape_mass_mentions(s)))

    @commands.command(pass_context=True)
    async def unicode(self, ctx, *, arg):
        """Returns the information on a Unicode character or named character."""

        author = ctx.message.author
        if len(arg) == 1:
            char = arg
        else:
            # try to find what character is meant
            # if starts with "U+", it's hex
            if arg.upper().startswith('U+'):
                arg = '0x' + arg[2:].strip()
            try:
                if arg.lower().startswith('0x'):
                    arg = arg[2:]
                char = chr(int(arg, 16))
            except ValueError:
                # otherwise, use name lookup
                try:
                    char = unicodedata.lookup(arg)
                except KeyError:
                    await self.bot.say("{} Character not found: `{}`".format(author.mention, arg))
                    return
        
        value = ord(char)
        name = unicodedata.name(char, None) # str or None
        decimal = unicodedata.decimal(char, None) # int or None
        digit = unicodedata.digit(char, None) # int or None
        numeric = unicodedata.numeric(char, None) # float or None
        category = unicodedata.category(char) # str
        bidirectional = unicodedata.bidirectional(char) # str
        combining = unicodedata.combining(char) # str
        east_asian_width = unicodedata.east_asian_width(char) # str
        mirrored = unicodedata.mirrored(char) # int
        decomposition = unicodedata.decomposition(char) # str

        table  = '{} About Unicode U+{:04X}:'.format(author.mention, value)
        table += '```\nCharacter:        {}'.format(char)
        if not name is None:
            table += '\nName:             {}'.format(name)
        if not decimal is None:
            table += '\nDecimal:          {}'.format(decimal)
        if not digit is None:
            table += '\nDigit:            {}'.format(digit)
        if not numeric is None:
            table += '\nNumeric:          {}'.format(numeric)
        table += '\nCategory:         {}'.format(category)
        if len(bidirectional) > 0:
            table += '\nBidirectional:    {}'.format(bidirectional)
        if combining != 0:
            table += '\nCombining class:  {}'.format(combining)
        table += '\nEast Asian width: {}'.format(east_asian_width)
        if mirrored != 0:
            table += '\nMirrored:         {}'.format(mirrored)
        if len(decomposition) > 0:
            table += '\nDecomposition:    {}'.format(decomposition)
        table += '```'

        await self.bot.say(table)

    @commands.command(pass_context=True)
    async def rot13(self, ctx, *, text):
        """Returns the ROT13 of the given text."""

        author = ctx.message.author
        result = codecs.encode(text, "rot_13")
        await self.bot.say('{}: {}'.format(author.mention, escape_mass_mentions(result)))

    @commands.command(pass_context=True, aliases=["shout"])
    async def upper(self, ctx, *, text):
        """Returns the uppercase of the given text."""

        author = ctx.message.author
        result = text.upper()
        await self.bot.say('{}: {}'.format(author.mention, escape_mass_mentions(result)))

    @commands.command(pass_context=True)
    async def lower(self, ctx, *, text):
        """Returns the lowercase of the given text."""

        author = ctx.message.author
        result = text.lower()
        await self.bot.say('{}: {}'.format(author.mention, escape_mass_mentions(result)))

    @commands.command(pass_context=True)
    async def expand(self, ctx, *, text):
        """Returns a spaced out version of the given text."""

        author = ctx.message.author
        result = ' '.join([c for c in text])
        await self.bot.say('{}: {}'.format(author.mention, escape_mass_mentions(result)))

    @commands.command(pass_context=True)
    async def echo(self, ctx, *, text):
        """Returns the given text."""

        author = ctx.message.author
        result = text
        await self.bot.say('{}: {}'.format(author.mention, escape_mass_mentions(result)))

    @commands.command(pass_context=True)
    async def reverse(self, ctx, *, text):
        """Returns the reverse-order of the given text."""

        author = ctx.message.author
        result = text[::-1]
        await self.bot.say('{}: {}'.format(author.mention, escape_mass_mentions(result)))

    @commands.command(pass_context=True)
    async def base64(self, ctx, *, text):
        """Returns the reverse-order of the given text."""

        author = ctx.message.author
        result = text[::-1]
        await self.bot.say('{}: {}'.format(author.mention, escape_mass_mentions(result)))

    @commands.command(pass_context=True)
    async def hex2str(self, ctx, *, text):
        """Converts the given hex bytes to a string assuming UTF-8."""

        author = ctx.message.author
        result = codecs.decode(text.replace(' ', ''), 'hex')
        resultx = result.decode('utf-8')
        await self.bot.say('{}: {}'.format(author.mention, escape_mass_mentions(resultx)))

    @commands.command(pass_context=True)
    async def hex2strx(self, ctx, encoding, *, text):
        """Converts the given hex bytes to a string given an encoding."""

        author = ctx.message.author
        result = codecs.decode(text.replace(' ', ''), 'hex')
        resultx = result.decode(encoding)
        await self.bot.say('{}: {}'.format(author.mention, escape_mass_mentions(resultx)))


def setup(bot):
    bot.add_cog(TextTools(bot))

