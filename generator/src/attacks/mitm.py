""" MITM (Kim): retransmissão via serviço de relay.

Ao interceptar uma notificação legítima, o atacante a reenvia através de um SERVIÇO DE RELAY
(service_id 0x100B, fora do conjunto legítimo), copiando o payload — o "middle hop" malicioso.
O tráfego original continua fluindo.
"""
from src import Msg, SomeIPPacket

NOTIFICATION = SomeIPPacket.messageTypes['NOTIFICATION']
RELAY_SERVICE = 0x100B


def doAttack(curAttack, msgOrig, a, attacksSuc):
    RetVal = {'msg': None, 'attackOngoing': False, 'dropMsg': False, 'counter': attacksSuc}

    if msgOrig.message['type'] == NOTIFICATION:
        message = dict(msgOrig.message)
        message['service'] = RELAY_SERVICE       # relay malicioso
        m = Msg.Msg(msgOrig.sender, msgOrig.receiver, message, msgOrig.timestamp + 0.0002)
        m.label = 'mitm'
        a.writerQueue.put(m)
        RetVal['counter'] = attacksSuc + 1
    else:
        RetVal['attackOngoing'] = True

    return RetVal
