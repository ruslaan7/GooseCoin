from collections import OrderedDict
import binascii
import Crypto
import Crypto.Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4
import requests
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

#по дефолтку добавим первую транзакцию для блока
MINING_SENDER = "THE BLOCKCHAIN"
MINING_REWARD = 1
MINING_DIFFICULTY = 2

class Blockchain:
    """
    идейно, храним набор следующих транзакций которые добавятся в блок, сама цепочка, которая представляет собой список блоков
    список блоков.....
    """
    def __init__(self, transactions = [], chain = [], nodes = set()):
        self.transactions = transactions
        self.chain = chain
        self.nodes = nodes
        self.node_id = str(uuid4()).replace('-', '')# генерим идентификатр узла, юзаем просто UUID в формате xxxxxxxx.xxxx.Mxxx.Nxxx.xxxxxxxxxxxx
        self.create_block(0, '00')#генезис, не уверен, что в таком виде можно оставить

    def register_node(self, node_url):#регистриурем нового пользователя сети
        parsed_url = urlparse(node_url)
        if parsed_url.path:#чекаем на формат адрес, можно добавить еще доменный формат, но у нас только ip:port
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL when try to register URL')

    def verify_transaction_signature(self, sender_address, signature, transaction):
        """
        Провяряем, что подпись соотвутсвует транзакции
        выносить в отдельный модуль 0 смысла
        """
        public_key = RSA.importKey(binascii.unhexlify(sender_address)) #импортим ключ. Открытый ключ - адрес клиента. hex -> bin
        verifier = PKCS1_v1_5.new(public_key) #PKCS1 стандарт для RSA, не обращайте внимания
        h = SHA.new(str(transaction).encode('utf8')) #SHA256 не заработал, господи...
        return verifier.verify(h, binascii.unhexlify(signature)

    def submit_transaction(self, sender_address, recipient_address, value, signature):
        """
        пушим транзакцию в список транзакций для следующего блока
        """
        transaction = OrderedDict({'sender_address': sender_address,
                                   'recipient_address': recipient_address,
                                   'value': value})

        if sender_address == MINING_SENDER: # первая транзация в блоке
            self.transactions.append(transaction)
            return len(self.chain) + 1
        else: 
            transaction_verification = self.verify_transaction_signature(sender_address, signature, transaction)
            if transaction_verification:
                self.transactions.append(transaction)
                return len(self.chain) + 1
            else:
                return False

    def create_block(self, nonce, previous_hash):
        block = {'block_number': len(self.chain) + 1,
                 'timestamp': time(),
                 'transactions': self.transactions,
                 'nonce': nonce,
                 'previous_hash': previous_hash}
        self.transactions = []

        self.chain.append(block)
        return block

    def hash(self, block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self):
        last_block = self.chain[-1]
        last_hash = self.hash(last_block)
        nonce = 0
        while self.valid_proof(self.transactions, last_hash, nonce) is False:
            nonce += 1
        return nonce

    def valid_proof(self, transactions, last_hash, nonce, difficulty=MINING_DIFFICULTY):
        guess = (str(transactions) + str(last_hash) + str(nonce)).encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:difficulty] == '0' * difficulty

    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            if block['previous_hash'] != self.hash(last_block):
                return False
            transactions = block['transactions'][:-1]
            transaction_elements = ['sender_address', 'recipient_address', 'value']
            transactions = [OrderedDict((k, transaction[k]) for k in transaction_elements) for transaction in
                            transactions]
            if not self.valid_proof(transactions, block['previous_hash'], block['nonce'], MINING_DIFFICULTY):
                return False
            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        neighbours = self.nodes
        new_chain = None
        max_length = len(self.chain)
        for node in neighbours:
            print('http://' + node + '/chain')
            response = requests.get('http://' + node + '/chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
        if new_chain:
            self.chain = new_chain
            return True

        return False


# запускаем нашу ракету------------------------
app = Flask(__name__)
CORS(app)
blockchain = Blockchain()

#роутеры которые нужны были Тимуру
@app.route('/')
def index():
    return render_template('./index.html')
                               
@app.route('/configure')
def configure():
    return render_template('./configure.html')
                               
@app.route('/transactions/new', methods=['POST'])
def new_transaction(): #пушим новую транзакцию в список транзакций если подпись будет верна
    values = request.form
    required = ['sender_address', 'recipient_address', 'amount', 'signature']
    if not all(k in values for k in required):
        return 'Missing values', 400
    transaction_result = blockchain.submit_transaction(values['sender_address'], values['recipient_address'],
                                                       values['amount'], values['signature'])
    if transaction_result == False:
        response = {'message': 'Invalid Transaction!'}
        return jsonify(response), 406
    else:
        response = {'message': 'Transaction will be added to Block ' + str(transaction_result)}
        return jsonify(response), 201


@app.route('/transactions/get', methods=['GET'])
def get_transactions():
    #возврщаем список всех транзакций, нужен Тимуру для вывода доступных транзакций
    transactions = blockchain.transactions
    response = {'transactions': transactions}
    return jsonify(response), 200


@app.route('/chain', methods=['GET'])
def full_chain():#не уверен, что будет нужно, но теоритически должна быть возможность получить всю цепочку
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/mine', methods=['GET'])
def mine():
    last_block = blockchain.chain[-1]
    nonce = blockchain.proof_of_work()
    blockchain.submit_transaction(sender_address=MINING_SENDER, recipient_address=blockchain.node_id,
                                  value=MINING_REWARD, signature="")
    previous_hash = blockchain.hash(last_block)
    block = blockchain.create_block(nonce, previous_hash)
    response = {
        'message': "New Block Forged",
        'block_number': block['block_number'],
        'transactions': block['transactions'],
        'nonce': block['nonce'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():#роутер для регистрации клиента, чекаем на формат добавляем в список
    values = request.form
    nodes = values.get('nodes').replace(" ", "").split(',')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400
    for node in nodes:
        blockchain.register_node(node)
    response = {
        'message': 'New nodes have been added',
        'total_nodes': [node for node in blockchain.nodes],
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()
    #чекаем на более длинную цепочку, Наташа должна дописать решение конфликтов
    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }
    return jsonify(response), 200


@app.route('/nodes/get', methods=['GET'])
def get_nodes():#роутер на список пользователей
    nodes = list(blockchain.nodes)
    response = {'nodes': nodes}
    return jsonify(response), 200

#ДЕФОЛТНЫЙ ПОРТ 5000
if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port
    app.run(host='127.0.0.1', port=port)
