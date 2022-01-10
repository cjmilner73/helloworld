from get_holdings import get_holdings
import requests
import psycopg2
from configparser import ConfigParser
import boto3
import argparse
import base64
import json
import time
from botocore.exceptions import ClientError
# import mysecret


def get_prices():
    allHoldings = get_holdings()
    for i in allHoldings:
        token = i[0]
        urlFull = 'https://api.coingecko.com/api/v3/simple/price?ids=' + token + '&vs_currencies=usd&include_24hr_change=true'
        r = requests.get(urlFull)
        tokenDict = r.json()
        priceDict = tokenDict[token]
        print(priceDict)
        price = priceDict['usd']
        day_change = priceDict['usd_24h_change']
        get_holdings.update_price(token, price, day_change)
    return("Success Prices")

get_prices()
