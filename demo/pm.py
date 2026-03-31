import concore
import numpy as np

def pm(u):
    return u + 0.01

concore.default_maxtime(150)
concore.delay = 0.02

init_simtime_u = "[0.0, 0.0]"
init_simtime_ym = "[0.0, 0.0]"

ym = np.array([concore.initval(init_simtime_ym)], dtype=float).T

while concore.simtime < concore.maxtime:
    while concore.unchanged():
        u_raw = concore.read(1, "u", init_simtime_u)
        if isinstance(u_raw, str):
            try:
                u_raw = concore.safe_eval_with_numpy(u_raw)
            except:
                print("Failed to parse fallback u string:", u_raw)
                u_raw = [0.0]
        u = np.array([u_raw], dtype=float).T

    ym = pm(u)

    print(f"{concore.simtime}. u={u} ym={ym}")
    # Convert numpy arrays to standard Python lists for writing
    ym_list = [float(x) for x in ym.T[0]]
    concore.write(1, "ym", ym_list, delta=1)

print("retry=" + str(concore.retrycount))