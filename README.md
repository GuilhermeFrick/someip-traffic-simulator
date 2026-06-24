# SOME/IP Traffic Simulator — planejamento

Projeto para construir um **gerador/simulador de tráfego SOME/IP** (Automotive Ethernet) capaz de
produzir tráfego **normal + ataques rotulados**, com *ground truth*, balanceamento controlável e
**ataques inéditos sob demanda** — o que os datasets estáticos existentes não permitem.

Construído em **duas fases**:

1. **Fase 1 — sem CARLA (leve, roda em CPU):** sinais de uma dinâmica simples / traces gravados →
   **vsomeip** (pilha SOME/IP real) → tráfego com payload de significado real + nós atacantes.
2. **Fase 2 — com CARLA + Autoware (realismo de sensores/percepção, exige GPU):** cenários de
   condução realistas alimentando os serviços SOME/IP.

📄 **Comece por:** [`docs/contexto-motivacao.md`](docs/contexto-motivacao.md) — por que estamos
construindo o simulador, o que os experimentos mostraram (em especial o **Experimento B**) e o
roadmap das duas fases.

## Estado atual (Fase 1a — gerador, sem container)

O gerador da Fase 1a já está implementado em [`generator/`](generator/), rodando em CPU e
produzindo **PCAP + ground truth por pacote**. Cobre **toda a taxonomia (7/7 famílias)**:
DoS, Fuzzy, MITM, Tamper, Replay, anomalias de processo e falha de hardware (Weibull).
Detalhes em [`docs/fase1a-gerador.md`](docs/fase1a-gerador.md).

## Como usar

Todo o uso é a partir de `generator/`, dirigido por um **único arquivo YAML** por cenário
(nada de editar `config.ini`/XML na mão). Detalhes do esquema em
[`generator/scenarios/README.md`](generator/scenarios/README.md).

### 1. Requisitos
```bash
cd generator
pip install pyyaml scapy
```

### 2. Gerar um cenário
```bash
python run_scenario.py scenarios/fuzzy.yaml          # gera o tráfego
python run_scenario.py scenarios/fuzzy.yaml --dry-run  # só mostra o config gerado, sem rodar
```
Cada execução produz, em `traces/`:
- `<nome>.pcap` — o tráfego SOME/IP;
- `<nome>.pcap.labels.npy` — **ground truth por pacote** (rótulo = nome do ataque, ou `normal`),
  alinhado ao índice do PCAP.

Ver o que foi gerado:
```bash
python -c "import numpy as np,collections; print(collections.Counter(np.load('traces/fuzzy.pcap.labels.npy',allow_pickle=True).tolist()))"
```

### 3. Configurar um cenário (esquema do YAML)
```yaml
seed: 42                      # semente do processo-pai (ver nota de reprodutibilidade)
packets_per_client: 100       # volume de tráfego (pacotes por cliente/método)
output:
  pcap: traces/meu_cenario.pcap
  interface: lo               # (opcional) também envia ao vivo numa interface
attack:
  types: [dos, fuzzy]         # módulos de ataque (lista vazia [] = só benigno)
  trigger_rate: 50            # prob. 1/N por mensagem de disparar -> MENOR = MAIS ataques
  interval_min_ms: 1          # intervalo de resposta do atacante
  interval_max_ms: 3
topology:                     # (opcional) padrão usa os XML de config/
  devices: config/devices.xml
  services: config/services.xml
verbose: {client: false, server: false, attacker: false}
```

**Ataques disponíveis** (`attack.types`): `dos`, `fuzzy`, `mitm`, `replay`, `tamper`,
`hwfailure`, `fakeClientID`, `wrongInterface`, `disturbTiming`, `fakeResponse`,
`sendErrorOnError`, `sendErrorOnEvent`, `deleteRequest`, `deleteResponse`
(= nomes dos módulos em [`generator/src/attacks/`](generator/src/attacks/)).

**Ajustar o volume de ataque:** `trigger_rate` é a probabilidade `1/N` por mensagem.
`50` dispara bastante; `2000` quase nunca. Para uma fração tipo-Kim (~12% de ataque),
suba o `trigger_rate` até a contagem de ataque no ground truth bater.

**Cenários prontos** (`scenarios/`): `normal` (só benigno), `dos`, `fuzzy`, e o par de
zero-day `zeroday_train_known` (dos/fuzzy/mitm) × `zeroday_test_novel` (replay).

### 4. Testar o tráfego gerado (no IDS)
A avaliação fica no repositório **`someip-ids-multiclass-contentext`** (carrega o PCAP, extrai
features `content_ext`, treina/testa e gera métricas + matriz de confusão):
```bash
cd ../../someip-ids-multiclass-contentext
pip install scapy xgboost scikit-learn matplotlib
# 1 PCAP: métricas + matriz de confusão (70/30)
python eval_pcap.py "<...>/generator/traces/fuzzy.pcap"
# zero-day: treina nos conhecidos, mede detecção do ataque NOVO
python eval_pcap.py "<...>/traces/zeroday_train_known.pcap" --test-pcap "<...>/traces/zeroday_test_novel.pcap" --binary
```
Ou, interativo, o notebook `notebooks/06-testar-pcap-gerado.ipynb` (mostra tudo inline, roda no Colab).

> **Nota de reprodutibilidade:** o gerador roda clientes/servidores/atacante como **processos
> separados** (`multiprocessing`), então `seed` no pai **não** torna a saída bit-a-bit
> determinística. O YAML torna a **configuração** reprodutível e versionável; determinismo por
> processo é trabalho futuro.

## Licença e atribuição

O diretório [`generator/`](generator/) é **derivado** do projeto
[**SOME-IP_Generator** (Egomania)](https://github.com/Egomania/SOME-IP_Generator), usado pelos
trabalhos de Alkhatib (2021) e Luo (2023), licenciado sob **GNU AGPL-3.0**. Por se tratar de obra
derivada, **este repositório também é distribuído sob AGPL-3.0** (ver [`LICENSE`](LICENSE)).

Nossas modificações sobre o original:
- compatibilidade com Python 3.12+ (`imp` → `importlib`);
- **ground truth por pacote** (rótulo verdadeiro salvo junto do PCAP);
- payload controlável no `SomeIPPacket`;
- **novos módulos de ataque**: `dos`, `fuzzy`, `mitm`, `tamper`, `replay`, `hwfailure`.

## Repositórios relacionados
- `someip-ensemble-zeroday` — extração de features, IDS multiclasse, zero-day, two-layer.
- `someip-ids-benchmark` — terreno comum de avaliação (Experimentos A e B).
- Reproduções: Alkhatib (RNN), Luo (multi-GRU), SISSA (LSTM+atenção), Kim (XGBoost).
