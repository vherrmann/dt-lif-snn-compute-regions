import numpy as np
from itertools import islice
import matplotlib.pyplot as plt


def get_nth_result(generator, n):
    return next(islice(generator, n, n + 1))


def first_layer(u0, β, W, b, V, ϑ, x):
    u = u0
    s = np.zeros_like(u0)
    while True:
        u = β * u + W @ x + b + V @ s - ϑ * s
        s = (u >= ϑ).astype(float)
        yield u, s


def run_with(V, x, W=[[1, 0], [0, 1]], b=None, ϑ=1, u0=None, β=1):
    if u0 is None:
        u0 = np.zeros_like(x)
    if b is None:
        b = np.zeros_like(x)
    if isinstance(W, list):
        W = np.array(W)
    if isinstance(V, list):
        V = np.array(V)
    if isinstance(b, list):
        b = np.array(b)
    if isinstance(x, list):
        x = np.array(x)
    if isinstance(u0, list):
        u0 = np.array(u0)

    for u, s in first_layer(u0, β, W, b, V, ϑ, x):
        print("Membrane potential:", u)
        print("Spikes:", s)
        input()


def spiketrain_to_nextspike(spiketrain, V, ϑ=1, u0=None):
    # we assume b=0 and W=𝟙
    if u0 is None:
        u0 = np.zeros_like(V[0])
    if isinstance(u0, list):
        u0 = np.array(u0)
    lower_bounds = [[] for _ in range(len(u0))]
    upper_bounds = [[] for _ in range(len(u0))]
    stW0 = np.append([[0, 0]], spiketrain, axis=0)
    one_n = np.ones_like(u0)
    for t, spike in enumerate(stW0):
        if t == 0:
            continue
        # we compute x, so that u(t) = ϑ
        stSum = np.sum(stW0[:t], axis=0)
        xCut = (ϑ * one_n - u0 - (V @ stSum - ϑ * stSum)) / t
        for i, x in enumerate(xCut):
            if spike[i] == 1.0:
                lower_bounds[i].append(x)
            else:
                upper_bounds[i].append(x)
    # print("Lower bounds:", lower_bounds)
    # print("Upper bounds:", upper_bounds)
    infimums = np.array([max(lb) if lb else -np.inf for lb in lower_bounds])
    # print("Highest lower bound:", infimums)
    supremums = np.array([min(ub) if ub else np.inf for ub in upper_bounds])
    # print("Lowest upper bound:", supremums)

    def get_continuation_us(x):
        return list(
            islice(
                first_layer(
                    u0=u0, β=1, W=[[1, 0], [0, 1]], b=np.zeros_like(u0), V=V, ϑ=ϑ, x=x
                ),
                0,
                len(spiketrain) + 1,
            )
        )

    check_if_spikes_fit = lambda stRes: spiketrain == list(
        map(lambda x: list(x[1]), stRes[:-1])
    )

    # The spike trains at infimums might not be correct,
    # since we can't properly compute with -∞.
    # Also the supremums are probably not correct,
    # since they should be the highest value that just produces another spike train.
    def find_actual_possible(x, other):
        y = np.copy(x)
        while np.all((x < other) == (y < other)) and np.all((other < x) == (other < y)):
            stRes = get_continuation_us(x)
            if check_if_spikes_fit(stRes):
                return stRes
            x = np.nextafter(x, other)
            print(f"trying next {x}")
        else:
            raise ValueError(f"no possible next value for {x} with other {other}")

    # print(f"checking spikes for infimums")
    # FIXME: wrong for negative weights in V
    stInf = find_actual_possible(infimums, supremums)
    uInf, sInf = stInf[-1]

    # print(f"checking spikes for supremums")
    stSup = find_actual_possible(supremums, infimums)
    uSup, sSup = stSup[-1]

    assert check_if_spikes_fit(stSup)
    if np.array_equal(sInf, sSup):
        # print(f"next spikes are fixed to {sInf}")
        return {"next": [sInf], "infs": infimums, "sups": supremums}
    else:
        # print(f"next spikes might be {sInf} or {sSup}")
        return {"next": [sInf, sSup], "infs": infimums, "sups": supremums}


def play(startSpikes, V, ϑ, u0):
    spiketrain = [startSpikes]
    forcedp = [False]
    while True:
        result = spiketrain_to_nextspike(spiketrain, V, ϑ, u0)
        forcedp.append(len(result["next"]) == 1)
        print("Infimums:", result["infs"])
        print("Supremums:", result["sups"])
        print(
            "Spikes:\n"
            + "\n".join(
                map(
                    lambda n: "".join(map(lambda x: "1" if x == 1 else "0", n)),
                    zip(*spiketrain),
                )
            )
            + "\n"
            + "".join(["^" if f else " " for f in forcedp])
        )
        print("Possible next spikes:", result["next"])
        choice = input("Choose next spikes (or 'q' to quit): ")
        if choice.lower() == "q":
            break
        try:
            next_spikes = result["next"][int(choice)]
            spiketrain.append(list(next_spikes))
        except (ValueError, IndexError):
            print("Invalid input, please enter q or an integer.")


def plot(V, n, lower=-1, upper=1, steps=100):
    x = np.linspace(lower, upper, steps)
    y = np.linspace(lower, upper, steps)

    X, Y = np.meshgrid(x, y)

    points = np.stack([X.ravel(), Y.ravel()], axis=1)
    g = lambda p: list(
        islice(
            first_layer(
                u0=np.zeros_like(p),
                β=1,
                W=[[1, 0], [0, 1]],
                b=np.zeros_like(p),
                V=V,
                ϑ=1,
                x=p,
            ),
            0,
            n,
        )
    )
    Z = np.array([g(p) for p in points])
    Z = Z.reshape(X.shape)

    plt.figure(figsize=(6, 6))
    plt.pcolormesh(X, Y, Z, cmap="Set2", shading="auto")
    plt.colorbar(label="Group")
    plt.title("Grouped Grid Function Output")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.axis("equal")
    plt.show()
