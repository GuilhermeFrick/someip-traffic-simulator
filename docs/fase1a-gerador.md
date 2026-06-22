# Fase 1a — Gerador SOME/IP (sem container) + ground truth

Base: **SOME-IP_Generator** (Egomania) — Python3 + scapy + multiprocessing, usado por Alkhatib e
Luo. Vendorizado em `generator/`. Roda **local, sem Docker**, em modo **PCAP-only** (sem rede,
sem privilégios).

## Adaptações já feitas

1. **Compatibilidade de Python (3.12+).** O código usava `import imp` (removido no Python 3.12).
   Trocado por `importlib.util` em `generator/src/Attacker.py` (2 pontos). Roda em python3.13.
2. **Ground truth por pacote (instrumentação).** O gerador agora salva, junto do PCAP, um vetor
   de rótulos alinhado pacote-a-pacote. Três mudanças mínimas:
   - `src/Msg.py`: `Msg` ganha `label='normal'` por padrão.
   - `src/Attacker.py` (helper `doAttack`): ao injetar a mensagem maliciosa, marca
     `RetVal['msg'].label = curAttack.__name__` (o nome do módulo de ataque) — **chokepoint único**
     que rotula **qualquer** ataque, atual ou futuro.
   - `src/Generator.py` (writer): acumula pacotes+rótulos e grava de uma vez →
     `traces/<nome>.pcap` + `traces/<nome>.pcap.labels.npy`. (De quebra, a escrita em lote é mais
     rápida que o `wrpcap(append=True)` por pacote do original.)

## Saída

| Arquivo | Conteúdo |
|---|---|
| `traces/<nome>.pcap` | tráfego SOME/IP |
| `traces/<nome>.pcap.labels.npy` | rótulo (string) por pacote, **alinhado por índice** |

Rótulos: `'normal'` ou o **nome do ataque** (`wrongInterface`, `fakeResponse`, `fakeClientID`,
`sendErrorOnError`, `sendErrorOnEvent`, `disturbTiming`, …). Ataques de **drop**
(`deleteRequest`/`deleteResponse`) não geram pacote rotulado — são **ausência** (anomalia de
processo), o que é semanticamente correto.

## Validação

- Gera PCAP e o nosso extrator (`someip-ensemble-zeroday/src/someip.py`) **lê normalmente**
  (services/campos corretos).
- PCAP e rótulos **alinhados** (mesmo nº; índice → rótulo).

## Como rodar

```bash
cd generator
python3.13 start.py            # usa config/config.ini  (PCAP-only)
# saída: traces/trace_baseline.pcap (+ .labels.npy)
```
Config relevante (`config/config.ini`): `[Pcap] counter` = pacotes por cliente/método;
`[Attacks] counter` = frequência de ataque (menor = mais ataques); `attacks=` lista os módulos.

## Cobertura da taxonomia (módulos de ataque)

| Família | Origem | Módulo | Assinatura validada | Status |
|---|---|---|---|---|
| Anomalia de processo (req/resp ausente, erro evento/erro, interface errada, fake clientID/response, timing) | Alkhatib, SISSA | `deleteRequest/Response`, `sendErrorOnError/Event`, `wrongInterface`, `fakeClientID`, `fakeResponse`, `disturbTiming` | (já vinha) | ✅ |
| **DoS** | Kim, Luo | `dos.py` | rajada de notificações em serviço legítimo | ✅ |
| **Fuzzy** | Kim, Luo | `fuzzy.py` | service_ids aleatórios (0x2000–0x9000) + payload random | ✅ |
| **MITM** | Kim | `mitm.py` | serviço de **relay 0x100B** | ✅ |
| **Tamper** | Luo | `tamper.py` | payload adulterado (valor fora de distribuição) | ✅ |
| **Replay** | Luo | `replay.py` | reenvio de mensagem antiga | ✅ |
| **Falha de hardware** (safety) | SISSA | `hwfailure.py` | payload degradado (stuck-at-0 / saturado) + jitter, **Weibull** | ✅ |

**Taxonomia completa (7/7 famílias) coberta.**

Os 5 novos módulos **injetam** os pacotes maliciosos (com `label` próprio), mantendo o tráfego
original fluindo. Habilitamos payload controlável no `SomeIPPacket.createSomeIP` (1 linha) para
Tamper/Fuzzy/Replay terem semântica. Validação: as assinaturas batem por rótulo (dos→serviços
legítimos; fuzzy→IDs aleatórios; mitm→0x100B; tamper→payload fixo anômalo) e o nosso extrator lê
todos os pacotes.

## Próximos passos (Fase 1a)

1. **Topologia/config** fiel a um veículo (ECUs, serviços, IPs) e **geração dos datasets**
   (múltiplas *seeds*/cenários, balanceamento controlado).
2. Alimentar **Experimentos A e B** com os datasets rotulados (ground truth perfeito → melhor que
   a rotulagem heurística do Kim).
3. (Refinamento) modelo de *vida útil* da ECU para a falha de hardware (degradação contínua, além
   do evento de falha Weibull-governado da v1).
