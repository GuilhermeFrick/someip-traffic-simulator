""" Tamper (Luo): adultera o VALOR do payload de uma mensagem em trânsito.

Injeta uma cópia forjada de uma notificação/resposta com o payload alterado (valor anômalo),
impersonando o remetente legítimo. O tráfego original continua fluindo.
"""
import copy
from src import Msg, SomeIPPacket

NOTIFICATION = SomeIPPacket.messageTypes['NOTIFICATION']
RESPONSE = SomeIPPacket.messageTypes['RESPONSE']
TAMPERED_PAYLOAD = 'DEADBEEFDEADBEEF'   # valor adulterado, fixo e fora de distribuição


def doAttack(curAttack, msgOrig, a, attacksSuc):
    RetVal = {'msg': None, 'attackOngoing': False, 'dropMsg': False, 'counter': attacksSuc}

    if msgOrig.message['type'] in (NOTIFICATION, RESPONSE):
        m = Msg.Msg(msgOrig.sender, msgOrig.receiver, dict(msgOrig.message),
                    msgOrig.timestamp + 0.0001)
        m.message['payload'] = TAMPERED_PAYLOAD
        m.label = 'tamper'
        a.writerQueue.put(m)
        RetVal['counter'] = attacksSuc + 1
    else:
        RetVal['attackOngoing'] = True   # espera uma mensagem do tipo certo

    return RetVal
