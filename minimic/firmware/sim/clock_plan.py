"""Liebling (R3MIC) F1: planos de clock do RP2040 para o PDM (3.072 MHz) e para o USB (48 MHz).

Regras do PLL do RP2040 (datasheet): ref = xtal/refdiv >= 5 MHz, VCO = ref*fb em 750..1600 MHz,
fb 16..320, dois pos-divisores 1..7.   python clock_plan.py
"""
import itertools


def plans(xtal, target, tol, vco=(750.0, 1600.0)):
    out = []
    for refdiv in range(1, 64):
        ref = xtal / refdiv
        if ref < 5.0:
            continue
        for fb in range(16, 321):
            v = ref * fb
            if not vco[0] <= v <= vco[1]:
                continue
            for p1, p2 in itertools.product(range(1, 8), repeat=2):
                if p1 < p2:
                    continue
                f = v / (p1 * p2)
                if abs(f / target - 1) <= tol:
                    out.append((f, refdiv, fb, v, p1, p2))
    return sorted(out, key=lambda t: abs(t[0] - target))


def pdm_plans(xtal, lo=100.0, hi=200.0):
    """sys em MHz tal que sys/3.072 e inteiro (divisor inteiro do PIO para qualquer
    multiplo) -> erro do PDM = 0."""
    res = []
    for refdiv in range(1, 64):
        ref = xtal / refdiv
        if ref < 5.0:
            continue
        for fb in range(16, 321):
            v = ref * fb
            if not 750.0 <= v <= 1600.0:
                continue
            for p1, p2 in itertools.product(range(1, 8), repeat=2):
                if p1 < p2:
                    continue
                f = v / (p1 * p2)
                if lo <= f <= hi:
                    n = f / 3.072
                    if abs(n - round(n)) < 1e-9:
                        res.append((f, round(n), refdiv, fb, v, p1, p2))
    return sorted(res)


if __name__ == "__main__":
    for xt in (12.0, 12.288):
        print("=== cristal %.3f MHz" % xt)
        u = plans(xt, 48.0, 0.0025)
        print(" USB 48 MHz (+-0.25 %%): melhor %s" % ((u[0] if u else None),))
        p = pdm_plans(xt)
        print(" sys 100..200 MHz com sys/3.072 inteiro: %s" % (p[:6] if p else "nenhum"))
        # sys com erro de PDM pequeno e USB exato (+-0.25%)
        near = plans(xt, 3.072 * 48, 0.002)
        print(" sys perto de 147.456 (=3.072*48), erro <= 0.2 %%: %s" % (near[:3],))
