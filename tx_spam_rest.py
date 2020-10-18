from cosmospy import Transaction, generate_wallet
import configparser
import requests
from requests import RequestException, Timeout
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import random
from pprint import pprint
from time import sleep

headers = {"accept": "application/json", "Content-Type": "application/json"}
c = configparser.ConfigParser()
c.read("config.ini")
c = c["DEFAULT"]

# Load data from config
tx_num         = int(c["tx_num"])
threads        = int(c["threads"])
accounts_num   = int(c["accounts_num"])
split_by       = int(c["split_by"])
fee            = int(c["fee"])
keypairs_file  = str(c["keypairs_file"])
rpc_providers  = str(c["rpc_providers"]).split(",")
verbose        = str(c["verbose"])
chain_id       = str(c["chain_id"])
denomination   = str(c["denomination"])
explorer_url   = str(c["explorer_url"])
BECH32_HRP     = str(c["BECH32_HRP"])


def req_get(url: str):
    try:
        req = requests.get(url=url, headers=headers, timeout=10)
        if req.status_code == 200:
            return req.json()

    except (RequestException, Timeout) as reqErrs:
        if verbose == "yes":
            print(f'req_get ERR: {reqErrs} {url}')


def get_addr_info(addr: str, provider: str):
    try:
        """:returns sequence: int, account_number: int, balance: int"""
        d = req_get(f'{provider}/auth/accounts/{addr}')
        if "amount" in str(d):
            acc_num = int(d["result"]["value"]["account_number"])
            seq     = int(d["result"]["value"]["sequence"])
            balance = int(d["result"]["value"]["coins"][0]["amount"])
            return seq, acc_num, balance
        else:
            return 0, 0, 0

    except Exception as Err11:
        if verbose == "yes":
            print(Err11)
        return 0, 0, 0


def gen_transaction(recipients_lst: list, priv_key: bytes, amount_lst: list, fee: int, sequence: int, account_num: int,
                    gas: int = 999999, memo: str = "", chain_id_: str = chain_id, denom: str = denomination):

    tx = Transaction(
        privkey=priv_key,
        account_num=account_num,
        sequence=sequence,
        fee=fee,
        gas=gas,
        memo=memo,
        chain_id=chain_id_,
        sync_mode="sync",
    )
    if len(recipients_lst) != len(amount_lst):
        raise Exception("ERROR: recipients_lst and amount_lst lengths not equal")

    # print(f'Got {len(recipients_lst)} recipients')

    for i, addr in enumerate(recipients_lst):
        # print(f'{i+1}\\{len(recipients_lst)} {addr} amount: {amount_lst[i]} {denomination}')
        tx.add_transfer(recipient=recipients_lst[i], amount=amount_lst[i], denom=denom)
    return tx


def send_trxs(transactions_str: str, provider: str) -> str:
    try:
        req = requests.post(url=provider+"/txs", data=transactions_str, headers=headers)
        return req.text

    except (RequestException, Timeout) as reqErrs:
        if verbose == "yes":
            print(f'send_trxs ERR {provider}: {reqErrs}')


def read_keypairs():
    print(f'Reading file {keypairs_file}...')
    addrs = []
    privs = []
    with open(keypairs_file, 'r') as csv_file:
        csv_reader = csv_file.read()
        data_lst = csv_reader.split("\n")

    for line in data_lst:
        if line == "":
            continue
        line = line.split(";")
        addr = line[0]
        priv = line[1]
        if len(addr) != 43 or addr[:4] != BECH32_HRP or len(priv) != 64:
            print(f"Incorrect address or private key format {addr}")
            continue
        addrs.append(addr)
        privs.append(priv)

    print(f'Found {len(data_lst)} lines in file {keypairs_file}')
    return addrs, privs


def main():
    prov       = random.choice(rpc_providers)
    rand_index = random.randint(0, random_accs)
    address    = addresses[rand_index]
    priv       = bytes.fromhex(private_keys[rand_index])
    addr_lst   = [address] * int(tx_num)
    sequence, account_num, balance = get_addr_info(address, provider=prov)

    if verbose == "yes":
        print(f'{address} nonce: {sequence}')
    txs = gen_transaction(recipients_lst=addr_lst, amount_lst=amount_lst, fee=0, memo=memo,
                          priv_key=priv, sequence=sequence, account_num=account_num)
    pushable_tx = txs.get_pushable()
    result = send_trxs(pushable_tx, provider=prov)
    transaction_hash = json.loads(result)["txhash"]
    if verbose == "yes":
        print(f'{sequence=} | {account_num=} | {balance=}')
        print(f"{result}\n"
              f"{explorer_url}/transactions/{transaction_hash}")


# check if config exists
if Path("config.ini").is_file():
    print('Config found')
else:
    print('Config not found')
    exit(1)

# check if keyfile exists
if Path(keypairs_file).is_file() is False:
    print(f'File with private keys and addresses not fount: {keypairs_file}')
    exit(1)
addresses, private_keys = read_keypairs()
random_accs = len(addresses)
print(f'Loaded {len(addresses)} keypairs')
amount_lst = [1] * int(tx_num)
memo = "f" * 256


# thread pool loop
while True:
    with ThreadPoolExecutor(max_workers=threads) as executor:
        [executor.submit(lambda: main()) for i in range(threads)]

