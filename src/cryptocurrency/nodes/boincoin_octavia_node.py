"""
Created on Sat Nov 21 10:37:20 2020

@author: Olich
"""

# Create a Cryptocurrency

# To be installed
# Flask: pip install Flask==0.12.2
# Postman http client
# requests==2.18.4: pip install requests==2.18.4

# importing the libraries
import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse


# ---------------------- Building a Blockchain --------------------------------------------------

class Blockchain:
    
    def __init__(self):
        # chain list containing blocks
        self.chain = []
        # transactions list used to adding waiting transactions in a block
        self.transactions = []
        # create genesis block
        self.create_block(proof = 1, previous_hash = '0' )
        # nodes connected to the network
        self.nodes = set()

    def create_block(self, proof, previous_hash):        
        block = { 
            'index': len(self.chain) + 1, 
            'timestamp': str(datetime.datetime.now()),
            'proof': proof,
            'previous_hash': previous_hash,
            'transactions' : self.transactions
        }        
        # clear transactions list
        self.transactions = []
        # add block to our chain
        self.chain.append(block)        
        return block
    
    def get_previous_block(self):
        return self.chain[-1]
    
    def proof_of_work(self, previous_proof):
        
        new_proof = 1
        check_proof = False
        
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        
        return new_proof
    
    def hash(self, block):
        
        encoded_block = json.dumps(block, sort_keys = True).encode()
        
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self, chain):
        #init loop variable
        previous_block = chain[0]
        block_index = 1
        
        # checking every block in a chain
        while block_index < len(chain):
            # set current block
            block = chain[block_index]
            # 1. check for valid previus hash
            if block['previous_hash'] != self.hash(previous_block):
                return False
            
            # 2. check for valid proof of work operation
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            
            # update loop variables
            previous_block = block
            block_index += 1
            
        # blockchain is valid
        return True                   
    
    def add_transaction(self, sender, receiver, amount):
        # add new transaction object
        self.transactions.append({ 'sender': sender,
                                   'receiver': receiver,
                                   'amount' : amount })
        # return a index of block (next block of chain) that
        # would receive this transaction
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1
    
    def add_node(self, address):
        # parse node address to url
        parsed_url = urlparse(address)
        # add netloc (ip + port number) to nodes
        self.nodes.add(parsed_url.netloc)
        
    # method to replace any chain that is shorter then longest  chain
    # among all the nodes of the network
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        # scan the network in order to fing a longest chain
        for node in network:
            # send get chain request to target node
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        
        if longest_chain:
            # replace my chain with the longest found
            self.chain = longest_chain
            return True
        
        return False

# ---------------------- Mining Blockchain --------------------------------------------------

# Creating a Web App
app = Flask(__name__)

# Creating an address for the node on Port 5000
node_address = str(uuid4()).replace('-','')

# Creating a Blockchain        
blockchain = Blockchain()

# mining a new block
@app.route("/mine_block", methods=['POST'])
def mine_block():
    # get data for new block
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    # add transaction
    blockchain.add_transaction(sender = node_address, receiver = 'Octavia', amount = 1)
    # create new block    
    block = blockchain.create_block(proof, previous_hash)
    
    # set response    
    response = { 'message' : 'Congrats Brate, a block is mined!', 
                 'index' : block['index'],
                 'timestamp' : block['timestamp'],
                 'proof' : block['proof'],
                 'previous_hash' : block['previous_hash'],
                 'transactions': block['transactions']
                 
    }
    
    return jsonify(response), 200

# getting the full blockchain
@app.route("/get_chain", methods=['GET'])
def get_chain():
    # set response
    # print(blockchain.chain)
    response = { 'chain' : blockchain.chain, 
                 'length' : len(blockchain.chain)
    }  

    return jsonify(response), 200

# Checking if the Blockchain is valid
@app.route('/is_valid', methods = ['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message': 'All good. The Blockchain is valid.'}
    else:
        response = {'message': 'Brate, we have a problem. The Blockchain is NOT valid.'}
    return jsonify(response), 200

# Adding a new transaction to the blockchain
@app.route('/add_transaction', methods = ['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amount']
    # validate a request
    if not all (key in json for key in transaction_keys):
        return 'Some elements of the transaction are missing', 400
    
    block_index = blockchain.add_transaction(json['sender'], json['receiver'], json['amount'])
    
    response = { 'message': f'Transaction will be added to block {block_index}',
                 'block_id': block_index
    }
    return jsonify(response), 201

# ---------------------- Decentralizing Blockchain --------------------------------------------------
# Connecting new nodes to the network
@app.route('/connect_node', methods = ['POST'])
def connect_node():
    # contain all nodes on the network including the new one
    json = request.get_json()
    nodes = json.get('nodes')
    
    if nodes is None:
        return "No node", 400
    
    for node in nodes:
        blockchain.add_node(node)
        
    response = { 'message': 'All the nodes was connected!',
                 'total_nodes': list(blockchain.nodes)
    }
    return jsonify(response), 201

# Replacing the chain by the longest chain if needed
@app.route('/replace_chain', methods = ['POST'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()    
    
    if is_chain_replaced:
        response = {'message': 'The nodes had different chains. The chain was replaced by the longest one!',
                    'chain': blockchain.chain            
        }
    else:
        response = {'message': 'All good. The chain is already the largest one!',
                    'chain': blockchain.chain
        }
    return jsonify(response), 200
    
# RUNNING THE APP
app.run(host = '0.0.0.0', port = 5002)    

