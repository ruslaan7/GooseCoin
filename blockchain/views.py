from urllib import response

from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, HttpRequest
import time
import hashlib
import json
from urllib.parse import urlparse
import requests
from uuid import uuid4



class Blockchain:
    '''
    Blockchain class
    '''

    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.create_new_block(proof_of_work = 100,previous_hash=1)
        self.network_nodes = set()

    def create_new_block(self, proof_of_work, previous_hash):
        """

        :param proof_of_work: proof of done work
        :param previous_hash: previous block hash
        :return: new block
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'proof_of_work': proof_of_work,
            'transactions': self.current_transactions,
            'previous_hash': previous_hash,
        }

        self.current_transactions = []
        self.chain.append(block)

        return block

    def create_new_transaction(self,  sender, recipient, amount):
        """

        :param sender: transaction sender adress
        :param recipient: recipient sender adress
        :param amount: transaction amount
        :return: last block index
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.chain[-1]['index']+1

    @staticmethod
    def hash_block(block):
        """

        :param block: input block
        :return: block hash
        """
        json_encoded_block = json.dumps(block,sort_keys=True).encode()
        return hashlib.sha256(json_encoded_block).hexdigest()


    def chain_validation_check(self,chain):
        """

        :param chain: actual chain
        :return: bool value
        """
        previous_block = chain[0]
        chain=chain[1:]
        for block in chain:
            if block['previous_hash'] != self.hash_block(previous_block):
                return False
            previous_proof = previous_block['proof_of_work']
            proof_of_work = block['proof_of_work']
            guess = f'{previous_proof}{proof_of_work}'.encode()
            guess_hash = hashlib.sha256(guess).hexdigest()
            if guess_hash[:4] != '0000':
                return False
            previous_block = block
        return True




    def proof_of_work(self, previous_proof):
        """

        :param previous_proof:
        :return: proof_of_work
        """
        proof_of_work = 1
        check_proof = False
        while check_proof is False:
            guess = f'{previous_proof}{proof_of_work}'.encode()
            guess_hash = hashlib.sha256(guess).hexdigest()
            if guess_hash[:4] == '0000':
                check_proof = True
            else:
                proof_of_work += 1
        return proof_of_work


    def add_new_node(self, url):
        """

        :param url: node url
        :return:
        """
        url = urlparse(url)
        self.network_nodes.add(url.netloc)

    def sync_nodes_by_chain(self):

        network = self.network_nodes
        max_chain = []
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.chain_validation_check(chain):
                    max_length = length
                    max_chain = chain
        if max_chain:
            self.chain = max_chain
            return True
        return False


blockchain = Blockchain()
node_identifier = str(uuid4()).replace('-', '') #new node exemple


def get_full_chain(request):
    """

    :param request:
    :return: full chain
    """
    if request.method == 'GET':
        responses = {'chain': blockchain.chain,
                    'length': len(blockchain.chain)}
    return JsonResponse(responses)

def chain_is_valid(request):
    if request.method == 'GET':
        chain_is_valid = blockchain.chain_validation_check(blockchain.chain)
        responses = {'message': 'Blockchain is valid'} if chain_is_valid else {'message': 'Blockchain is not valid'}

    return JsonResponse(responses)



def add_new_transaction(request):
    if request.method == 'POST':
        values = json.loads(request.body)
        need_keys = ['sender', 'recipient', 'amount']
        if not all(key in values for key in need_keys):
            return 'There are some missing values', HttpResponse(status=400)
        index = blockchain.create_new_transaction(values['sender'],
                                                  values['receiver'],
                                                  values['amount'])
        responses = {'message': f'Transaction will be added to Block {index}'}
    return JsonResponse(responses)

def sync_nodes(request):
    if request.method == 'GET':
        is_chain_synced = blockchain.sync_nodes_by_chain()
        responses = {'message': 'Chain synced','new_chain': blockchain.chain} if is_chain_synced else {'message': 'Your chain is actual',
                        'actual_chain': blockchain.chain}
    return JsonResponse(responses)


def connect_new_node(request):
    if request.method == 'POST':
        received_json = json.loads(request.body)
        nodes = received_json.get('nodes')
        if nodes is None:
            return "No node", HttpResponse(status=400)
        for node in nodes:
            blockchain.add_new_node(node)
        responses = {
            'message': 'All the nodes are now connected. The Sudocoin Blockchain now contains the following nodes:',
            'total_nodes': list(blockchain.network_nodes)}
    return JsonResponse(responses)

def mining():
    pass
