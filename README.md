# sentinel-tx-stress-test  
In Sentinel Turing-3a, a stress test of the network and the readiness of validators to respond quickly to emerging problems was carried out.
The essence of testing was to send many transactions with 0 fee from 50,000 wallets in multi-threaded mode    

1. Launching 3 Sentinel full nodes, launching REST servers over RPC  
2. Generation of private keys and addresses, followed by sending coins to all generated addresses  
3. Script for sending transactions in multithreaded mode  
- the script can send batch transactions  
- can send transactions to multiple REST servers  
 

1. After starting and synchronizing the full Sentinel nodes, the REST servers were launched. There are methods required to send transactions  
`sentinel-hub-cli rest-server --laddr tcp://0.0.0.0:1318 --chain-id sentinel-turing-3a --trust-node true --max-open 15000`

2. `send_to_all.py` - generation of key pairs and batch sending coins to generated wallets

3. `tx_spam_rest.py` - multithreaded transaction sending from all addresses in the file `keypairs.txt`  
A brief description and instructions for launching [here](https://github.com/c29r3/sentinel-tx-stress-test#installation-and-launch)

## A few tips to avoid getting into trouble:  
1. Keep RPC on localhost  
2. Set min fee in `~/.sentinel-hubd/config/app.toml` > 0  
`minimum-gas-prices ="0.0025tsent"` - for example  
3. Set limitnofile to 15000-30000 in systemd unit file `/etc/systemd/system/sentinel.service`  
`LimitNOFILE=30000`
4. Run unjail script. I wrote simple example - https://raw.githubusercontent.com/c29r3/cosmos-utils/main/unjail.sh  
`curl -s https://raw.githubusercontent.com/c29r3/cosmos-utils/main/unjail.sh > unjail.sh && chmod u+x unjail.sh`  
Then edit `unjail.sh` - specify your parameters in variables and run script via tmux  
`tmux new -s sentinel_unjail -d 'cat unjail.sh | bash'`  


## Installation and launch
1. Run command below  
```
apt install -y python3-pip python3-virtualenv git; \
git clone https://github.com/c29r3/sentinel-tx-stress-test.git; \
cd sentinel-tx-stress-test; \
virtualenv venv && source venv/bin/activate && pip install --upgrade pip setuptools wheel; \
pip3 install -r requirements.txt
```  
2. Run REST server on your full node and specify the address in config.ini  
`sentinel-hub-cli rest-server --laddr tcp://0.0.0.0:1318 --chain-id sentinel-turing-3a --trust-node true --max-open 15000`  
3. Run spam script  
`python3 tx_spam_rest.py`  

*This repository created for testing purposes only  
*For generating wallets and sending transcations I used [cosmospy](https://github.com/hukkinj1/cosmospy)
