from collections import OrderedDict

import binascii

import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4
import requests


MINING_SENDER = "THE BLOCKCHAIN"
MINING_REWARD = 1
MINING_DIFFICULTY = 2


def create_block(nonce, previous_hash, chain, transactions):
    """
    Добавление блока транзакции в блокчейн
    """
    block = {'block_number': len(chain) + 1,
             'timestamp': time(),
             'transactions': transactions,
             'nonce': nonce,
             'previous_hash': previous_hash}

    # Задаем начальный массив транзакций
    self.transactions = []

    self.chain.append(block)
    return block


def hash(block):
    """
    Создание хэша для блока
    """
    block_string = json.dumps(block, sort_keys=True).encode()

    return hashlib.sha256(block_string).hexdigest()


def proof_of_work(chain, transactions):
    """
    Доказательство работы
    """
    prev_block = chain[-1]
    prev_hash = hash(prev_block)

    nonce = 0
    while valid_proof(transactions, prev_hash, nonce) is False:
        nonce += 1

    return nonce


def valid_proof(transactions, prev_hash, nonce, difficulty=MINING_DIFFICULTY):
    """
    Проверка, удовлетворяет ли хэш условиям майнинга
    """
    guess = (str(transactions) + str(prev_hash) + str(nonce)).encode()
    guess_hash = hashlib.sha256(guess).hexdigest()
    return guess_hash[:difficulty] == '0' * difficulty


def valid_chain(chain):
    """
    проверяет валидность цепочки блокчейна
    """
    prev_block = chain[0]
    current_ind = 1

    while current_ind < len(chain):
        block = chain[current_ind]
        print(prev_block)
        print(block, "\n")

        # Проверка хэша на корректность
        if block['previous_hash'] != hash(prev_block):
            return False

        # Проверка что функция Proof of work корректна
        # Delete the reward transaction
        transactions = block['transactions'][:-1]
        # Надо убедиться что словарь упорядочен, иначе получится другой хэш
        elements_of_transaction = ['sender_address', 'recipient_address', 'value']
        transactions = [OrderedDict((k, transaction[k]) for k in elements_of_transaction) for transaction in transactions]

        if not valid_proof(transactions, block['previous_hash'], block['nonce'], MINING_DIFFICULTY):
            return False

        prev_block = block
        current_ind += 1

    return True


def resolve_conflicts(nodes, chain):

    '''Происходит разрешение конфликтов между узлами путем заменой на более длинную цепочку
    '''
    neighbours = nodes
    new_chain = None

    # Поиск только самых длинных цепочек
    max_length = len(chain)

    # Проверка цепочек всех узлов сети
    for node in neighbours:
        print('http://' + node + '/chain')
        response = requests.get('http://' + node + '/chain')

        if response.status_code == 200:
            length = response.json()['length']
            chain = response.json()['chain']

            # Check if the length is longer and the chain is valid
            if length > max_length and valid_chain(chain):
                max_length = length
                new_chain = chain

    # Замена на более длинную цепочку
    if new_chain:
        chain = new_chain
        return True

    return False