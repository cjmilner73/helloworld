import get_holdings
import requests
import psycopg2
from configparser import ConfigParser
import boto3
import argparse
import base64
import json
import time
from botocore.exceptions import ClientError

def update_price(token, price, day_change):
    conn = connect()
    # result = {'chris':'milner'}
    cur = conn.cursor()
    sql_update_query = """Update holding set last_price = %s where name = %s"""
    cur.execute(sql_update_query, (price, token))
    sql_update_query = """Update holding set day_change = %s where name = %s"""
    cur.execute(sql_update_query, (day_change, token))
#    sql = "INSERT INTO {} (name, last_price) VALUES ('{}',{})".format("holding", token, price)
#    sql = """INSERT INTO HOLDING VALUES (token,'---',100,price,100)"""
    #cur.execute("insert into holding values ('solana','sol',100,100,100)")
    #cur.execute(sql)
    conn.commit()
    #return "Insert"

def get_secret():

#    secret_name = "tracker_db_secret"
    secret_name = "database"
    region_name = "ap-southeast-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.
    print("SM client...")
    print(client)
    try:
        print("Trying client.get_secret_value")
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        print("Got client.get_secret_value")
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
        print("Should be returning Secret now")
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
        #    print("Secret is" + secret)
            print(type(secret))
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
        print("Calling get_secret()")
        mySecStr = get_secret()
        print("mySecStr password is: " + mySecStr["password"])
        myPass = mySecStr["password"]

        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        connStr = f"host=database-2-cluster.cluster-cnylyxuhkuui.ap-southeast-1.rds.amazonaws.com dbname=postgres user=app_user password={myPass}"
        #connStr = f"host=database-2.cluster-cnylyxuhkuui.ap-southeast-1.rds.amazonaws.com dbname=postgres user=app_user password={myPass}"
        #connStr = f"host=trackerdb.cluster-cnylyxuhkuui.ap-southeast-1.rds.amazonaws.com dbname=postgres user=app_user password={myPass}"
        print("Connection String: " + connStr)
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
