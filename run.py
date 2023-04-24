#!/usr/bin/python3.9

import json, requests, config, discord
from discord.ext import commands
from bs4 import BeautifulSoup
from datetime import datetime

intents = discord.Intents.default()
intents.members = True
taxArg = 1.75
taxSteam = 1.15
currencies = {}

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print("Bot listo")
    getCurrencies()
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"1 UY = {round(currencies['AR'] / currencies['UY'], 2)} AR"))
    
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
    currencies['MarketDifference'] = getMarketPlacePriceDiference()
    currencies['date'] = now.strftime("%H:%M %d/%m/%Y")

def getMarketPlacePriceDiference():
    itemUY = json.loads(requests.get('https://steamcommunity.com/market/priceoverview/?appid=730&currency=41&market_hash_name=StatTrak%E2%84%A2%20M4A1-S%20|%20Hyper%20Beast%20(Minimal%20Wear)').text)
    itemAR = json.loads(requests.get('https://steamcommunity.com/market/priceoverview/?appid=730&currency=34&market_hash_name=StatTrak%E2%84%A2%20M4A1-S%20|%20Hyper%20Beast%20(Minimal%20Wear)').text)

    stringMedianPriceUY = itemUY['median_price'].split('U')[1]
    stringMedianPriceAR = itemAR['median_price'].split(' ')[1]

    medianPriceUY = float(stringMedianPriceUY.replace(".", "").replace(",", "."))
    medianPriceAR = float(stringMedianPriceAR.replace(".", "").replace(",", "."))
    return round((medianPriceAR / medianPriceUY) / taxSteam, 2)


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
    priceArg = float(priceArgString.replace(".", "").replace(",", ".")) 
    priceUy = float(priceUyString.replace(".", "").replace(",", "."))
        
    priceArgConvPrex = (priceArg * taxArg * currencies['UY']) / currencies['AR']
    priceArgConvSteam = priceArg / currencies['MarketDifference']

    gameDiscount = game[gameid]['data']['price_overview']['discount_percent']

    # Game title

    # The original prices plus the discount if there's any
    #

    # The price converted to UYU using both exchange methods
    # Also calculates the porcentage of discount and the diference with the base uruguayan price

    # Exchange rates for steam market and prex
    #
    # Date of the last update

    # Open the game in the steam client
    await message.channel.send(
    f"""
**__{game[gameid]['data']['name']}__**

Precio en Uruguay: **{priceUy}** :flag_uy: {f'{gameDiscount}% OFF ' if gameDiscount > 0 else ''}
Precio en Argentina: **{priceArg}** :flag_ar: {f'{gameDiscount}% OFF ' if gameDiscount > 0 else ''}
 
Prex: **{round(priceArgConvPrex + currencies['UY'] * 0.99, 2)}** :flag_uy:  {round(priceArgConvPrex, 2)} + {round(currencies['UY'] * 0.99, 2)} | Ahorro {priceUy - round(priceArgConvPrex, 2)} :flag_uy: ({round(100 - (((priceArgConvPrex) * 100) / priceUy), 1)}%)
Steam Market: **{round(priceArgConvSteam, 2)}** :flag_uy: | Ahorro {priceUy - round(priceArgConvSteam, 2)} :flag_uy: ({round(100 - ((priceArgConvSteam * 100) / priceUy), 1)}%)
 
1 :flag_uy: = {round((currencies['AR'] / currencies['UY']) / taxArg, 2)} :flag_ar: (Prex {round(currencies['AR'] / currencies['UY'], 2)} :flag_ar: sin impuesto argentino)
1 :flag_uy: = {currencies['MarketDifference']} :flag_ar: (Steam Market con impuesto de Steam 22%)
Actualizado {currencies['date']}

Abrir con steam: <steam://store/{gameid}>
Abrir en navegador: <https://store.steampowered.com/app/{gameid}>
    """
    )

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
