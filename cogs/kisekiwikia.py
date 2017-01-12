import discord
from discord.ext import commands
import aiohttp
import asyncio
import urllib.parse
import re

find_whitespace = re.compile("\\s")

class KisekiWikia:
    """Command to view Kiseki Wikia pages."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def wiki(self, *, search_terms : str):
        """Kiseki Wiki search"""

        if '#' in search_terms:
            parts = search_terms.split('#', 1)
            search_terms = parts[0].strip()
            section = parts[1].strip()
            section = self._norm_sect(section.replace('_', ' '))
        else:
            search_terms = search_terms.strip()
            section = None

        search_terms = search_terms.replace('_', ' ').split(' ')

        url_term = urllib.parse.quote(' '.join(search_terms))
        headers = {'User-Agent': 'MegamiBot/1.0 RedDiscordBot/1.0'}
        base_url = 'https://kiseki.wikia.com/wiki/'
        url = 'https://kiseki.wikia.com/api.php?action=query&titles={}&prop=revisions&rvprop=content&format=json&redirects=1'.format(url_term)
        #try:
        result = None
        async with aiohttp.get(url, headers=headers) as r:
            result = await r.json()
        #await self.bot.say('```\r\n{}```'.format(r))
        #await self.bot.say('The response was malformed:\r\n```json\r\n{}```'.format(result))
        #return
        if not result is None and 'query' in result:
            page_name = search_terms
            old_page_name = None
            if 'normalized' in result['query']:
                if len(result['query']['normalized']) > 0:
                    if 'to' in result['query']['normalized'][0]:
                        page_name = result['query']['normalized'][0]['to']
            if 'redirects' in result['query']:
                if len(result['query']['redirects']) > 0:
                    if 'from' in result['query']['redirects'][0]:
                        old_page_name = result['query']['redirects'][0]['from']
                    if 'to' in result['query']['redirects'][0]:
                        page_name = result['query']['redirects'][0]['to']
            if 'pages' in result['query']:
                #await self.bot.say('```\r\n{}```'.format(result['query']['pages']))
                for key, value in result['query']['pages'].items():
                    if 'title' in value:
                        page_name = value['title']
                    page_url = base_url + urllib.parse.quote(page_name.replace(' ', '_'))
                    if section and len(section) > 0:
                        section_name = ' \u2192 {}'.format(section)
                        section_url = '#{}'.format(section.replace(' ', '_'))
                    else:
                        section_name = ''
                        section_url = ''
                    if 'missing' in value:
                        await self.bot.say('"{}{}" is not a page on Kiseki Wikia.'.format(page_name, section_name))
                        return
                    if 'revisions' in value:
                        for rev in value['revisions']:
                            if '*' in rev:
                                if not old_page_name is None:
                                    redirected = '\n*Redirected from "{}".*'.format(old_page_name)
                                else:
                                    redirected = ''
                                page_content, infobox_data = self._parse_content(rev['*'].replace('\r', ''), section)
                                await self.bot.say('**__{}__{}** (<{}{}>):{}\n\n{}'.format(page_name, section_name, page_url, section_url, redirected, page_content))
                                return

        await self.bot.say('The response was malformed:\r\n```json\r\n{}```'.format(result))
        #except Exception as ex:
        #    await self.bot.say('Error: {}'.format(ex))
    
    def _norm_sect(self, sect):
        return urllib.parse.unquote(sect.replace('_', ' ').replace('.', '%'))

    def _parse_content(self, page_content, section = None):
        global find_whitespace

        # replace wiki format with markdown format (by going to HTML)
        rwf_data = [
                {'find': "'''''", 'replace': '***'},
                {'find': "'''", 'replace': '**'},
                {'find': "''", 'replace': '*'},
                #{'find': '[[', 'replace': '__'},
                #{'find': ']]', 'replace': '__'},
                #{'find': '[', 'replace': '__'},
                #{'find': ']', 'replace': '__'}
                ]


        for rwf in rwf_data:
            page_content = page_content.replace(rwf['find'], rwf['replace'])

        # find header for section
        lines = page_content.split('\n')
        header_sect_content = ''
        sect_content = ''
        current_section = None
        section_found = False
        for line in lines:
            # section header
            linet = line.strip()
            header_number = 0
            while len(linet) > 2 and linet[0] == '=' and linet[-1] == '=':
                linet = linet[1:-1]
                header_number += 1
                if header_number == 6:
                    break
            if header_number > 0:
                current_section = linet.strip(' ')
                if not section is None and self._norm_sect(current_section.lower()) == self._norm_sect(section.lower()):
                    section_found = True
                    section = current_section
                continue

            if current_section is None:
                header_sect_content += line + '\n'
            elif not section is None and not current_section is None and current_section == section:
                sect_content += line + '\n'

        page_content = header_sect_content
        if not section is None and len(section) > 0:
            if section_found:
                page_content = '{}__{}__\n{}'.format(page_content, section, sect_content)
            else:
                page_content += '*No section called "{}".*'.format(section)

        templ_level = 0
        templ_start_pos = 0
        is_start_brace = False
        is_end_brace = False
        is_pipe = False
        cut_point = 0
        prev_cut_point = 0
        pos = 0
        for char in page_content:
            # skip tables and templates!
            if char == '|':
                if is_start_brace: # seq '{|'
                    if templ_level == 1:
                        templ_start_pos = pos - 1
                    is_start_brace = False
                is_pipe = True

            if char == '{':
                if is_start_brace: # seq '{{'
                    templ_level += 1
                    if templ_level == 1:
                        templ_start_pos = pos - 1
                is_start_brace = not is_start_brace
            else:
                is_start_brace = False
            
            if char == '}':
                if is_end_brace or is_pipe: # seq '}}' or '|}'
                    templ_level -= 1
                    if templ_level == 0:
                        templ_end_pos = pos
                        page_content = page_content[:templ_start_pos] + page_content[templ_end_pos + 1:]
                        pos = templ_start_pos - 1
                    if templ_level < 0:
                        templ_level = 0
                is_end_brace = not is_end_brace
            else:
                is_end_brace = False

            if char != '|':
                is_pipe = False

            # set "cut" points
            if char == ' ' or char == '\n' or char == '\t' or char == '-':
                cut_point = pos

            # find plain links (FOR DISCORD)
            if char == 'h':
                content_part = page_content[pos:]
                if content_part.lower().startswith('http://') or content_part.lower().startswith('https://'):
                    matchobj = find_whitespace.search(content_part)
                    if matchobj:
                        lookahead_endurl = matchobj.start()
                        page_content = page_content[:pos] + '<' + content_part[:lookahead_endurl] + '>' + content_part[lookahead_endurl:]
                    else:
                        page_content = page_content[:pos] + '<' + content_part + '>'
                    pos += 2

            pos += 1

            # cut here; no more looping
            if cut_point > 1500:
                if prev_cut_point < 1000:
                    page_content = page_content[:1500] + '...'
                else:
                    page_content = page_content[:prev_cut_point + 1] + '...'
                break
            else:
                prev_cut_point = cut_point

       ## strip html tags: format/keep content
       #sht_data = [
       #        {'tag': 'b', 'format': ['**','**']},
       #        {'tag': 'strong', 'format': ['**','**']},
       #        {'tag': 'i', 'format': ['*','*']},
       #        {'tag': 'em', 'format': ['*','*']},
       #        {'tag': 'u'},
       #        {'tag': 'p', 'format': ['\n', '']},
       #        {'tag': 'br', 'format': ['\n','']},
       #        {'tag': 'span'},
       #        {'tag': 'font'},
       #        {'tag': 'table', 'remove': True},
       #        {'tag': 'table', 'remove': True},
       #        {'tag': 'table', 'remove': True},
       #        {'tag': 'table', 'remove': True},
       #        {'tag': 'mainpage-leftcolumn-start', 'remove': True},
       #        {'tag': 'mainpage-rightcolumn-start', 'remove': True},
       #        {'tag': 'mainpage-endcolumn', 'remove': True},
       #        {'tag': 'rss', 'remove': True},
       #        ]

       #count = 0
       #pos = 0
       #for sht in sht_data:
       #    while '<' + sht['tag'] in page_content:
       #        tag_start_pos = page_content.find('<' + sht['tag'], pos)
       #        content_start_pos = page_content.find('>', tag_start_pos)
       #        if page_content[content_start_pos - 1] == '/': # self-closed
       #            content = ''
       #            tag_end_pos = content_start_pos
       #            tag_end_length = 1
       #        else:
       #            tag_end_pos = page_content.find('</' + sht['tag'] + '>', content_start_pos)
       #            tag_end_length = len(sht['tag']) + 3
       #            content = page_content[content_start_pos + 1:tag_end_pos]
       #        if 'remove' in sht and sht['remove']:
       #            content = ''
       #        if 'format' in sht:
       #            if len(sht['format']) > 0:
       #                content = sht['format'][0] + content
       #            if len(sht['format']) > 1:
       #                content = content + sht['format'][1]
       #        page_content = page_content[:tag_start_pos] + content + page_content[tag_end_pos + tag_end_length:]
       #        pos = tag_start_pos
       #        count += 1
       #        if count == 1000:
       #            return page_content, None

        return page_content, None


def setup(bot):
    n = KisekiWikia(bot)
    bot.add_cog(n)
