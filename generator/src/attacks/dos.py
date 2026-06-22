""" DoS (Kim/Luo): inundação de notificações de alta taxa.

Ao disparar, o atacante emite uma RAJADA de notificações para o destino da mensagem que passou,
em intervalos muito curtos. O tráfego original continua fluindo.
"""
from src import Msg, SomeIPPacket

NOTIFICATION = SomeIPPacket.messageTypes['NOTIFICATION']
BURST = 40        # nº de pacotes por disparo
IAT = 0.0002      # ~5000 pkt/s


def doAttack(curAttack, msgOrig, a, attacksSuc):
    RetVal = {'msg': None, 'attackOngoing': False, 'dropMsg': False, 'counter': attacksSuc}

    ts = msgOrig.timestamp
    for i in range(BURST):
        message = dict(msgOrig.message)
        message['type'] = NOTIFICATION
        m = Msg.Msg(msgOrig.sender, msgOrig.receiver, message, ts + i * IAT)
        m.label = 'dos'
        a.writerQueue.put(m)

    RetVal['counter'] = attacksSuc + 1
    return RetVal
