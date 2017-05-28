# Project Gurumin Spoilers

import sys
import os
import discord
from datetime import datetime
from discord.ext import commands
from .utils.dataIO import dataIO
from PIL import Image, ImageDraw, ImageFont, ImageSequence

class Spoilers:
    """Provides "GIF spoiler" commands. These generate a GIF of the hidden text that can be viewed on hover."""

    def __init__(self, bot):
        self.draw_font = ImageFont.truetype('NotoSansCJKjp-Regular.otf', 14)
        self.history = dataIO.load_json("data/spoilers/splog.json")
        self.bot = bot

    @commands.command(pass_context=True, aliases=['sp', 'hidetext', 'spoilers', 'ht'])
    async def spoiler(self, ctx, *, args):
        """Hide the given text, image, or  behind a GIF spoiler.
        
        The first word is the "spoiler context" and will be shown at all times, for example:
        
        `.spoiler NieR hidden text` will hide only the "hidden text" part.
        
        Use quotation marks around the "spoiler context" to use more than one word."""

        message = ctx.message
        if len(args) == 0 or (not ' ' in args and not '"' in args and not "'" in args):
            await self.bot.say('{} Error: No message provided. You must provide a "context" as the first word (you may quote it for multiple words).'.format(message.author.mention))
        else:
            s_context, s_hidden = self._parse_args(args)

            if len(s_hidden) == 0:
                await self.bot.say('{} Error: No message provided. You must provide a "context" as the first word (you may quote it for multiple words) and the text to be "hidden" as the rest.'.format(message.author.mention))
            else:
                await self.bot.delete_message(message)
                await self.bot.send_typing(message.channel)
                history = self._gen_history(ctx, s_context, s_hidden)
                text_hash = self._text_hash(s_hidden)
                file_name = 'data/spoilers/spoiler_{}.gif'.format(text_hash)
                success, cache_hit, w, h, ex = self._generate_gif(['Hover mouse to view hidden text.', s_hidden], width=300, bg=(54,57,62), fg=(255,255,255), pad=10, loop=None, file_name=file_name)
                if not success:
                    await self.bot.say('{} Error: GIF generation exception `{}`'.format(message.author.mention, str(ex)))
                else:
                    #await self.bot.say('```\r\nContext: {}\r\nHidden: {}\r\nHash: {}\r\nPath: {}\r\nW: {} H: {}```'.format(s_context, s_hidden, text_hash, file_name, w, h))
                    await self.bot.send_file(message.channel, file_name, content='Context: **{1}**  Message author: {0}  *[hidden message: hover or open to view]*'.format(message.author.mention, s_context))
                self._save_history(history, text_hash, file_name, success, cache_hit, w, h, ex)

    def _gen_history(self, ctx, s_context, s_hidden):
        channel = ctx.message.channel
        author = ctx.message.author
        server = ctx.message.server
        if not server.id in self.history:
            self.history[server.id] = {}
        if not channel.id in self.history[server.id]:
            self.history[server.id][channel.id] = []

        return {
                "server"    : server.id,
                "channel"   : channel.id,
                "author"    : author.id,
                "req_time"  : datetime.utcnow().timestamp(),
                "context"   : s_context,
                "hidden"    : s_hidden
                }
    def _save_history(self, history, text_hash, file_name, success, cache_hit, w, h, ex):
        history["hash"]     = text_hash
        history["file"]     = file_name
        history["rsp_time"] = datetime.utcnow().timestamp()
        history["success"]  = success
        if success:
            history["cache_hit"]  = cache_hit
            history["im_width"]  = w
            history["im_height"]  = h
        else:
            history["exception"] = str(ex)

        server_id = history["server"]
        channel_id = history["channel"]
        self.history[server_id][channel_id].append(history)
        dataIO.save_json("data/spoilers/splog.json", self.history)

    def _parse_args(self, allargs):
        """Parses a message into "Context" and "Hidden" parts."""
        args = allargs.split(' ')
        if args[0].startswith('"'):
            s_context_ender = '"'
        elif args[0].startswith("'"):
            s_context_ender = "'"
        else:
            s_context_ender = None

        # start with context = first word
        s_context = args[0]
        s_hidden = ''

        if not s_context_ender is None:
            # if a context_ender is detected, check if the first word "ends" the context too
            s_context1 = s_context[1:]
            s_end_pos = s_context1.find(s_context_ender)
            if s_end_pos >= 0:
                s_context = s_context1[:s_end_pos]
                s_hidden1 = s_context1[(s_end_pos + 1):]
                if len(s_hidden1) > 0:
                    s_hidden = s_hidden1
                s_context_ender = None
            else:
                s_context = args[0][1:]
        
        # go through each word and look for a context_ender (until ending, in which case just construct s_hidden)
        # if no context_ender or already ended, just construct s_hidden
        for i in range(1, len(args)):
            s_word = args[i]
            if not s_context_ender is None:
                s_end_pos = s_word.find(s_context_ender)
                if s_end_pos >= 0:
                    s_context += ' ' + s_word[:s_end_pos]
                    s_hidden1 = s_word[(s_end_pos + 1):]
                    if len(s_hidden1) > 0:
                        s_hidden = s_hidden1
                    s_context_ender = None
                else:
                    s_context += ' ' + s_word
            else:
                if len(s_hidden) == 0:
                    s_hidden = s_word
                else:
                    s_hidden += ' ' + s_word

        # handle .spoiler "Context Hidden Hidden Hidden
        # (unended context quote: handle as first word is context, keep quotes to show the user the error)
        if len(s_hidden) == 0:
            s_context = args[0]
            s_hidden = ' '.join(args[1:])

        return s_context, s_hidden.strip()

    def _generate_gif(self, strings, width=300, bg=(0,0,0), pad=0, fg=(255,255,255), loop=None, duration=[10,10], file_name='data/spoilers/spoiler.gif'):
        try:
            if os.path.exists(file_name):
                return True, True, 0, 0, None

            canvas = Image.new('RGB', (640,300), bg)
            #print(canvas.mode)                 # P
            #print(len(canvas.palette.palette)) # RGB
            #print(canvas.palette.rawmode)      # 768
            #canvas = canvas.convert('RGB')
            max_w = width
            max_h = -1
            for index in range(0, len(strings)):
                draw = ImageDraw.Draw(canvas)
                w, h, wr_string = self._measure_wrap_text(strings[index], draw, font=self.draw_font, spacing=0, width=max_w)
                strings[index] = wr_string
                if h > max_h:
                    max_h = h
            max_w += pad * 2
            max_h += pad * 2
            canvas.close()

            frames = []
            for index in range(0, len(strings)):
                canvas = Image.new('RGB', (max_w, max_h), bg)
                draw = ImageDraw.Draw(canvas)
                draw.rectangle([(0,0), (max_w,max_h)], fill=bg)
                draw.text((pad, pad), strings[index], font=self.draw_font, fill=fg)
                frames.append(canvas.convert('P', dither=Image.NONE, palette=Image.ADAPTIVE, colors=256))
            if loop:
                frames[0].save(file_name, save_all=True, loop=loop, duration=duration, append_images=frames[1:])
            else:
                frames[0].save(file_name, save_all=True, append_images=frames[1:])
        except Exception as ex:
            return False, False, 0, 0, ex

        return True, False, max_w, max_h, None

    def _measure_wrap_text(self, string, draw, font=None, spacing=0, width=480):
        if draw is None:
            return 0, 0
        spc_w, h = draw.multiline_textsize(' ', font=font, spacing=0)
        
        wr_string = ''
        tot_h = 0
        for line in string.split('\n'):
            tot_w = 0
            for word in line.split(' '):
                w, h = draw.multiline_textsize(word, font=font, spacing=0)
                if w + tot_w > width:
                    if tot_w == 0:
                        # word was longer than canvas; commit word (draw will go off end)
                        wr_string += word + '\n'
                        tot_h += h + 4
                        tot_w = 0
                    else:
                        # commit word after soft wrap
                        wr_string += '\n' + word
                        tot_h += h + 4
                        tot_w = w
                elif tot_w == 0:
                    # commit first word in line
                    wr_string += word
                    tot_w += w + spc_w
                else:
                    # commit word
                    wr_string += ' ' + word
                    tot_w += w + spc_w
            # hard wrap
            wr_string += '\n'
            tot_h += h + 4
        return tot_w, tot_h + h, wr_string

    def _text_hash(self, text):
        h = hash(text.rstrip())
        if h < 0:
            h += sys.maxsize + 1
        return hex(h).lstrip('0x').zfill(16)

def check_folders():
    folders = ("data", "data/spoilers/")
    for folder in folders:
        if not os.path.exists(folder):
            print("Creating " + folder + " folder...")
            os.makedirs(folder)

def check_files():
    files = {
            "splog.json" : {}
    }

    for filename, value in files.items():
        if not os.path.isfile("data/spoilers/{}".format(filename)):
            print("Creating empty {}".format(filename))
            dataIO.save_json("data/spoilers/{}".format(filename), value)

def setup(bot):
    check_folders()
    check_files()
    bot.add_cog(Spoilers(bot))

