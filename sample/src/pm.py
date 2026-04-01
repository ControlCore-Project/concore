import concore
import numpy as np
import ast


def pm(u):
    return u + 0.01


concore.default_maxtime(150)
concore.delay = 0.02

init_simtime_u = "[0.0, 0.0]"
init_simtime_ym = "[0.0, 0.0]"

ym = np.array([concore.initval(init_simtime_ym)], dtype=np.float64).T

while concore.simtime < concore.maxtime:
    while concore.unchanged():
        u_raw = concore.read(1, "u", init_simtime_u)
        if isinstance(u_raw, str):
            try:
                u_raw = ast.literal_eval(u_raw)
            except (ValueError, SyntaxError):
                print("Failed to parse fallback u string:", u_raw)
                u_raw = [0.0]
        u = np.array([u_raw], dtype=np.float64).T

    ym = pm(u)

    print(f"{concore.simtime}. u={u} ym={ym}")
    concore.write(1, "ym", [float(x) for x in ym.T[0]], delta=1)

print("retry=" + str(concore.retrycount))
