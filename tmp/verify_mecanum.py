#!/usr/bin/env python3
# 验证麦克纳姆轮 (V_i, omega_i) 关系式的修正版
import numpy as np

def v_wheel(vx, vy, wz, Pi):
    """轮心速度 V_i = V_b + omega_b x P_i"""
    x, y = Pi
    return np.array([vx - wz*y, vy + wz*x])          # wz*z_hat x (x,y) = (-wz*y, wz*x)

# 修正版：V_i . u_hat_i = R*w_i*cos(theta_i)，u_hat_i=(cos t, sin t)
def omega_corrected(V, theta, R):
    u = np.array([np.cos(theta), np.sin(theta)])
    return (V @ u) / (R*np.cos(theta))

# 教科书标准麦克纳姆逆解（四轮，左前起逆时针编号）
def omega_textbook(vx, vy, wz, lx, ly, R):
    s = lx + ly
    return np.array([vx - vy - s*wz,      # 1 左前
                     vx + vy + s*wz,      # 2 右前
                     vx + vy - s*wz,      # 3 右后
                     vx - vy + s*wz]) / R # 4 右后

# 几何：左前(+lx,+ly) 右前(+lx,-ly) 右后(-lx,-ly) 左后(-lx,+ly)，逆时针 1..4
P = [( lx := 0.15,  ly := 0.12),
     ( lx, -ly),
     (-lx, -ly),
     (-lx,  ly)]
THETA = [-np.pi/4, np.pi/4, np.pi/4, -np.pi/4]   # 左右轮辊子偏角反号
R = 0.035

rng = np.random.default_rng(3)
worst = 0.0
for _ in range(20000):
    vx, vy, wz = rng.uniform(-1, 1, 3)
    mine = np.array([omega_corrected(v_wheel(vx, vy, wz, p), t, R)
                     for p, t in zip(P, THETA)])
    ref = omega_textbook(vx, vy, wz, lx, ly, R)
    worst = max(worst, np.max(np.abs(mine - ref)))
print(f"[修正版 vs 教科书标准逆解] max|Δomega| = {worst:.3e} rad/s")

print("\n[量纲检查] 原式 V_{r,i} = omega_i*cos(theta_i):")
print(f"  右边量纲 = rad/s = {1.0*np.cos(np.pi/4):.6f} (无长度量纲)")
print(f"  左边 V_{{r,i}} 定义为 m/s")
print("  -> 量纲不一致，且与 V_i 无关，无法由轮心速度反解轮速")

print("\n[数值对照] 同一位姿 v=(0.5,0.2,0.3):")
vx, vy, wz = 0.5, 0.2, 0.3
print("  修正版 omega (rad/s):", np.round(
    [omega_corrected(v_wheel(vx, vy, wz, p), t, R) for p, t in zip(P, THETA)], 4))
print("  教科书 omega (rad/s):", np.round(omega_textbook(vx, vy, wz, lx, ly, R), 4))
print("  原式  omega*cos45    :", np.round(
    [omega_corrected(v_wheel(vx, vy, wz, p), t, R)*np.cos(t) for p, t in zip(P, THETA)], 4),
    " <- 这才是原式右边，单位错且丢了 R")

print("\n[紧致等价形式] R*w_i = V_{i,x} + V_{i,y}*tan(theta_i):")
worst2 = 0.0
for _ in range(20000):
    vx, vy, wz = rng.uniform(-1, 1, 3)
    for p, t in zip(P, THETA):
        V = v_wheel(vx, vy, wz, p)
        a = omega_corrected(V, t, R)*R
        b = V[0] + V[1]*np.tan(t)
        worst2 = max(worst2, abs(a-b))
print(f"  max 偏差 = {worst2:.3e}")
