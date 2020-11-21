"""
Created on Sat Nov 21 10:37:20 2020

@author: Olich
"""

# Create a Blockchain

# To be installed
# Flask: pip install Flask==0.12.2
# Postman http client


# importing the libraries
import datetime
import hashlib
import json
from flask import Flask, jsonify


# ---------------------- Building a Blockchain --------------------------------------------------

class Blockchain:
    
    def __init__(self):
        self.chain = []
        self.create_block(proof = 1, previous_hash = '0' )

    def create_block(self, proof, previous_hash):
        
        block = { 
            'index': len(self.chain) + 1, 
            'timestamp': str(datetime.datetime.now()),
            'proof': proof,
            'previous_hash': previous_hash
        }
        
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
    
        

# ---------------------- Mining our Blockchain --------------------------------------------------

# Creating a Web App
app = Flask(__name__)

# Creating a Blockchain        
blockchain = Blockchain()

# mining a new block from request
@app.route("/mine_block", methods=['GET'])
def mine_block():
    # get data for new block
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    
    # create new block    
    block = blockchain.create_block(proof, previous_hash)
    
    # set response    
    response = { 'message' : 'Congrats, you just mined a block!', 
                 'index' : block['index'],
                 'timestamp' : block['timestamp'],
                 'proof' : block['proof'],
                 'previous_hash' : block['previous_hash']                
    }
    
    #return response
    return jsonify(response), 200

# getting the full blockchain
@app.route("/get_chain", methods=['GET'])
def get_chain():
    # set response
    # print(blockchain.chain)
    response = { 'chain' : blockchain.chain, 
                 'length' : len(blockchain.chain)
    }  
    
    #return response
    return jsonify(response), 200

# Checking if the Blockchain is valid
@app.route('/is_valid', methods = ['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message': 'All good. The Blockchain is valid.'}
    else:
        response = {'message': 'Houston, we have a problem. The Blockchain is not valid.'}
    return jsonify(response), 200


# RUNNING THE APP
app.run(host = '0.0.0.0', port = 5000)    

