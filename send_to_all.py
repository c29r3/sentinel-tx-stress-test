from cosmospy import Transaction, generate_wallet
import configparser
import requests
from requests import RequestException, Timeout
import json
from pathlib import Path
from time import sleep


headers = {"accept": "application/json", "Content-Type": "application/json"}
c = configparser.ConfigParser()
c.read("config.ini")
c = c["DEFAULT"]

# Load data from config
amount_to_send = int(c["send_to_every_wallet"])
accounts_num   = int(c["accounts_num"])
split_by       = int(c["split_by"])
fee            = int(c["fee"])
keypairs_file  = str(c["keypairs_file"])
provider       = str(c["rpc_providers"]).split(",")[0]
chain_id       = str(c["chain_id"])
denomination   = str(c["denomination"])
BECH32_HRP     = str(c["BECH32_HRP"])
explorer_url   = str(c["explorer_url"])


def generate_keypairs():
    privs_lst = []
    addrs_lst = []

    print(f'Generating new wallets...')
    for i in range(accounts_num):
        new_wallet = generate_wallet(hrp=BECH32_HRP)
        privs_lst.append(new_wallet["private_key"])
        addrs_lst.append(new_wallet["address"])

    with open(keypairs_file, "w") as config_f:
        for n in range(accounts_num):
            config_f.write(f'{addrs_lst[n]};{privs_lst[n]}\n')


def read_keypairs():
    print(f'Reading file {keypairs_file}...')
    addrs_lst = []
    privs_lst = []
    with open(keypairs_file, 'r') as csv_file:
        csv_reader = csv_file.read()
        data_lst = csv_reader.split("\n")

    for line in data_lst:
        if line == "":
            continue
        line = line.split(";")
        addr = line[0]
        priv = line[1]
        if len(addr) != 43 or addr[:4] != "sent" or len(priv) != 64:
            print(f"Incorrect address or private key format {addr}")
            continue
        addrs_lst.append(addr)
        privs_lst.append(priv)

    print(f'Found {len(data_lst)} lines in file {keypairs_file}')
    return addrs_lst, privs_lst


def list_split(keypairs_list: list, list_size: int = 4500):
    keypairs_len = len(keypairs_list)
    if keypairs_len == 0:
        raise Exception("list_split(): list is empty --> exit")

    elif keypairs_len < list_size:
        return keypairs_list

    elif keypairs_len > list_size:
        for n in range(0, keypairs_len, list_size):
            yield keypairs_list[n:n + list_size]


def gen_transaction(recipients_lst: list, priv_key: bytes, amount_lst: list, fee: int, sequence: int, account_num: int,
                    gas: int = 999999999, memo: str = "", chain_id_: str = chain_id, denom: str = denomination):

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

    for i, addr in enumerate(recipients_lst):
        # print(f'{i+1}\\{len(recipients_lst)} {addr} amount: {amount_lst[i]} uakt')
        tx.add_transfer(recipient=recipients_lst[i], amount=amount_lst[i], denom=denom)
    return tx


def req_get(url: str):
    try:
        req = requests.get(url=url, headers=headers)
        if req.status_code == 200:
            return req.json()

    except (RequestException, Timeout) as reqErrs:
        print(f'req_get ERR: {reqErrs}')


def send_trxs(transactions_str: str) -> str:
    try:
        req = requests.post(url=provider+"/txs", data=transactions_str, headers=headers)
        return req.text

    except (RequestException, Timeout) as reqErrs:
        print(f'send_trxs ERR: {reqErrs}')
        return "error"


def get_addr_info(addr: str):
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
        print(Err11)
        return 0, 0, 0


if not Path(keypairs_file).is_file():
    print(f'{keypairs_file=} not found --> generating new key pairs')
    generate_wallet()
    print("Done")

addrs, privs = read_keypairs()

addrs_split_lst = list(list_split(addrs, split_by))
bunch_trans_len = len(addrs_split_lst)
print("Number bunches of transactions", bunch_trans_len)

main_addr = addrs[0]
main_priv = bytes.fromhex(privs[0])
seq, acc_num, balance = get_addr_info(main_addr)

print(f'Address: {main_addr} | balance: {balance} {denomination}')

for i, addrs_bunch in enumerate(addrs_split_lst):
    print(f'Send bunch #{i} of {split_by} addresses')
    _, _, bal = get_addr_info(addrs_bunch[2])
    if bal >= 4:
        print("Already funded --> skip")
        continue

    seq, acc_num, balance = get_addr_info(main_addr)
    txs = gen_transaction(recipients_lst=addrs_bunch, amount_lst=[amount_to_send] * len(addrs_bunch), fee=fee,
                          priv_key=main_priv, sequence=seq, account_num=acc_num)
    pushable_tx = txs.get_pushable()
    result = send_trxs(pushable_tx)
    tx_hash = json.loads(result)["txhash"]
    print(f"{explorer_url}/transactions/{tx_hash}")
    sleep(7)

    while "code" in str(result):
        print(f'RETRY: Send #{i} bunch')
        seq, acc_num, balance = get_addr_info(main_addr)
        txs = gen_transaction(recipients_lst=addrs_bunch, amount_lst=[amount_to_send] * len(addrs_bunch), fee=fee,
                              priv_key=main_priv, sequence=seq, account_num=acc_num)
        pushable_tx = txs.get_pushable()
        result = send_trxs(pushable_tx)
        # print(result)
        sleep(5)

print("Done")


