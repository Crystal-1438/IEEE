#!/usr/bin/env python3
# 验证：MATLAB 原文 与 LaTeX 转写 是否等价；以及公式本身的自洽性
import math
import numpy as np

# ---------- A. MATLAB 原文逐字转写（numpy，逐元素语义同 MATLAB） ----------
def matlab_q1(x, y, L1, L2):
    A = (1.0/np.sqrt(x**2 + y**2) * (L1**2 - L2**2 + x**2 + y**2)) / (L1*2.0)
    B = x*1.0/np.sqrt(x**2 + y**2)
    return np.pi/2.0 - np.arccos(A) - np.arccos(B)

def matlab_q2(x, y, L1, L2):
    A = (1.0/np.sqrt(x**2 + y**2) * (L1**2 - L2**2 + x**2 + y**2)) / (L1*2.0)
    B = x*1.0/np.sqrt(x**2 + y**2)
    return (np.arctan2(y + L1*np.sin(np.arccos(A) + np.arccos(B)),
                       x - L1*np.cos(np.arccos(A) + np.arccos(B)))
            + np.arccos(A) + np.arccos(B))

# ---------- B. LaTeX 渲染式独立实现（标量 math，按排版结果从头写） ----------
def _ab(x, y, L1, L2):
    r = math.sqrt(x**2 + y**2)
    alpha = math.acos((L1**2 - L2**2 + x**2 + y**2) / (2*L1*r))
    beta = math.acos(x/r)
    return alpha, beta

def latex_q1(x, y, L1, L2):
    alpha, beta = _ab(x, y, L1, L2)
    return math.pi/2 - alpha - beta

def latex_q2(x, y, L1, L2):
    alpha, beta = _ab(x, y, L1, L2)
    return (math.atan2(y + L1*math.sin(alpha + beta),
                       x - L1*math.cos(alpha + beta))
            + alpha + beta)

# ---------- C. 正运动学（上一轮那两式） ----------
def fk(q1, q2, L1, L2):
    return (L1*math.sin(q1) + L2*math.sin(q1 + q2),
            -L1*math.cos(q1) - L2*math.cos(q1 + q2))

rng = np.random.default_rng(0)

def run_test(name, xs, ys, L1, L2):
    d1 = d2 = 0.0
    for x, y in zip(xs, ys):
        d1 = max(d1, abs(float(matlab_q1(x, y, L1, L2)) - latex_q1(x, y, L1, L2)))
        d2 = max(d2, abs(float(matlab_q2(x, y, L1, L2)) - latex_q2(x, y, L1, L2)))
    print(f"  [MATLAB vs LaTeX] {name:26s}  max|Δq1|={d1:.3e}  max|Δq2|={d2:.3e}")

print("=== 测试 1：MATLAB 原文 vs LaTeX 转写（纯语法等价性） ===")
L1, L2 = 0.2, 0.2
x = rng.uniform(-0.4, 0.4, 200000); y = rng.uniform(-0.4, 0.4, 200000)
r = np.sqrt(x**2 + y**2)
m = (r > 1e-6) & (r <= L1 + L2)         # 只取工作空间内、非奇异的点
run_test("x 全域 (-0.4,0.4)", x[m], y[m], L1, L2)
run_test("x > 0", x[m & (x > 0)], y[m & (x > 0)], L1, L2)
run_test("x < 0", x[m & (x < 0)], y[m & (x < 0)], L1, L2)

print("\n=== 测试 2：正运动学 -> 逆运动学 往返（检验公式本身） ===")
for (L1, L2) in [(0.2, 0.2), (0.2, 0.15), (1.0, 1.0)]:
    q1t = rng.uniform(-math.pi, math.pi, 100000)
    q2t = rng.uniform(-math.pi, math.pi, 100000)
    e_pos = e_q2 = 0.0
    bad = 0
    for a, b in zip(q1t, q2t):
        px, py = fk(a, b, L1, L2)
        try:
            r1 = latex_q1(px, py, L1, L2)
            r2 = latex_q2(px, py, L1, L2)
        except ValueError:
            bad += 1
            continue
        # (b) 不变式：IK 解代回 FK 应还原目标点（与肘分支无关）
        bx, by = fk(r1, r2, L1, L2)
        e_pos = max(e_pos, math.hypot(bx - px, by - py))
        # (a) 直接与原 q2 比
        d = abs((r2 - b + math.pi) % (2*math.pi) - math.pi)
        e_q2 = max(e_q2, d)
    tag = f"L1={L1}, L2={L2}"
    print(f"  {tag:18s} max|Δp|={e_pos:.3e} m   max|Δq2|={e_q2:.3e} rad   定义域外={bad}")

print("\n=== 测试 3：R = L1+L2 边界与 x_leg<0 的象限行为 ===")
L1 = L2 = 0.2
for (px, py) in [(0.4, 0.0), (-0.4, 0.0), (0.0, -0.4), (0.0, 0.4),
                 (-0.3, -0.2), (-0.25, 0.25), (0.3, 0.2)]:
    try:
        a = latex_q1(px, py, L1, L2); b = latex_q2(px, py, L1, L2)
        bx, by = fk(a, b, L1, L2)
        print(f"  target=({px:+.2f},{py:+.2f})  q1={math.degrees(a):+8.3f}°  "
              f"q2={math.degrees(b):+8.3f}°   FK回代误差={math.hypot(bx-px, by-py):.2e}")
    except ValueError as e:
        print(f"  target=({px:+.2f},{py:+.2f})  acos 定义域外: {e}")
