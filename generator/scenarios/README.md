# Cenários (YAML) — uso recomendado

Em vez de editar `config.ini` + `devices.xml` + `services.xml` na mão, descreva o cenário
num único **YAML** e rode pela CLI:

```bash
pip install pyyaml scapy          # dependências
python run_scenario.py scenarios/normal.yaml              # gera o PCAP
python run_scenario.py scenarios/dos.yaml --dry-run       # só mostra o .ini gerado
```

Cada execução produz:
- `traces/<nome>.pcap` — o tráfego;
- `traces/<nome>.pcap.labels.npy` — **ground truth** por pacote (rótulo = nome do ataque, ou `normal`),
  alinhado ao índice do PCAP.

## Esquema do YAML

```yaml
seed: 42                      # semente do processo-pai (ver nota)
packets_per_client: 100       # pacotes por cliente/método
output:
  pcap: traces/normal.pcap    # arquivo de saída
  interface: lo               # (opcional) envia ao vivo numa interface
attack:
  types: [dos, fuzzy]         # módulos de src/attacks/ (vazio = só benigno)
  trigger_rate: 5000          # 1..N uniforme dispara um ataque
  interval_min_ms: 1
  interval_max_ms: 3
topology:                     # opcional — padrão usa os XML de config/
  devices: config/devices.xml
  services: config/services.xml
verbose: {client: false, server: false, attacker: false}
```

## Ataques disponíveis
`dos, fuzzy, mitm, replay, tamper, hwfailure, fakeClientID, wrongInterface,
disturbTiming, fakeResponse, sendErrorOnError, sendErrorOnEvent, deleteRequest,
deleteResponse` (= nomes dos módulos em `src/attacks/`).

## Exemplos prontos
- `normal.yaml` — só benigno (base / treino do "normal").
- `zeroday_train_known.yaml` — benigno + ataques **conhecidos** (dos, fuzzy, mitm).
- `zeroday_test_novel.yaml` — benigno + ataque **novo** (replay) → teste de zero-day.

Fluxo zero-day: treine o IDS no `*_train_known`, avalie a detecção do `*_test_novel`
(tipo nunca visto) — tudo no **mesmo domínio** (mesmo gerador), isolando "ataque novo"
de "domain shift".

## Nota de reprodutibilidade
O gerador roda clientes/servidores/atacante como **processos separados**
(`multiprocessing`), então `seed` no processo-pai **não** torna a saída bit-a-bit
determinística. O YAML torna a **configuração** reprodutível e versionável; o
determinismo por processo é um trabalho futuro.
