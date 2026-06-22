"""Teste de fechamento de ciclo: o IDS aprende/detecta os ataques do NOSSO gerador?

Fluxo: PCAP gerado + ground truth -> extrai features content_ext (byte-models ajustados no
tráfego normal gerado) -> XGBoost multiclasse 70/30 -> métricas + matriz de confusão.

Valida que o tráfego gerado é coerente e *aprendível*. Reproduzir:
  python validation/test_ids_on_generated.py
"""
from __future__ import annotations

import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from xgboost import XGBClassifier

# extrator/byte-models do repo someip-ensemble-zeroday
SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "someip-ensemble-zeroday", "src"))
sys.path.insert(0, SRC)
from scapy.utils import RawPcapReader   # noqa: E402
import someip                            # noqa: E402
import extract as _ex                    # noqa: E402
import extract_ext                       # noqa: E402
from bytemodel import ByteModel          # noqa: E402

PCAP = os.path.join(os.path.dirname(__file__), "..", "generator", "traces", "dataset_test.pcap")
LABELS = PCAP + ".labels.npy"
CONTENT_EXT = list(range(12)) + [12, 13, 14, 16]
PROCESS = {"deleteRequest", "deleteResponse", "sendErrorOnError", "sendErrorOnEvent",
           "wrongInterface", "fakeClientID", "fakeResponse", "disturbTiming"}


def map_label(s):
    if s == "normal":
        return "normal"
    return "process" if s in PROCESS else s   # dos/fuzzy/mitm/tamper/replay/failure


def main():
    labels_raw = np.load(LABELS)

    # 1) byte-models ajustados no tráfego NORMAL gerado
    models = {k: ByteModel(_ex.L[k]) for k in _ex.L}
    i = 0
    for raw, meta in RawPcapReader(PCAP):
        p = someip.parse(raw)
        if p is not None and labels_raw[i] == "normal":
            if p.pl_l4:
                models["l4"].update(p.pl_l4)
            if p.is_sd and p.pl_sd:
                models["sd"].update(p.pl_sd)
            elif p.pl_someip:
                models["someip"].update(p.pl_someip)
        i += 1
    for m in models.values():
        m.finalize()

    # 2) features content_ext (ground truth do gerador, não o rotulador por IP)
    X, _, _ = extract_ext.extract_file(PCAP, models, attack_type=0, benign_ips=set())
    X = np.asarray(X, dtype=np.float64)[:, CONTENT_EXT]
    assert len(X) == len(labels_raw), f"desalinhado {len(X)} vs {len(labels_raw)}"

    # 3) mapeia rótulos -> classes presentes (contíguas)
    mapped = np.array([map_label(s) for s in labels_raw])
    classes = [c for c in ["normal", "dos", "fuzzy", "mitm", "tamper", "replay", "failure", "process"]
               if (mapped == c).sum() >= 6]   # só classes com amostras suficientes p/ split
    cid = {c: i for i, c in enumerate(classes)}
    keep = np.isin(mapped, classes)
    X, mapped = X[keep], mapped[keep]
    y = np.array([cid[c] for c in mapped])
    print("classes:", {c: int((y == cid[c]).sum()) for c in classes})

    # 4) normaliza + split 70/30
    xmin, xmax = X.min(0), X.max(0)
    Xn = ((X - xmin) / np.where(xmax > xmin, xmax - xmin, 1.0)).astype(np.float32)
    X_tr, X_te, y_tr, y_te = train_test_split(Xn, y, test_size=0.30, random_state=0, stratify=y)

    # 5) XGBoost multiclasse
    clf = XGBClassifier(objective="multi:softprob", num_class=len(classes), n_estimators=300,
                        max_depth=6, learning_rate=0.3, tree_method="hist", n_jobs=-1,
                        eval_metric="mlogloss")
    clf.fit(X_tr, y_tr)
    y_pred = clf.predict(X_te)

    print("\n== IDS sobre tráfego GERADO ==")
    print(classification_report(y_te, y_pred, target_names=classes, digits=4))
    print("macro-F1:", round(f1_score(y_te, y_pred, average="macro"), 4))

    cm = confusion_matrix(y_te, y_pred)
    cmn = cm / cm.sum(1, keepdims=True)
    N = len(classes)
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(cmn, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(N)); ax.set_yticks(range(N))
    ax.set_xticklabels(classes, rotation=45, ha="right"); ax.set_yticklabels(classes)
    ax.set_xlabel("Predito"); ax.set_ylabel("Verdadeiro")
    ax.set_title("IDS sobre tráfego gerado (matriz de confusão)")
    for a in range(N):
        for b in range(N):
            ax.text(b, a, f"{cmn[a,b]*100:.0f}", ha="center", va="center", fontsize=8,
                    color="white" if cmn[a, b] > 0.5 else "black")
    fig.colorbar(im, fraction=0.046, pad=0.04)
    os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
    out = os.path.join(os.path.dirname(__file__), "results", "ids_sobre_gerado.png")
    plt.tight_layout(); plt.savefig(out, dpi=130); plt.close()
    print("matriz salva em:", out)


if __name__ == "__main__":
    main()
