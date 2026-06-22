"""CLI do simulador SOME/IP — dirige a geração por um único arquivo YAML.

Em vez de editar config.ini + devices.xml + services.xml na mão, você descreve o
cenário num YAML e roda:

    python run_scenario.py scenarios/normal.yaml
    python run_scenario.py scenarios/dos.yaml --dry-run     # só imprime o .ini gerado

Saída: <output.pcap> + <output.pcap>.labels.npy (ground truth alinhado ao PCAP).

Esquema do YAML (campos opcionais usam o padrão entre colchetes):

    seed: 42                      # semente do processo-pai [None]
    packets_per_client: 100       # pacotes por cliente/método [100]
    output:
      pcap: traces/normal.pcap    # arquivo de saída [traces/scenario.pcap]
      interface: lo               # (opcional) envia ao vivo numa interface
    attack:
      types: [dos, fuzzy]         # módulos de src/attacks/ (vazio = só benigno) [[]]
      trigger_rate: 5000          # 1..N uniforme dispara um ataque [5000]
      interval_min_ms: 1          # intervalo mín. de resposta do atacante [1]
      interval_max_ms: 3          # intervalo máx. [3]
    topology:
      devices: config/devices.xml   # [config/devices.xml]
      services: config/services.xml # [config/services.xml]
    verbose: {client: false, server: false, attacker: false}

Ataques disponíveis (= nomes dos módulos em src/attacks/):
  dos, fuzzy, mitm, replay, tamper, hwfailure, fakeClientID, wrongInterface,
  disturbTiming, fakeResponse, sendErrorOnError, sendErrorOnEvent,
  deleteRequest, deleteResponse

NOTA de reprodutibilidade: o gerador roda clientes/servidores/atacante como
processos separados (multiprocessing), então `seed` no pai NÃO torna a saída
bit-a-bit determinística. O YAML torna a CONFIGURAÇÃO reprodutível/versionável;
determinismo por processo é um trabalho futuro.
"""
from __future__ import annotations

import argparse
import configparser
import os
import sys

try:
    import yaml
except ImportError:
    sys.exit("Falta PyYAML. Instale com:  pip install pyyaml")


VALID_ATTACKS = {
    "dos", "fuzzy", "mitm", "replay", "tamper", "hwfailure",
    "fakeClientID", "wrongInterface", "disturbTiming", "fakeResponse",
    "sendErrorOnError", "sendErrorOnEvent", "deleteRequest", "deleteResponse",
}


def compile_to_ini(scn: dict, ini_path: str) -> str:
    """Traduz o dicionário do YAML para um config.ini que o Generator entende.
    Retorna o caminho do PCAP de saída."""
    topo = scn.get("topology") or {}
    out = scn.get("output") or {}
    atk = scn.get("attack") or {}
    vb = scn.get("verbose") or {}

    pcap = out.get("pcap", "traces/scenario.pcap")
    os.makedirs(os.path.dirname(pcap) or ".", exist_ok=True)

    types = atk.get("types") or []
    desconhecidos = [t for t in types if t not in VALID_ATTACKS]
    if desconhecidos:
        raise SystemExit(f"Ataque(s) desconhecido(s): {desconhecidos}\n"
                         f"Válidos: {sorted(VALID_ATTACKS)}")

    C = configparser.ConfigParser()
    C["Files"] = {
        "deviceFile": topo.get("devices", "config/devices.xml"),
        "serviceFile": topo.get("services", "config/services.xml"),
    }
    C["Pcap"] = {"file": pcap, "counter": str(scn.get("packets_per_client", 100))}
    if out.get("interface"):
        C["Pcap"]["interface"] = out["interface"]
    C["Attacks"] = {
        "counter": str(atk.get("trigger_rate", 5000)),
        "min": str(atk.get("interval_min_ms", 1)),
        "max": str(atk.get("interval_max_ms", 3)),
        "attacks": ", ".join(types),
    }
    C["Verbose"] = {k: str(vb.get(k, False)).lower() for k in ("client", "server", "attacker")}

    with open(ini_path, "w", encoding="utf-8") as f:
        C.write(f)
    return pcap


def main() -> None:
    ap = argparse.ArgumentParser(description="Roda um cenário SOME/IP a partir de um YAML.")
    ap.add_argument("scenario", help="caminho do arquivo .yaml do cenário")
    ap.add_argument("--dry-run", action="store_true", help="só gera/imprime o .ini, não executa")
    args = ap.parse_args()

    with open(args.scenario, encoding="utf-8") as f:
        scn = yaml.safe_load(f) or {}

    ini_path = "config/_scenario.ini"
    pcap = compile_to_ini(scn, ini_path)

    print(f"Cenário : {args.scenario}")
    print(f"Ataques : {scn.get('attack', {}).get('types') or '(só benigno)'}")
    print(f"Saída   : {pcap}  (+ {pcap}.labels.npy)")
    print(f"Config  : {ini_path}")

    if args.dry_run:
        print("\n--- .ini gerado (dry-run, nada foi executado) ---")
        with open(ini_path, encoding="utf-8") as f:
            print(f.read())
        return

    if scn.get("seed") is not None:
        import random
        random.seed(scn["seed"])

    from src import Generator
    Generator.start(ini_path)


if __name__ == "__main__":
    main()
