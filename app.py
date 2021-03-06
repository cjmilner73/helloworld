from chalice import Chalice
import requests
import psycopg2
from configparser import ConfigParser
import os
import boto3
import argparse
import base64
import json
import logging
from pprint import pprint
import time
import boto3
from botocore.exceptions import ClientError
# import mysecret


app = Chalice(app_name='helloworld')

@app.route('/dummy2')
def dummy2():
    return("dummy")


@app.route('/holdings')
def get_holdings():
    print("Entering get_holdings()")
    path = os.getcwd()
    conn = connect()
    cur = conn.cursor()
    #result = {'chris':'milner'}
    cur.execute('SELECT * from holding')
    result = cur.fetchall()
    print(result)
    return result

@app.route('/ohlc')
def get_prices():
    allHoldings = get_holdings()
    for i in allHoldings:
        token = i[0]
        print(token)
        urlFull = 'https://api.coingecko.com/api/v3/coins/' + token + '/ohlc?vs_currency=usd&days=90'
        r = requests.get(urlFull)
        ohlcDict = r.json()
        print(ohlcDict)
#        priceDict = tokenDict[token]
#        print(priceDict)
#        price = priceDict['usd']
#        day_change = priceDict['usd_24h_change']
#        update_price(token, price, day_change)

@app.route('/prices')
def get_prices():
    print("Entering get_prices()")
    allHoldings = get_holdings()
    for i in allHoldings:
        print(i)
        token = i[0]
        urlFull = 'https://api.coingecko.com/api/v3/simple/price?ids=' + token + '&vs_currencies=usd&include_24hr_change=true'
        print(urlFull)
        r = requests.get(urlFull)
        print("Did we get here?")
        tokenDict = r.json()
        print(urlFull)
        priceDict = tokenDict[token]
        print(priceDict)
        price = priceDict['usd']
        day_change = priceDict['usd_24h_change']
        print(token)
        print(price)
        print(day_change)
        update_price(token, price, day_change)
        print("Updated prices");
    #return("Updated Prices")
        

#    token = 'bitcoin'
#    urlFull = 'https://api.coingecko.com/api/v3/simple/price?ids=' + token + '&vs_currencies=usd&include_24hr_change=true'
#    print(urlFull)
#    # r =requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin%2Cethereum&vs_currencies=usd')
#    r = requests.get(urlFull)
#    tokenDict = r.json()
#    priceDict = tokenDict[token]
#    price = priceDict['usd']
#    update_price(token, price)
    #return(true)

@app.route('/update')
def update_price(token, price, day_change):
    print("Entering update_price()")
    path = os.getcwd()
    conn = connect()
    # result = {'chris':'milner'}
    cur = conn.cursor()
    sql_update_query = """Update holding set last_price = %s where name = %s"""
    cur.execute(sql_update_query, (price, token))
    sql_update_query = """Update holding set day_change = %s where name = %s"""
    cur.execute(sql_update_query, (day_change, token))
    #sql = "INSERT INTO {} (name, last_price) VALUES ('{}',{})".format("holding", token, price)
    #cur.execute("insert into holding values ('solana','sol',100,100,100)")
    #cur.execute(sql)
    conn.commit()
    #return "Insert"

def get_secret():

    print("Entering get_secret()")
#    secret_name = "tracker_db_secret"
    secret_name = "database"
    #secret_name = "database-serverless"
    region_name = "ap-southeast-1"
    #secret_name = "arn:aws:secretsmanager:ap-southeast-1:869696343558:secret:database-serverless-Kq00lE"
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.
    print(client)
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        print("Response e.response:")
        print(e.response)
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            print("Failed:1 ")
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            print("Failed:2 ")
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            print("Failed:3 ")
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            print("Failed:4 ")
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            print("Failed:5 ")
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            return json.loads(secret)
        else:
            decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
    finally:
        print("Finally")
    # Your code goes here.

def connect():
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        print("Entering connect())")
        mySecStr = get_secret()
        #print("mySecStr password is: " + mySecStr["password"])
        myPass = mySecStr["password"]

        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        connStr = f"host=trackdb-cluster.cluster-cnylyxuhkuui.ap-southeast-1.rds.amazonaws.com dbname=trackdb user=sysadmin password={myPass}"
        #connStr = f"host=database-2-cluster.cluster-cnylyxuhkuui.ap-southeast-1.rds.amazonaws.com dbname=postgres user=app_user password={myPass}"
        #connStr = f"host=tracker.cluster-cnylyxuhkuui.ap-southeast-1.rds.amazonaws.com dbname=trackdb user=sysadmin password={myPass}"
        #connStr = f"host=database-2.cluster-cnylyxuhkuui.ap-southeast-1.rds.amazonaws.com dbname=postgres user=app_user password={myPass}"
        #connStr = f"host=trackerdb.cluster-cnylyxuhkuui.ap-southeast-1.rds.amazonaws.com dbname=postgres user=app_user password={myPass}"
        # print("Connection String: " + connStr)
        conn = psycopg2.connect(connStr)
        # conn = psycopg2.connect("host=localhost dbname=tracker user=app_user password={myPass}")
		
        # create a cursor
        return(conn)
        cur = conn.cursor()
	# execute a statement
        print('PostgreSQL database version:')
        cur.execute('SELECT * from holding')
        # cur.execute('SELECT version()')

        # display the PostgreSQL database server version
        # db_version = cur.fetchone()
        db_version = cur.fetchall()
        print(db_version)
       
	# close the communication with the PostgreSQL
        cur.close()
        return(db_version)
    except (Exception, psycopg2.DatabaseError) as error:
        print(type(error))
        print(str(error))
        print("Return error")
        return(str(error))
    finally:
        if conn is not None:
#            conn.close()
            print('Database connection closed.')

# The view function above will return {"hello": "world"}
# whenever you make an HTTP GET request to '/'.
#
# Here are a few more examples:
#
# @app.route('/hello/{name}')
# def hello_name(name):
#    # '/hello/james' -> {"hello": "james"}
#    return {'hello': name}
#
# @app.route('/users', methods=['POST'])
# def create_user():
#     # This is the JSON body the user sent in their POST request.
#     user_as_json = app.current_request.json_body
#     # We'll echo the json body back to the user in a 'user' key.
#     return {'user': user_as_json}
#
# See the README documentation for more examples.
#
