#!/usr/bin/python3.9

import time, json, requests, config, discord, asyncio
from discord.ext import commands
from bs4 import BeautifulSoup
from datetime import datetime

intents = discord.Intents.default()
intents.members = True
taxArg = 1.75
currencies = {}

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print("Bot listo")
    getCurrencies()
    
def getGameWithName(name):
    response = requests.get(f'https://store.steampowered.com/search/?category1=998&term={name}')
    soup = BeautifulSoup(response.content, "html.parser")

    try:
        gameid = soup.find(id="search_resultsRows").findChildren("a" , recursive=False)[0]['href'].split('/')[4]
        return gameid
    except:
        return None

def getCurrencies():
    global currencies
    response = requests.get('https://www.prexcard.com/hacelabien')
    soup = BeautifulSoup(response.content, "html.parser")

    print(f"UY {soup.find(id='cotizacionUy')['value']}")
    print(f"AR {soup.find(id='cotizacionArg')['value']}")
    now = datetime.now()

    currencies['AR'] = float(soup.find(id="cotizacionArg")['value'])
    currencies['UY'] = float(soup.find(id="cotizacionUy")['value'])
    currencies['date'] = now.strftime("%H:%M %d/%m/%Y")

async def sendGame(message, gameid, iscommand):
    game = json.loads(requests.get(f'https://store.steampowered.com/api/appdetails/?appids={gameid}&cc=AR&l=english&v=1').text)

    if message.content.startswith("!sp "):
        if not game[gameid]['success']:
            if iscommand: await message.channel.send(f'Juego con ID **{gameid}** no encontrado')
            return
        if game[gameid]['data']['is_free']:
            if iscommand: await message.channel.send(f"El juego **{game[gameid]['data']['name']}** ya es gratis")
            return
        if not "price_overview" in game[gameid]['data']:
            if iscommand: await message.channel.send(f"Flaco esto no tiene precio")
            return
    
    priceUyString = json.loads(requests.get(f'https://store.steampowered.com/api/appdetails/?appids={gameid}&cc=UY&l=english&v=1').text)[gameid]['data']['price_overview']['final_formatted'].split('U')[1]
    priceArgString = game[gameid]['data']['price_overview']['final_formatted'].split(' ')[1]
    priceArg = float(priceArgString.replace(".", "").replace(",", ".")) * taxArg
    priceUy = float(priceUyString.replace(".", "").replace(",", "."))
        
    priceArgConv = (priceArg * currencies['UY']) / currencies['AR']

    #TODO
    #Reformat this shitty message now that the code is public
    await message.channel.send(f"**{game[gameid]['data']['name']}**\n\nPrecio en Uruguay: **{priceUy}** :flag_uy: \nPrecio en Argentina: **{round(priceArgConv, 2)}** :flag_uy: ({round(priceArg, 2)} :flag_ar: )\n\nAhorro: {round(priceUy - priceArgConv, 2)} :flag_uy: - {round(100 - ((priceArgConv * 100) / priceUy), 1)}%\n\n1 :flag_uy:  = {round(currencies['AR'] / currencies['UY'], 2)} :flag_ar:  (Prex {currencies['date']})\nAbrir con steam: <steam://store/{gameid}>")

@bot.event
async def on_message(message):
    if message.content.split(' ')[0].startswith("https://store.steampowered.com/app/"):
        gameid = message.content.split(' ')[0].split('/')[4]
        await sendGame(message, gameid, False)
        
    if message.content.startswith("!sp "):
        s = message.content[4:]
        gameid = getGameWithName(s)

        if gameid: await sendGame(message, gameid, True)
        else: await message.channel.send(f'No hay resultados para "{s}"')

    
    


                                
bot.run(config.BOTTOKEN, reconnect=True)
