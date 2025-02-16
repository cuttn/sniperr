import asyncio
import aiohttp
import json
import requests
from datetime import datetime, timezone
from gql import Client, gql
from gql.transport.websockets import WebsocketsTransport

headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ory_at_N08PIbMJrl5vTAUu0qNDAaAbcaZrO1MJIlkehwwFxwk.6dgOJJoXFRzFiYIMF7VcbsRm0oTR3ScODdQochOn8uU'
}

url = "https://streaming.bitquery.io/eap"
devToken = {}
currentTask = None
inTheRing = None
devQuery = ""
socket = WebsocketsTransport(
    url="wss://streaming.bitquery.io/eap?token=ory_at_N08PIbMJrl5vTAUu0qNDAaAbcaZrO1MJIlkehwwFxwk.6dgOJJoXFRzFiYIMF7VcbsRm0oTR3ScODdQochOn8uU",
    headers={"Sec-WebSocket-Protocol": "graphql-ws"},
)

holding = {}

snipe = ""

moneyyy = 100

lastcall = {"time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}  # Store as dict, not string

tasks = {}  # Track running tasks

def is_timestamp_good(timestamp_str):
    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - timestamp).total_seconds() / 3600 < 2

async def spawnCamp():
    global lastcall
    print(lastcall)
    payload = json.dumps({
        "query": f"""{{
            Solana {{
                TokenSupplyUpdates(
                    where: {{
                        Instruction: {{ Program: {{ Method: {{ is: "create" }} }} }},
                        TokenSupplyUpdate: {{ Currency: {{ Uri: {{ startsWith: "https:" }}, MintAddress: {{ endsWith: "pump" }} }} }},
                        Block: {{ Time: {{ after: "{lastcall["time"]}" }} }}
                    }},
                    limit: {{ count: 100 }},
                    orderBy: {{ ascending: Block_Time }}
                ) {{
                    Block {{ Time }}
                    Transaction {{ Signer }}
                    TokenSupplyUpdate {{ Currency {{ Symbol MintAddress }} }}
                }}
            }}
        }}""",
    })

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=payload) as response:
            data = await response.json()
            data = data.get('data', {}).get('Solana', {}).get('TokenSupplyUpdates', [])
    
    if data:
        lastcall = {"time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}  # Store as dict, not string  # Store back in dict
        for token in data:
            realshit = await isDevABaller(token["TokenSupplyUpdate"]["Currency"]["MintAddress"])
            if realshit and token["TokenSupplyUpdate"]["Currency"]["MintAddress"] not in [v[0] for v in devToken.values()]:
                devToken[token["Transaction"]["Signer"]] = [
                    token["TokenSupplyUpdate"]["Currency"]["MintAddress"],
                    token["Block"]["Time"],
                    realshit[0],
                    realshit[1],
                ]
                await smgNoSnipes()
    await asyncio.sleep(30)
                
async def isDevABaller(token):
    payload = json.dumps({
   "query": f"query MyQuery {{\n  Solana {{\n    DEXTrades(\n      where: {{Trade: {{Buy: {{Currency: {{MintAddress: {{is: \"{token}\"}}}}}}}}}}\n      limit: {{count: 1}}\n      orderBy: {{ascending: Block_Time}}\n    ) {{\n      Trade {{\n        Buy {{\n          Amount\n          Account {{\n            Owner\n          }}\n          PriceInUSD\n        }}\n      }}\n    }}\n  }}\n}}\n",
   "variables": "{}"
    })

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=payload) as response:
            data = await response.json()
            data = data.get('data', {}).get('Solana', {}).get('DEXTrades', [])
    if data:
        trade = data[0]['Trade']['Buy']
        amount = float(trade['Amount'])  # Convert the amount to a float
        price = trade['PriceInUSD']
    
    if price > .0000077:
        print("big baller found: " + token)
        return [price, amount*price]
    else:
        return False

async def ate(query):
    async for result in socket.subscribe(query):
        for dev, trades in result.data.items():  # Ensure we iterate over actual data
            dex_trades = trades.get("DEXTrades", [])  # Safely get "DEXTrades"
            if dex_trades:
                print("ok this is an actual snipe right here wow")
                first_trade = dex_trades[0]
                coin = {
                    "mint": first_trade["Trade"]["Buy"]["Currency"]["MintAddress"],
                    "amount": first_trade["Trade"]["Buy"]["Amount"],
                    "price": first_trade["Trade"]["Buy"]["Price"],}
                if coin["price"] < holding[dev[1:]]["price"] * .9:
                    print(holding[dev[1:]]["$$$$$"])
                    holding.pop(holding[dev[1:]])
                    await smgNoSnipes()
                else:
                    holding[dev[1:]]["$$$$$"] = max(holding[dev[1:]]["$$$$$"], coin["price"]/holding[dev[1:]]["price"])
        
async def subscriptionTask(query):
    global snipe, inTheRing
    try:
        print(query)
        async for result in socket.subscribe(query):
            for dev, trades in result.data.items():  # Ensure we iterate over actual data
                dex_trades = trades.get("DEXTrades", [])  # Safely get "DEXTrades"
                if dex_trades:  # Check if there are any trades
                    first_trade = dex_trades[0]
                    coin = {
                        "mint": first_trade["Trade"]["Buy"]["Currency"]["MintAddress"],
                        "amount": first_trade["Trade"]["Buy"]["Amount"],
                        "price": first_trade["Trade"]["Buy"]["Price"],
                        "$$$$$" : 1}
                    devToken.pop(dev[1:], None)
                    holding[dev[1:]] = coin
                    print("SNIPE!!" + coin["mint"])
            for dev, coin in holding.items():
                snipe += f'''
                            {"a" + dev} : Solana {{
                                DEXTrades(
                                    where: {{
                                        Trade: {{
                                            Dex: {{ ProtocolName: {{ is: "pump" }} }},
                                            Buy: {{
                                                Currency: {{ MintAddress: {{ is: "{coin["mint"]}" }} }},
                                            }}
                                        }},
                                        Transaction: {{ Result: {{ Success: true }} }}
                                    }}
                                ) {{
                                    Trade {{ 
                                        Buy {{ 
                                            Amount 
                                            Price 
                                            PriceInUSD 
                                            Currency {{ Symbol MintAddress }}
                                            Account {{ Owner }}
                                        }} 
                                    }}
                                    Block {{ Time }}
                                }}
                            }}\n
                        '''
            if len(snipe) != 0:
            # if is_timestamp_good(token[1]):
                letsGetThisBRead = gql(f"""
                    subscription {{
                        {snipe}
                    }}
                """)
            if inTheRing and not inTheRing.done():
                await asyncio.sleep(len(holding.keys()))
                inTheRing.cancel()
                
            inTheRing = asyncio.create_task(ate(letsGetThisBRead))
            await smgNoSnipes()
                
    except asyncio.CancelledError:
        print("Subscription cancelled.")
    except Exception as e:
        print(f"Error in subscriptionTask: {e}")


async def smgNoSnipes():
    global devQuery, currentTask
    
    print("reloading sniper...")
    
    devQuery = ""
    for dev, token in devToken.items():
        if is_timestamp_good(token[1]):
            devQuery += f'''
                            {"a" + dev} : Solana {{
                                DEXTrades(
                                    where: {{
                                        Trade: {{
                                            Dex: {{ ProtocolName: {{ is: "pump" }} }},
                                            Buy: {{
                                                Currency: {{ MintAddress: {{ is: "{token[0]}" }} }},
                                                AmountInUSD: {{ gt: "200" }},
                                            }}
                                        }},
                                        Transaction: {{ Result: {{ Success: true }} }}
                                    }}
                                ) {{
                                    Trade {{ 
                                        Buy {{ 
                                            Amount 
                                            Price 
                                            PriceInUSD 
                                            Currency {{ Symbol MintAddress }}
                                            Account {{ Owner }}
                                        }} 
                                    }}
                                    Block {{ Time }}
                                }}
                            }}\n
                        '''
            # we use these after but for testing i gotta remove them
                                    # Account: {{ Owner: {{ is: "{dev}" }} }},
                                    # Currency: {{ MintAddress: {{ is: "{token[0]}" }} }},
                                    # AmountInUSD: {{ gt: "77" }},
                                    # PriceInUSD: {{ lt: {token[2]*2} }},
                                    # AmountInUSD: {{ gt: "77" }},
        else:
            devToken.pop(dev, None)
    if len(devQuery) != 0:
    # if is_timestamp_good(token[1]):
        query = gql(f"""
            subscription {{
                {devQuery}
            }}
        """)
        if currentTask and not currentTask.done():
            await asyncio.sleep(len(devToken.values()))
            currentTask.cancel()
        currentTask = asyncio.create_task(subscriptionTask(query))
                # Solana {{
                #     DEXTrades(
                #         where: {{
                #             Trade: {{
                #                 Dex: {{ ProtocolName: {{ is: "pump" }} }},
                #                 Buy: {{
                #                     Currency: {{ MintAddress: {{ is: "{token[0]}" }} }},
                #                     Account: {{ Owner: {{ is: "{dev}" }} }},
                #                     AmountInUSD: {{ gt: "1000" }},
                #                     PriceInUSD: {{ lt: {token[2]*2} }}
                #                 }}
                #             }},
                #             Transaction: {{ Result: {{ Success: true }} }}
                #         }}
                #     ) {{
                #         Instruction {{ Program {{ Method }} }}
                #         Trade {{ Buy {{ Amount Currency {{ Symbol MintAddress }} Account {{ Owner }} }} }}
                #         Transaction {{ Signature }}
                #     }}
                # }}

        # else:
        #     devToken.pop(dev, None)  # Safe removal
    else:
        print("no dev :()")

async def main():
    await socket.connect()
    while True:
        try:
            await asyncio.gather(spawnCamp())
        except Exception as e:
            print(f"Main loop error: {e}")
            await socket.close()
            await asyncio.sleep(5)
            await socket.connect()
        await asyncio.sleep(5)

# Run the asyncio event loop
asyncio.run(main())
