""" Falha de hardware / safety (SISSA): uma ECU degradada produz dados ERRÁTICOS.

Modela a manifestação no tráfego de uma falha funcional de ECU. A magnitude do evento de falha
e o jitter de timing seguem uma distribuição de **Weibull** (padrão de confiabilidade / desgaste,
como no SISSA). O payload degrada para valores típicos de sensor com defeito: travado em zero
(stuck-at-0) ou saturado (0xFF...). Rotulado 'failure'.

Obs.: a v1 modela o *evento* de falha (rajada errática Weibull-governada). Um modelo de
*vida útil* completo da ECU (degradação contínua) é refinamento futuro.
"""
import numpy as np
from src import Msg, SomeIPPacket

NOTIFICATION = SomeIPPacket.messageTypes['NOTIFICATION']
WEIBULL_SHAPE = 1.5         # k>1 => desgaste/envelhecimento (hazard crescente)
STUCK_AT_ZERO = '00000000'
SATURATED = 'FFFFFFFF'


def doAttack(curAttack, msgOrig, a, attacksSuc):
    RetVal = {'msg': None, 'attackOngoing': False, 'dropMsg': False, 'counter': attacksSuc}

    # magnitude do evento de falha ~ Weibull (nº de mensagens erráticas)
    burst = int(np.random.weibull(WEIBULL_SHAPE) * 15) + 1
    ts = msgOrig.timestamp
    for i in range(burst):
        message = dict(msgOrig.message)
        message['type'] = NOTIFICATION
        # valor degradado: alterna travado-em-zero / saturado
        message['payload'] = STUCK_AT_ZERO if (i % 2 == 0) else SATURATED
        # jitter de timing irregular (sintoma de falha), também Weibull
        jitter = float(np.random.weibull(WEIBULL_SHAPE)) * 0.001
        m = Msg.Msg(msgOrig.sender, msgOrig.receiver, message, ts + i * 0.0005 + jitter)
        m.label = 'failure'
        a.writerQueue.put(m)

    RetVal['counter'] = attacksSuc + 1
    return RetVal
