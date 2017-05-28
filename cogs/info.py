
import discord
from discord.ext import commands
from cogs.utils.chat_formatting import display_interval, escape_mass_mentions

class Info:
    """Display information about the server."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, no_pm=True)
    async def userinfo(self, ctx, *, text = None):
        """Shows information about this user on this server."""
        def fetch_joined_at(server, user):
            """Just a special case for someone special :^)"""
            if user.id == "96130341705637888" and server.id == "133049272517001216":
                return datetime.datetime(2016, 1, 10, 6, 8, 4, 443000)
            else:
                return user.joined_at

        def fetch_past_names(bot, server, user):
            mod = bot.get_cog("Mod")
            if not mod is None:
                names = mod.past_names[user.id] if user.id in mod.past_names else []
                try:
                    nicks = mod.past_nicknames[server.id][user.id]
                except:
                    nicks = []
                names = [escape_mass_mentions(name) for name in names]
                nicks = [escape_mass_mentions(nick) for nick in nicks]
                return names, nicks
            else:
                return [], []

        def to_bool(val):
            if val:
                return 'Yes'
            else:
                return 'No'

        author = ctx.message.author
        server = ctx.message.server

        if len(ctx.message.mentions) > 0:
            user = ctx.message.mentions[0]
        else:
            if not text:
                user = author
            else:
                user = server.get_member_named(text)

        if not user:
            await self.bot.say("{} User not found on this server: `{}`".format(author.mention, text))
            return

        roles = [x.name for x in user.roles if x.name != "@everyone"]

        names, nicks = fetch_past_names(self.bot, server, user)

        joined_at_value = fetch_joined_at(server, user)
        since_joined = (ctx.message.timestamp - joined_at_value).total_seconds()
        joined_at = ("{}\n({} ago)".format(
                joined_at_value.strftime("%d %b %Y %H:%M"),
                display_interval(since_joined, 2)))

        created_at_value = user.created_at
        since_created = (ctx.message.timestamp - created_at_value).total_seconds()
        created_at = ("{}\n({} ago)".format(
                created_at_value.strftime("%d %b %Y %H:%M"),
                display_interval(since_created, 2)))

        sorted_members = sorted(server.members, key=lambda m: m.joined_at)
        member_number = sorted_members.index(user) + 1
        before_text = ''
        if member_number > 1:
            before_text = str(sorted_members[member_number - 2]) + ' > '
        after_text = ''
        if member_number < len(sorted_members):
            after_text = ' > ' + str(sorted_members[member_number])

        game = "Chilling in {} status".format(user.status)

        if user.game is None:
            pass
        elif user.game.url is None:
            game = "Playing {}".format(user.game)
        else:
            game = "Streaming: [{}]({})".format(user.game, user.game.url)

        if roles:
            roles = sorted(roles, key=[x.name for x in server.role_hierarchy
                                       if x.name != "@everyone"].index)
            roles = '{}: {}'.format(len(roles), ', '.join(roles))

        data = discord.Embed(description=game, colour=user.colour)
        data.add_field(name="Joined Discord on", value=created_at)
        data.add_field(name="Joined this server on", value=joined_at)
        if roles:
            data.add_field(name="Roles", value=roles, inline=False)
        if len(names) > 0:
            data.add_field(name="Past usernames", value='{}: {}'.format(len(names), ', '.join(names)), inline=False)
        if len(nicks) > 0:
            data.add_field(name="Past nicknames", value='{}: {}'.format(len(nicks), ', '.join(nicks)), inline=False)
        if server.owner == user:
            data.add_field(name="Is owner?", value=to_bool(True))
        data.add_field(name="Member position", value='{}: {}**{}**{}'.format(member_number, before_text, user, after_text), inline=False)
        data.set_footer(text="Requested by {} | User ID: {}".format(author, user.id))

        if user.avatar_url:
            name = str(user)
            name = " ~ ".join((name, user.nick)) if user.nick else name
            data.set_author(name=name, url=user.avatar_url)
            data.set_thumbnail(url=user.avatar_url)
        else:
            data.set_author(name=user.name)

        try:
            await self.bot.say(embed=data)
        except discord.HTTPException:
            await self.bot.say("I need the `Embed links` permission "
                               "to send this")

    @commands.command(pass_context=True, no_pm=True)
    async def serverinfo(self, ctx):
        """Shows information about this server."""
        def can_everyone_view(server, channel):
            overwrites = channel.overwrites_for(server.default_role)
            return overwrites.read_messages != False

        def to_bool(val):
            if val:
                return 'Yes'
            else:
                return 'No'

        server = ctx.message.server
        online = len([m.status for m in server.members
                      if m.status != discord.Status.offline])
        total_users = len(server.members)
        text_channels = len([x for x in server.channels
                             if x.type == discord.ChannelType.text and
                             can_everyone_view(server, x)])
        voice_channels = len([x for x in server.channels
                             if x.type == discord.ChannelType.voice])
        passed = (ctx.message.timestamp - server.created_at).total_seconds()
        created_at = ("Since {}. That's {} ago!".format(
                server.created_at.strftime("%d %b %Y %H:%M"),
                display_interval(passed, 2)))

        verif_level_text = 'Unknown'
        if   server.verification_level == discord.VerificationLevel.none:
            verif_level_text = 'None'
        elif server.verification_level == discord.VerificationLevel.low:
            verif_level_text = 'Low'
        elif server.verification_level == discord.VerificationLevel.medium:
            verif_level_text = 'Medium'
        elif server.verification_level == discord.VerificationLevel.high:
            verif_level_text = '(╯°□°）╯︵ ┻━┻'

        emoji_text = ''.join([str(x) for x in server.emojis])

        data = discord.Embed(
            description=created_at,
            colour=discord.Colour(value=0x2c2f33))
        data.add_field(name="Region", value=str(server.region))
        data.add_field(name="Users", value="{}/{}".format(online, total_users))
        data.add_field(name="Emoji", value="{}/{}".format(len(server.emojis), 50))
        data.add_field(name="Roles", value=len(server.roles))
        data.add_field(name="Text Channels", value=text_channels)
        data.add_field(name="Voice Channels", value=voice_channels)
        data.add_field(name="Owner", value=str(server.owner))
        data.add_field(name="Is large?", value=to_bool(server.large))
        if server.unavailable:
            data.add_field(name="Is unavailable?", value=to_bool(server.unavailable))
        data.add_field(name="Verification Level", value=verif_level_text)
        data.set_footer(text="Requested by {} | Server ID: {}".format(ctx.message.author, server.id))

        if server.icon_url:
            data.set_author(name=server.name, url=server.icon_url)
            data.set_thumbnail(url=server.icon_url)
        else:
            data.set_author(name=server.name)

        try:
            await self.bot.say(embed=data)
        except discord.HTTPException as ex:
            await self.bot.say("I need the `Embed links` permission "
                               "to send this")

    @commands.command(pass_context=True, no_pm=True)
    async def roleinfo(self, ctx, *, text = None):
        """Shows information about this role on this server."""
        def to_bool(val):
            if val:
                return 'Yes'
            else:
                return 'No'

        author = ctx.message.author
        server = ctx.message.server

        if len(ctx.message.role_mentions) > 0:
            role = ctx.message.role_mentions[0]
        else:
            if not text:
                roles_without_everyone = [x for x in author.roles if not x.is_everyone]
                if len(roles_without_everyone) == 1:
                    role = roles_without_everyone[0]
                elif len(roles_without_everyone) == 0: 
                    await self.bot.say("{} You have no roles. Request `.roleinfo` with a role name specified.".format( \
                            author.mention))
                    return
                else:
                    await self.bot.say("{} You have {} roles: {} Request `.roleinfo` with a role name specified.".format( \
                            author.mention, \
                            len(roles_without_everyone), \
                            ', '.join([escape_mass_mentions(str(x)) for x in roles_without_everyone])))
                    return
            else:
                role = None
                for r in server.role_hierarchy:
                    if text == str(r):
                        role = r
                        break

        if not role:
            await self.bot.say("{} Role not found on this server: `{}`".format(author.mention, text))
            return

        sorted_roles = server.role_hierarchy
        users_with_role = [x for x in server.members if role in x.roles]
        role_permissions = [key for key, val in role.permissions if val]
        role_permissions_neg = [key for key, val in role.permissions if not val]
        role_permissions_count = len(role_permissions)
        if len(role_permissions_neg) < len(role_permissions):
            role_permissions = [('-' + x) for x in role_permissions_neg]
            if len(role_permissions) == 0:
                role_permissions = ['ALL']
            else:
                role_permissions[0] = 'ALL ' + role_permissions[0]
        else:
            if len(role_permissions) == 0:
                role_permissions = ['NONE']

        role_number = sorted_roles.index(role) + 1
        before_text = ''
        if role_number > 1:
            before_text = str(sorted_roles[role_number - 2]) + ' > '
        after_text = ''
        if role_number < len(sorted_roles):
            after_text = ' > ' + str(sorted_roles[role_number])
        passed = (ctx.message.timestamp - role.created_at).total_seconds()
        created_at = ("Since {}. That's {} ago!".format(
                role.created_at.strftime("%d %b %Y %H:%M"),
                display_interval(passed, 2)))
        data = discord.Embed(description=created_at, colour=role.colour)
        data.add_field(name="Displayed separately?", value=to_bool(role.hoist))
        data.add_field(name="Mentionable?", value=to_bool(role.mentionable))
        if role.is_everyone:
            data.add_field(name="Is @everyone?", value=to_bool(role.is_everyone))
        if role.managed:
            data.add_field(name="Managed by Integration?", value=to_bool(role.managed))
        data.add_field(name="Members", value="{}".format(len(users_with_role)), inline=False)
        data.add_field(name="Permissions", value="{}: {}".format(role_permissions_count, ", ".join(role_permissions)), inline=False)
        data.add_field(name="Role position", value='{}: {}**{}**{}'.format(role_number, \
                escape_mass_mentions(before_text), \
                escape_mass_mentions(role.name), \
                escape_mass_mentions(after_text)), inline=False)
        data.set_footer(text="Requested by {} | Role ID: {}".format(ctx.message.author, role.id))

        data.set_author(name=role.name)

        try:
            await self.bot.say(embed=data)
        except discord.HTTPException as ex:
            await self.bot.say("I need the `Embed links` permission "
                               "to send this")

    @commands.command(pass_context=True, no_pm=True, aliases=['emoji', 'emojis'])
    async def emojiinfo(self, ctx):
        """Shows information about the emoji on this server."""
        server = ctx.message.server

        emoji_cats = [
                {'name': 'Falcom', 'entries': ['MeeHee']},
                {'name': 'Gurumin', 'entries': ['ParinDisgust']},
                {'name': 'Xanadu Next', 'entries': ['BraveKnight', 'InventoryChar']},
                {'name': 'Brandish', 'entries': []},
                {'name': 'Zwei!!', 'entries': ['PipiroConfident']},
                {'name': 'Ys', 'entries': ['AdolDistressed', 'AdolAmerica', 'AdolCelceta', 'AdolSparkles', 'ParoParrot', 'CalilicaTaunt', 'FriedaWink', 'KarnaSigh', 'LeezaDistant', 'OzmaAnger', 'DurenLaugh', 'AishaSlap', 'DogiWallCrushing', 'GeisStunned', 'LiliaOffering', 'TiaSurprise', 'PikkardArmy', 'DanaLacrimosa']},
                {'name': 'Trails in the Sky', 'entries': ['DukeDizzy', 'ScheraSing', 'CampanellaBow', 'KevinWink', 'EinLaugh', 'ErikaStars', 'EstelleGlare', 'EstelleSmug', 'OlivierLoveSeeker', 'TitaSigh', 'PhantomThiefBeauty', 'GilbertBlorf', 'DaddyDisappointed', 'CapuaDelivery', 'SiegScree', 'PrincessJoshua', 'RenneSmug', 'OsBro', 'AnelaceSweets', 'Estdull', 'AnelaceCute', 'RiesNom', 'CapuaReady']},
                {'name': 'Trails to Zero/Azure', 'entries': []},
                {'name': 'Trails of Cold Steel', 'entries': ['ReanHalt', 'FieGlare', 'JusisShrug', 'MachiasRage', 'MilliumLetsGo', 'TowaSmile', 'OsBro', 'AbsolutelyDuNot', 'LauraConfused']},
                {'name': 'Akatsuki no Kiseki', 'entries': ['NachtEdge', 'ChloeExcited', 'LifSmug']},
                ]

        emoji_text = ''.join([str(x) for x in server.emojis])

        data = discord.Embed(
            description='Emoji List',
            colour=discord.Colour(value=0x2c2f33))

        uncat_cat = {'name': 'Uncategorized', 'entries': []}
        for emoji in server.emojis:
            uncat = True
            for emoji_cat in emoji_cats:
                if emoji.name in emoji_cat['entries']:
                    uncat = False
                    break
            if uncat:
                uncat_cat['entries'].append(emoji.name)

        if len(uncat_cat['entries']):
            emoji_cats.append(uncat_cat)

        for emoji_cat in emoji_cats:
            emoji_cat['objs'] = []
            for emoji in server.emojis:
                if emoji.name in emoji_cat['entries']:
                    emoji_cat['objs'].append(emoji)
            if len(emoji_cat['objs']):
                data.add_field(name=emoji_cat['name'], value=''.join([str(x) for x in emoji_cat['objs']]))

        data.set_footer(text="Requested by {}".format(ctx.message.author))

        if server.icon_url:
            data.set_author(name=server.name, url=server.icon_url)
            data.set_thumbnail(url=server.icon_url)
        else:
            data.set_author(name=server.name)

        try:
            await self.bot.say(embed=data)
        except discord.HTTPException as ex:
            await self.bot.say("I need the `Embed links` permission "
                               "to send this")

def setup(bot):
    bot.add_cog(Info(bot))
