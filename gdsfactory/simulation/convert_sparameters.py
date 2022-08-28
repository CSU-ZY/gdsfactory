import re

import numpy as np
import pandas as pd


def csv_to_numpy(filepath, port_map=None):
    """Converts a pandas CSV sparameters into a numpy array.

    Fundamental mode starts at 0.
    """
    df = pd.read_csv(filepath)
    s_headers = sorted({c[:-1] for c in df.columns if c.lower().startswith("s")})
    idxs = sorted({idx for c in s_headers for idx in _s_header_to_port_idxs(c)})

    if port_map is None:
        port_map = {f"o{i}@0": i for i in idxs}
    rev_port_map = {i: p for p, i in port_map.items()}
    assert len(rev_port_map) == len(
        port_map
    ), "Duplicate port indices found in port_map"

    s_map = {
        s: tuple(rev_port_map[i] for i in _s_header_to_port_idxs(s)) for s in s_headers
    }

    dfs = {
        s: df[["wavelengths", f"{s}m", f"{s}a"]]
        .copy()
        .rename(columns={f"{s}m": "magnitude", f"{s}a": "phase"})
        for s in s_map
    }

    S = dict(wavelengths=df["wavelengths"].values)
    for key, df in dfs.items():
        pm1, pm2 = s_map[key]
        (p1, m1), (p2, m2) = pm1.split("@"), pm2.split("@")
        name = f"{p1}@{m1},{p2}@{m2}"
        S[name] = df["magnitude"].values * np.exp(1j * df["phase"].values)

    return S


def _s_header_to_port_idxs(s):
    s = re.sub("[^0-9]", "", s)
    inp, out = (int(i) for i in s)
    return inp, out


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    import gdsfactory as gf

    filepath = gf.CONFIG["sparameters"] / "mmi1x2_d542be8a.csv"
    filepath = gf.CONFIG["sparameters"] / "mmi1x2_00cc8908.csv"
    filepath = gf.CONFIG["sparameters"] / "mmi1x2_1f90b7ca.csv"  # lumerical

    s = csv_to_numpy(filepath)
    plt.plot(s["wavelengths"], np.abs(s["o1@0,o2@0"]) ** 2)
    plt.plot(s["wavelengths"], np.abs(s["o1@0,o3@0"]) ** 2)
    plt.show()
