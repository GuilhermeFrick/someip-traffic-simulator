# Por que construir um simulador de tráfego SOME/IP

## 1. Contexto em alto nível

Carros modernos são, por dentro, uma rede de computadores (ECUs) que conversam entre si. Boa
parte dessa conversa usa o protocolo **SOME/IP** sobre Automotive Ethernet. Como o SOME/IP foi
projetado para *funcionar*, não para *ser seguro*, quem entra na rede pode injetar mensagens
maliciosas. Daí a necessidade de um **IDS** (sistema de detecção de intrusão) — um vigia que
observa o tráfego e aponta o que é ataque.

Nossa pesquisa reproduziu quatro IDS de referência (Alkhatib 2021, Luo 2023, SISSA/Liu 2024,
Kim 2026), construiu detectores próprios e os comparou de forma justa. **Este documento explica
por que o próximo passo natural é um simulador de tráfego.**

## 2. O que os experimentos mostraram (e como levam ao simulador)

### 2.1 A detecção de ataque CONHECIDO já está resolvida — e o gargalo são os dados
- Reconstruímos do zero o pipeline de dados do Kim e **batemos os números dele** (diferença de
  7 pacotes em 14,2 milhões). Isso deu confiança total e, de quebra, rótulos por **tipo** de
  ataque (que o autor não publicou).
- Descobrimos que **o que decide o desempenho são as *features* (o que se mede), não a
  complexidade do modelo**: trocando as features certas, um modelo simples saltou de medíocre
  (macro-F1 0,78) para quase perfeito (**0,99**) — e ensembles complexos (LCCDE) **não** melhoraram.
- Mostramos também uma armadilha: *features* baseadas em **identificadores de cabeçalho** inflam
  o desempenho no conhecido mas **pioram a detecção do desconhecido** (overfitting).

### 2.2 O Experimento B — a comparação justa (o que fizemos por último)
O problema histórico da área: cada trabalho reporta ~99%, mas **em datasets, taxonomias e
métricas diferentes** — não dá para saber qual é realmente melhor. Construímos um **terreno
comum** (`someip-ids-benchmark`): mesma representação de *features*, mesmos rótulos, mesmo split,
mesmos pacotes-alvo. Aí re-treinamos **as quatro arquiteturas** lado a lado:

| Arquitetura | macro-F1 (terreno comum) | tempo de treino |
|---|---:|---:|
| **XGBoost** (features comportamentais) | **0,9934** | 11 s |
| Luo — multi-GRU | 0,9436 | 158 s |
| SISSA — LSTM + atenção | 0,9224 | 120 s |
| Alkhatib — RNN | 0,8849 | 33 s |

**Resultado:** no mesmo terreno, o modelo **mais simples (XGBoost) vence com folga e é 10–15×
mais rápido** que os modelos sequenciais (RNN/GRU/LSTM). Ou seja, *features* comportamentais +
*boosting* são a base mais forte e barata — a complexidade arquitetural não compensa.

> **Antes do B**, tentamos o Experimento A (transferência: jogar os modelos já treinados num
> tráfego novo). Ele revelou duas coisas: (a) os modelos do Kim **transferem mal** para tráfego
> que não viram (*domain shift*); (b) **não dá nem para comparar** Alkhatib/Luo/SISSA por
> transferência, porque cada um vive numa **representação e numa taxonomia incompatíveis**. Foi
> isso que motivou o B (re-treinar todos no terreno comum) — e motiva o simulador (gerar o
> tráfego comum onde a comparação é possível e justa).

### 2.3 O que continua em aberto — e por que é um problema de DADOS
1. **Zero-day (ataque desconhecido):** o melhor que conseguimos é ~60% de detecção, muito
   desigual — porque alguns ataques **se disfarçam de tráfego legítimo**. Não dá para estudar
   isso bem com um dataset que tem poucos tipos de ataque, capturados uma única vez.
2. **Generalização / domain shift:** os datasets são **estáticos e únicos**; não há como testar
   se um modelo aguenta cenários, veículos e condições diferentes.
3. **Cobertura incompleta da taxonomia:** o dataset do Kim só tem DoS/Fuzzy/MITM. Tamper, Replay,
   anomalias de processo e falha de hardware (dos outros trabalhos) **nem existem** nele para
   testar.

**A conclusão converge:** o limite não está mais no modelo, está nos **dados**. Precisamos de uma
fonte de tráfego **dinâmica, diversa, rotulada e controlável** — um **simulador**.

## 3. O que o simulador resolve

- **Ground truth perfeito** (sabemos exatamente o que é ataque, sem rotulagem heurística).
- **Balanceamento e cenários controláveis** (avaliação honesta, sem o desbalanceamento artificial
  dos datasets atuais).
- **Cobertura da taxonomia completa** (gerar todas as famílias de ataque dos 4 trabalhos).
- **Ataques inéditos sob demanda** → finalmente um teste sério de **zero-day**.
- **Payload com significado real** (estilo Luo) → habilita Tamper/Replay, que exigem semântica.
- Alimenta tanto o **Experimento A** (transferência) quanto o **B** (benchmark justo) com dados
  ricos.

## 4. Cobertura de ataques por fase

| Família | Origem | Fase 1 (sem CARLA) | Fase 2 (CARLA+Autoware) |
|---|---|:--:|:--:|
| DoS (flood) | Kim, Luo | ✅ | ✅ |
| Fuzzy (IDs/payload aleatórios) | Kim, Luo | ✅ | ✅ |
| MITM (relay/withdraw/injeção) | Kim | ✅ | ✅ |
| Tamper (adulterar payload) | Luo | ✅ (payload de dinâmica simples) | ✅ (payload de sensores reais) |
| Replay (reenvio) | Luo | ✅ | ✅ |
| Anomalia de processo (req sem resp, etc.) | Alkhatib, SISSA | ✅ (via vsomeip) | ✅ |
| Falha de hardware (safety) | SISSA | ✅ (ECU degradada, Weibull) | ✅ |

A peça que destrava Tamper/Replay e anomalia de processo já na Fase 1 é o **vsomeip** (pilha
SOME/IP real, com máquina de estados request/response e payload com significado).

## 5. Roadmap das duas fases

### Fase 1 — sem CARLA (leve, CPU)
```
sinais (dinâmica simples / traces gravados) → vsomeip (ECUs publish/subscribe, req/resp)
        → tráfego SOME/IP real → nó(s) atacante(s) → captura (tcpdump) → PCAP + ground truth
```
- **Não precisa de GPU** — roda em CPU comum.
- Entrega a maior parte da taxonomia (ver §4).
- Reaproveita todo o pipeline de extração/IDS que já temos.

**Passos:** (1) PoC vsomeip (2–3 ECUs trocando eventos) → captura → roda nosso extrator/IDS;
(2) adicionar request/response e service discovery corretos; (3) injetar os ataques; (4) gerar
datasets rotulados e re-rodar Experimentos A e B sobre eles.

### Fase 2 — com CARLA + Autoware (realismo, GPU)
```
CARLA (cenário + sensores) → Autoware (percepção/planejamento, ROS 2)
        → mapeamento de serviços → vsomeip → tráfego SOME/IP realista → ataques → PCAP
```
- **Exige GPU NVIDIA** (~6–8 GB) — de preferência máquina de laboratório/HPC.
- Acrescenta **realismo de sensores e semântica de payload de verdade** (percepção dirige os
  valores), elevando a fidelidade de Tamper/Replay e dos cenários.

> **Por que CARLA é opcional e tardio:** o objetivo central (tráfego SOME/IP com payload
> significativo + protocolo correto) já é atingível na Fase 1, em CPU. CARLA entra só quando
> quisermos realismo de percepção / Autoware no loop — então o custo de GPU é adiado.

## 6. Hardware

| Fase | GPU | RAM | Observação |
|---|---|---|---|
| Fase 1 (vsomeip) | **não precisa** | 8–16 GB | roda no notebook atual |
| Fase 2 (CARLA+Autoware) | **NVIDIA 6–8 GB** | 16–32 GB | máquina de laboratório / nuvem GPU |

## 7. Em uma frase

Os experimentos mostraram que **o modelo já não é o gargalo — os dados são**. O simulador é o que
nos dá dados dinâmicos, rotulados e com ataques inéditos para atacar o problema que sobra
(zero-day e generalização). Começamos **leve, sem CARLA** (CPU + vsomeip), e só depois subimos
para **CARLA + Autoware** quando o realismo de sensores justificar o custo de GPU.
