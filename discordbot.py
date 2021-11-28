import asyncio
import discord
from discord.ext import commands
import os
import traceback
import urllib.parse
import re
import emoji
import json
import wikipedia
import pya3rt #A3RTのTalk APIを使用
import requests
import sys #終了時に使用
import datetime

prefix = os.getenv('DISCORD_BOT_PREFIX', default='!')
lang = os.getenv('DISCORD_BOT_LANG', default='ja')
token = os.environ['DISCORD_BOT_TOKEN']
talk_api = os.environ['TALK_API']
bitly_token = os.environ['BITLY_TOKEN']
# text_channel = os.environ['TEXT_CHANNEL']
# voice_channel = os.environ['VOICE_CAHNNEL']

client = commands.Bot(command_prefix=prefix)
with open('emoji_ja.json', encoding='utf-8') as file:
    emoji_dataset = json.load(file)

@client.event
async def on_ready():
    presence = f'{prefix}ヘルプ | 0/{len(client.guilds)}サーバー'
    await client.change_presence(activity=discord.Game(name=presence))

@client.event
async def on_guild_join(guild):
    presence = f'{prefix}ヘルプ | {len(client.voice_clients)}/{len(client.guilds)}サーバー'
    await client.change_presence(activity=discord.Game(name=presence))

@client.event
async def on_guild_remove(guild):
    presence = f'{prefix}ヘルプ | {len(client.voice_clients)}/{len(client.guilds)}サーバー'
    await client.change_presence(activity=discord.Game(name=presence))

@client.command()
async def 接続(ctx):
    if ctx.message.guild:
        if ctx.author.voice is None:
            await ctx.send('ボイスチャンネルに接続してから呼び出してください。')
        else:
            if ctx.guild.voice_client:
                if ctx.author.voice.channel == ctx.guild.voice_client.channel:
                    await ctx.send('接続済みです。')
                else:
                    await ctx.voice_client.disconnect()
                    await asyncio.sleep(0.5)
                    await ctx.author.voice.channel.connect()
            else:
                await ctx.author.voice.channel.connect()

@client.command()
async def 切断(ctx):
    if ctx.message.guild:
        if ctx.voice_client is None:
            await ctx.send('ボイスチャンネルに接続していません。')
        else:
            await ctx.voice_client.disconnect()

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith(prefix):
        pass
    else:
        if message.guild.voice_client:
            text = message.content
            text = text.replace('\n', '、')
            text = re.sub(r'[\U0000FE00-\U0000FE0F]', '', text)
            text = re.sub(r'[\U0001F3FB-\U0001F3FF]', '', text)
            for char in text:
                if char in emoji.UNICODE_EMOJI['en'] and char in emoji_dataset:
                    text = text.replace(char, emoji_dataset[char]['short_name'])
            pattern = r'<@!?(\d+)>'
            match = re.findall(pattern, text)
            for user_id in match:
                user = await client.fetch_user(user_id)
                user_name = f'、{user.name}へのメンション、'
                text = re.sub(rf'<@!?{user_id}>', user_name, text)
            pattern = r'<@&(\d+)>'
            match = re.findall(pattern, text)
            for role_id in match:
                role = message.guild.get_role(int(role_id))
                role_name = f'、{role.name}へのメンション、'
                text = re.sub(f'<@&{role_id}>', role_name, text)
            pattern = r'<:([a-zA-Z0-9_]+):\d+>'
            match = re.findall(pattern, text)
            for emoji_name in match:
                emoji_read_name = emoji_name.replace('_', ' ')
                text = re.sub(rf'<:{emoji_name}:\d+>', f'、{emoji_read_name}、', text)
            pattern = r'https://tenor.com/view/[\w/:%#\$&\?\(\)~\.=\+\-]+'
            text = re.sub(pattern, '画像', text)
            pattern = r'https?://[\w/:%#\$&\?\(\)~\.=\+\-]+(\.jpg|\.jpeg|\.gif|\.png|\.bmp)'
            text = re.sub(pattern, '、画像', text)
            pattern = r'https?://[\w/:%#\$&\?\(\)~\.=\+\-]+'
            text = re.sub(pattern, '、URL', text)
            #text = message.author.name + '、' + text
            if text[-1:] == 'w' or text[-1:] == 'W' or text[-1:] == 'ｗ' or text[-1:] == 'W':
                while text[-2:-1] == 'w' or text[-2:-1] == 'W' or text[-2:-1] == 'ｗ' or text[-2:-1] == 'W':
                    text = text[:-1]
                text = text[:-1] + '、ワラ'
            for attachment in message.attachments:
                if attachment.filename.endswith((".jpg", ".jpeg", ".gif", ".png", ".bmp")):
                    text += '、画像'
                else:
                    text += '、添付ファイル'
            if len(text) < 100:
                s_quote = urllib.parse.quote(text)
                mp3url = f'http://translate.google.com/translate_tts?ie=UTF-8&q={s_quote}&tl={lang}&client=tw-ob'
                while message.guild.voice_client.is_playing():
                    await asyncio.sleep(0.5)
                message.guild.voice_client.play(discord.FFmpegPCMAudio(mp3url))
            else:
                await message.channel.send('100文字以上は読み上げできません。')
        else:
            pass
    await client.process_commands(message)

@client.event
async def on_voice_state_update(member, before, after):
    if before.channel is None:
        if member.id == client.user.id:
            presence = f'{prefix}ヘルプ | {len(client.voice_clients)}/{len(client.guilds)}サーバー'
            await client.change_presence(activity=discord.Game(name=presence))
        else:
            if member.guild.voice_client is None:
                await asyncio.sleep(0.5)
                await after.channel.connect()
            else:
                if member.guild.voice_client.channel is after.channel:
                    text = member.name + 'さんが入室しました'
                    s_quote = urllib.parse.quote(text)
                    mp3url = f'http://translate.google.com/translate_tts?ie=UTF-8&q={s_quote}&tl={lang}&client=tw-ob'
                    while member.guild.voice_client.is_playing():
                        await asyncio.sleep(0.5)
                    member.guild.voice_client.play(discord.FFmpegPCMAudio(mp3url))
    elif after.channel is None:
        if member.id == client.user.id:
            presence = f'{prefix}ヘルプ | {len(client.voice_clients)}/{len(client.guilds)}サーバー'
            await client.change_presence(activity=discord.Game(name=presence))
        else:
            if member.guild.voice_client:
                if member.guild.voice_client.channel is before.channel:
                    if len(member.guild.voice_client.channel.members) == 1:
                        await asyncio.sleep(0.5)
                        await member.guild.voice_client.disconnect()
                    else:
                        text = member.name + 'さんが退室しました'
                        s_quote = urllib.parse.quote(text)
                        mp3url = f'http://translate.google.com/translate_tts?ie=UTF-8&q={s_quote}&tl={lang}&client=tw-ob'
                        while member.guild.voice_client.is_playing():
                            await asyncio.sleep(0.5)
                        member.guild.voice_client.play(discord.FFmpegPCMAudio(mp3url))
    elif before.channel != after.channel:
        if member.guild.voice_client:
            if member.guild.voice_client.channel is before.channel:
                if len(member.guild.voice_client.channel.members) == 1 or member.voice.self_mute:
                    await asyncio.sleep(0.5)
                    await member.guild.voice_client.disconnect()
                    await asyncio.sleep(0.5)
                    await after.channel.connect()

@client.event
async def on_command_error(ctx, error):
    orig_error = getattr(error, 'original', error)
    error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
    await ctx.send(error_msg)

@client.command()
async def ヘルプ(ctx):
    message = f'''◆◇◆{client.user.name}の使い方◆◇◆
{prefix}＋コマンドで命令できます。
{prefix}接続：ボイスチャンネルに接続します。
{prefix}切断：ボイスチャンネルから切断します。'''
    await ctx.send(message)

#wiki
@client.command()
async def wiki(ctx, *args):
    print("received message: " + str(args))
    if client.user != ctx.message.author:
        try:
            wikipedia.set_lang("ja")
            text=wikipedia.summary(args, auto_suggest=False)
            await ctx.send(text)
        except:
            await ctx.send("検索エラー！")

#talkapi
@client.command()
async def talk(ctx, *args):
    talk_url = "https://api.a3rt.recruit.co.jp/talk/v1/smalltalk"
    payload = {"apikey": talk_api, "query": args}
    response = requests.post(talk_url, data=payload)
    try:
        await ctx.send(response.json()["results"][0]["reply"])
    except:
        print(response.json())
        await ctx.send("ごめんなさい。もう一度教えて下さい。")

@client.command()
async def url(ctx, *args):
    url = 'https://api-ssl.bitly.com/v3/shorten'
    access_token = bitly_token
    query = {
            'access_token': access_token,
            'longurl':args
            }
    r = requests.get(url,params=query).json()['data']['url']
    await ctx.send("短縮したよ！"+"\n"+r)

client.run(token)
