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
