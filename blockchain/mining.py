from collections import OrderedDict

import hashlib
import json
from time import time
import requests


mining_root = "THE BLOCKCHAIN"
#mining_reward = 1
mining_difficulty = 3


def create_block(nonce, previous_hash, chain, transactions):
    """
    Добавление блока транзакции в блокчейн
    """
    block = {'block_number': len(chain) + 1,
             'timestamp': time(),
             'transactions': transactions,
             'nonce': nonce,
             'previous_hash': previous_hash}

    chain.append(block)
    return block, chain


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


def valid_proof(transactions, prev_hash, nonce, mining_difficulty):
    """
    Проверка, удовлетворяет ли хэш условиям майнинга
    """
    guess = (str(transactions) + str(prev_hash) + str(nonce)).encode()
    guess_hash = hashlib.sha256(guess).hexdigest()
    return guess_hash[:mining_difficulty] == '0' * mining_difficulty


def valid_chain(chain):
    """
    проверяет валидность цепочки блокчейна
    """
    prev_block = chain[0]
    current_ind = 1

    while current_ind < len(chain):
        block = chain[current_ind]
        print('prev_block = ', prev_block)
        print('block = ', block, "\n")

        # Проверка хэша на корректность

        if block['previous_hash'] != hash(prev_block):
            return False

        # Проверка что функция Proof of work корректна
        transactions = block['transactions'][:-1]
        # Надо убедиться что словарь упорядочен, иначе получится другой хэш
        elements_of_transaction = ['sender_address', 'recipient_address', 'value']
        transactions = [OrderedDict((k, transaction[k]) for k in elements_of_transaction) for transaction in transactions]

        if not valid_proof(transactions, block['previous_hash'], block['nonce'], mining_difficulty):
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