# sentinel-tx-stress-test  
`tx_spam_rest.py` - multithreaded transaction sending from all addresses in the file `keypairs.txt`  
`send_to_all.py` - generation of key pairs and batch sending coins to generated wallets  

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
