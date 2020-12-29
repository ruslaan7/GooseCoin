from collections import OrderedDict

import binascii
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from flask import jsonify, request

def new_transaction(blockchain):
    values = request.form

    # проверка запрашиваемых полей
    required = ['sender_address', 'recipient_address', 'amount', 'signature']
    if not all(k in values for k in required):
        return 'Missing values', 400
    # Создание новой транзакции
    new_transaction = blockchain.submit_transaction(values['sender_address'], values['recipient_address'], values['amount'], values['signature'])

    if new_transaction == False:
        response = {'message': 'Invalid Transaction!'}
        return jsonify(response), 406
    else:
        response = {'message': 'Transaction will be added to Block '+ str(new_transaction)}
        return jsonify(response), 201


def get_transactions(blockchain):
    #Получение транзакций из пула транзакций
    transactions = blockchain.transactions

    response = {'transactions': transactions}
    return jsonify(response), 200