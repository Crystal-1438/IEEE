#!/usr/bin/env python3
# 用第一性原理独立重推 2 连杆逆解，与 MATLAB 公式对照
import math
import numpy as np

# ---- 待验证：MATLAB 转写公式 ----
def formula_q1(x, y, L1, L2):
    r = math.hypot(x, y)
    alpha = math.acos((L1*L1 - L2*L2 + x*x + y*y) / (2*L1*r))
    beta = math.acos(x/r)
    return math.pi/2 - alpha - beta

def formula_q2(x, y, L1, L2):
    r = math.hypot(x, y)
    alpha = math.acos((L1*L1 - L2*L2 + x*x + y*y) / (2*L1*r))
    beta = math.acos(x/r)
    return (math.atan2(y + L1*math.sin(alpha + beta), x - L1*math.cos(alpha + beta))
            + alpha + beta)

# ---- 独立重推：由 FK  x=L1 sin q1 + L2 sin(q1+q2),  y=-L1 cos q1 - L2 cos(q1+q2)
#      r^2 = L1^2 + L2^2 + 2 L1 L2 cos q2        (余弦定理)
#      基 (x, -y) 下，q1 即目标极角 minus 三角形顶角
def derived_q1(x, y, L1, L2):
    r = math.hypot(x, y)
    return math.atan2(x, -y) - math.acos((r*r + L1*L1 - L2*L2) / (2*L1*r))

def derived_q2(x, y, L1, L2):
    r = math.hypot(x, y)
    return math.acos((r*r - L1*L1 - L2*L2) / (2*L1*L2))

def fk(q1, q2, L1, L2):
    return (L1*math.sin(q1) + L2*math.sin(q1+q2),
            -L1*math.cos(q1) - L2*math.cos(q1+q2))

def wrap(a):
    return (a + math.pi) % (2*math.pi) - math.pi

print("=== 公式 vs 第一性原理重推（域内 y_leg<0, 肘分支 q2>0） ===")
rng = np.random.default_rng(11)
for (L1, L2) in [(0.2, 0.2), (0.2, 0.15), (0.3, 0.25), (1.0, 1.0)]:
    n = ok = 0
    w1 = w2 = 0.0
    for _ in range(50000):
        q1t = rng.uniform(-math.pi, math.pi)
        q2t = rng.uniform(1e-6, math.pi - 1e-6)
        px, py = fk(q1t, q2t, L1, L2)
        if py >= -1e-3:            # 只取足端在髋下方的工况
            continue
        n += 1
        try:
            d1 = abs(wrap(formula_q1(px, py, L1, L2) - derived_q1(px, py, L1, L2)))
            d2 = abs(wrap(formula_q2(px, py, L1, L2) - derived_q2(px, py, L1, L2)))
        except ValueError:
            continue
        w1 = max(w1, d1); w2 = max(w2, d2)
        if max(d1, d2) < 1e-9: ok += 1
    print(f"  L1={L1:<5} L2={L2:<5} n={n:<6} 一致率={100.0*ok/n:6.2f}%  "
          f"max|Δq1|={math.degrees(w1):.2e}°  max|Δq2|={math.degrees(w2):.2e}°")

print("\n=== 域外对照：y_leg>0 时两式是否分歧 ===")
L1 = L2 = 0.2
for (px, py) in [(0.30, 0.20), (-0.30, 0.20), (0.0, 0.35)]:
    try:
        f1, f2 = formula_q1(px, py, L1, L2), formula_q2(px, py, L1, L2)
        d1, d2 = derived_q1(px, py, L1, L2), derived_q2(px, py, L1, L2)
        bx, by = fk(f1, f2, L1, L2)
        print(f"  target=({px:+.2f},{py:+.2f})  MATLAB公式 q1={math.degrees(f1):+8.2f}° q2={math.degrees(f2):+8.2f}°  "
              f"(FK回代误差 {math.hypot(bx-px, by-py):.3f}m) | 重推 q1={math.degrees(d1):+8.2f}° q2={math.degrees(d2):+8.2f}°")
    except ValueError as e:
        print(f"  target=({px:+.2f},{py:+.2f})  acos 越界: {e}")
