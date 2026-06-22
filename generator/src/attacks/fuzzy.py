""" Fuzzy (Kim/Luo): injeção de mensagens com identificadores e payload aleatórios.

Ao disparar, o atacante emite mensagens com service/method aleatórios (fora do conjunto
legítimo) e payload de tamanho/conteúdo aleatório, para sondar/confundir os serviços.
"""
import random
from src import Msg, SomeIPPacket

NOTIFICATION = SomeIPPacket.messageTypes['NOTIFICATION']
BURST = 12
HEX = '0123456789ABCDEF'


def _rand_payload():
    n = random.randint(0, 40)
    return ''.join(random.choice(HEX) for _ in range(n))


def doAttack(curAttack, msgOrig, a, attacksSuc):
    RetVal = {'msg': None, 'attackOngoing': False, 'dropMsg': False, 'counter': attacksSuc}

    ts = msgOrig.timestamp
    for i in range(BURST):
        message = dict(msgOrig.message)
        message['service'] = random.randint(0x2000, 0x9000)   # serviço fora do legítimo
        message['method'] = random.randint(0x0000, 0xFFFF)
        message['type'] = NOTIFICATION
        message['payload'] = _rand_payload()
        m = Msg.Msg(msgOrig.sender, msgOrig.receiver, message, ts + i * 0.001)
        m.label = 'fuzzy'
        a.writerQueue.put(m)

    RetVal['counter'] = attacksSuc + 1
    return RetVal
