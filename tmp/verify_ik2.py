#!/usr/bin/env python3
# 定位公式的有效区域：假设是 y_leg < 0 才成立
import math
import numpy as np

def latex_q1(x, y, L1, L2):
    r = math.sqrt(x*x + y*y)
    alpha = math.acos((L1*L1 - L2*L2 + x*x + y*y) / (2*L1*r))
    beta = math.acos(x/r)
    return math.pi/2 - alpha - beta

def latex_q2(x, y, L1, L2):
    r = math.sqrt(x*x + y*y)
    alpha = math.acos((L1*L1 - L2*L2 + x*x + y*y) / (2*L1*r))
    beta = math.acos(x/r)
    return (math.atan2(y + L1*math.sin(alpha + beta), x - L1*math.cos(alpha + beta))
            + alpha + beta)

def fk(q1, q2, L1, L2):
    return (L1*math.sin(q1) + L2*math.sin(q1 + q2),
            -L1*math.cos(q1) - L2*math.cos(q1 + q2))

def wrap(a):
    return (a + math.pi) % (2*math.pi) - math.pi

def trial(L1, L2, q2lo, q2hi, ysel, n=20000, seed=1):
    rng = np.random.default_rng(seed)
    ok = bad = skip = 0
    worst = 0.0
    for _ in range(n):
        q1t = rng.uniform(-math.pi, math.pi)
        q2t = rng.uniform(q2lo, q2hi)
        px, py = fk(q1t, q2t, L1, L2)
        if ysel == '<0' and py >= 0: skip += 1; continue
        if ysel == '>0' and py <= 0: skip += 1; continue
        try:
            a = latex_q1(px, py, L1, L2); b = latex_q2(px, py, L1, L2)
        except ValueError:
            bad += 1; continue
        e1 = abs(wrap(a - q1t)); e2 = abs(wrap(b - q2t))
        e = max(e1, e2)
        if e < 1e-9: ok += 1
        else:
            bad += 1; worst = max(worst, e)
    tot = ok + bad
    frac = 100.0*ok/tot if tot else 0.0
    print(f"  L1={L1:<5} q2∈({q2lo:+.0f},{q2hi:+.0f})  y{ysel:<3}  "
          f"命中 {frac:6.2f}%  (n={tot}, 跳过{skip})  最差残差={math.degrees(worst):7.2f}°")

print("=== 按 y_leg 符号 与 肘分支 分层统计 FK->IK 命中率 ===")
for (L1, L2) in [(0.2, 0.2), (0.2, 0.15), (1.0, 1.0)]:
    for ysel in ['<0', '>0']:
        for (lo, hi) in [(0.0, math.pi), (-math.pi, 0.0)]:
            trial(L1, L2, lo, hi, ysel)
    print()

print("=== 有效区间（y<0, q2>0）内的精度 ===")
L1 = L2 = 0.2
rng = np.random.default_rng(7)
worst = 0.0
for _ in range(200000):
    q1t = rng.uniform(-math.pi, math.pi); q2t = rng.uniform(0, math.pi)
    px, py = fk(q1t, q2t, L1, L2)
    if py >= 0: continue
    try:
        a = latex_q1(px, py, L1, L2); b = latex_q2(px, py, L1, L2)
    except ValueError:
        continue
    worst = max(worst, abs(wrap(a-q1t)), abs(wrap(b-q2t)))
print(f"  max 角度残差 = {math.degrees(worst):.3e}°")

print("\n=== 边界：y_leg = 0 附近 ===")
for (px, py) in [(0.3, -0.2), (-0.3, -0.2), (0.4, 0.0), (0.0, -0.4), (0.0, 0.4)]:
    try:
        a = latex_q1(px, py, L1, L2); b = latex_q2(px, py, L1, L2)
        bx, by = fk(a, b, L1, L2)
        print(f"  target=({px:+.2f},{py:+.2f})  q1={math.degrees(a):+8.3f}°  q2={math.degrees(b):+8.3f}°  "
              f"FK回代误差={math.hypot(bx-px, by-py):.2e}")
    except ValueError:
        print(f"  target=({px:+.2f},{py:+.2f})  acos 越界")
