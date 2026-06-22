""" Replay (Luo): reenvia uma mensagem legítima antiga, fora de ordem.

O atacante mantém um buffer das mensagens que passam e, ao disparar, reinjeta uma mensagem
ANTIGA (mesmo conteúdo) com timestamp atual. O tráfego original continua fluindo.
"""
import copy
from src import Msg

BUF_MAX = 300
REPLAY_AFTER = 50   # só começa a reenviar quando há histórico suficiente


def doAttack(curAttack, msgOrig, a, attacksSuc):
    if not hasattr(a, '_replay_buf'):
        a._replay_buf = []
    a._replay_buf.append((msgOrig.sender, msgOrig.receiver, dict(msgOrig.message)))
    if len(a._replay_buf) > BUF_MAX:
        a._replay_buf.pop(0)

    RetVal = {'msg': None, 'attackOngoing': False, 'dropMsg': False, 'counter': attacksSuc}

    if len(a._replay_buf) >= REPLAY_AFTER:
        sender, receiver, message = a._replay_buf[0]   # uma mensagem antiga
        m = Msg.Msg(sender, receiver, dict(message), msgOrig.timestamp + 0.0001)
        m.label = 'replay'
        a.writerQueue.put(m)
        RetVal['counter'] = attacksSuc + 1

    return RetVal
