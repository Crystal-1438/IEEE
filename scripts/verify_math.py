"""Numerically audit the paper's derivations; no robot/hardware tests are implied.
Run with Python 3 and NumPy: python scripts/verify_math.py
Synthetic geometries below are validation fixtures, not measured robot parameters.
"""
from pathlib import Path
import re
import numpy as np

rng = np.random.default_rng(1438)


def check(name, error, tolerance=1e-8):
    assert np.isfinite(error) and error < tolerance, (name, error)
    print(f'{name}: PASS (maximum residual {error:.3e})')


def leg_fk(q):
    q1, q2 = q
    return np.array([.17*np.sin(q1)+.22*np.sin(q1+q2),
                     -.17*np.cos(q1)-.22*np.cos(q1+q2), 0.])


def leg_j(q):
    q1, q2 = q
    return np.array([[.17*np.cos(q1)+.22*np.cos(q1+q2), .22*np.cos(q1+q2)],
                     [.17*np.sin(q1)+.22*np.sin(q1+q2), .22*np.sin(q1+q2)],
                     [0., 0.]])


ik_error = jac_error = power_error = 0.
A = np.array([[1., 0.], [-1., 1.]])
for _ in range(1000):
    q = rng.uniform([-.9, .3], [.2, 1.7])
    p = leg_fk(q)
    x, y, _ = p
    rho = np.hypot(x, y)
    alpha = np.arccos((.17**2-.22**2+rho**2)/(2*.17*rho))
    gamma = alpha+np.arctan2(-y, x)
    solved = np.array([np.pi/2-gamma,
                       np.arctan2(y+.17*np.sin(gamma), x-.17*np.cos(gamma))+gamma])
    ik_error = max(ik_error, np.max(np.abs(leg_fk(solved)-p)))
    direction = rng.normal(size=2)
    numeric = (leg_fk(q+1e-6*direction)-leg_fk(q-1e-6*direction))/2e-6
    jac_error = max(jac_error, np.max(np.abs(numeric-leg_j(q)@direction)))
    force = rng.normal(size=3)
    wheel_torque = rng.normal()
    tq = leg_j(q).T@force + wheel_torque*np.ones(2)
    tm = A.T@tq
    motor_velocity = rng.normal(size=2)
    q_velocity = A@motor_velocity
    power_error = max(power_error, abs(tm@motor_velocity -
        force@leg_j(q)@q_velocity-wheel_torque*np.sum(q_velocity)))
check('Leg FK/IK round trip (1000 targets)', ik_error)
check('Leg analytic Jacobian vs finite differences', jac_error)
check('Transmission and wheel-load virtual power', power_error)

mecanum_error = 0.
for _ in range(1000):
    velocity = rng.normal(size=3)
    velocity[2] = 0
    axle = np.array([0., -1., 0.])
    rolling = np.cross([0., 0., 1.], axle)
    for theta in [-np.pi/4, np.pi/4, .3]:
        roller_axis = np.cos(theta)*rolling - np.sin(theta)*axle
        omega = (velocity@rolling-(velocity@axle)*np.tan(theta))/.08
        residual = roller_axis@(velocity-.08*omega*rolling)
        mecanum_error = max(mecanum_error, abs(residual))
check('Mecanum no-slip constraint (both handednesses)', mecanum_error)

psi = np.arange(3)*2*np.pi/3
radial = np.column_stack([np.cos(psi), np.sin(psi), np.zeros(3)])


def delta_centres(q):
    centres = (.095-.066+.15*np.cos(q))[:, None]*radial
    centres[:, 2] = -.15*np.sin(q)
    return centres


def delta_fk(q):
    centres = delta_centres(q)
    diff = centres[1:]-centres[0]
    B = 2*diff[:, :2]
    d = np.sum(centres[1:]**2, axis=1)-centres[0]@centres[0]
    u = np.linalg.solve(B, d)
    v = np.linalg.solve(B, -2*diff[:, 2])
    coeff = [1+v@v, 2*(v@(u-centres[0, :2])-centres[0, 2]),
             np.sum((u-centres[0, :2])**2)+centres[0, 2]**2-.2**2]
    roots = np.roots(coeff)
    assert np.all(np.isreal(roots))
    z = min(roots)
    return np.r_[u+v*z, z]


delta_error = delta_j_error = 0.
for _ in range(1000):
    q = rng.uniform(.35, 1.15, 3)
    p = delta_fk(q)
    centres = delta_centres(q)
    S = p-centres
    delta_error = max(delta_error, np.max(abs(np.sum(S*S, axis=1)-.2**2)))
    c_prime = (-.15*np.sin(q))[:, None]*radial
    c_prime[:, 2] = -.15*np.cos(q)
    D = np.diag(np.sum(S*c_prime, axis=1))
    J = np.linalg.solve(S, D)
    direction = rng.normal(size=3)
    numeric = (delta_fk(q+1e-6*direction)-delta_fk(q-1e-6*direction))/2e-6
    delta_j_error = max(delta_j_error, np.max(abs(numeric-J@direction)))
check('Delta FK: all three rod-length constraints', delta_error)
check('Delta implicit Jacobian vs finite differences', delta_j_error)


def cross_matrix(r):
    x, y, z = r
    return np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])


contacts = [np.array(p) for p in [(.3,.2,-.4),(-.3,.2,-.4),(-.3,-.2,-.4),(.3,-.2,-.4)]]
H = np.vstack([np.hstack([np.eye(3)]*4), np.hstack([cross_matrix(p) for p in contacts])])
b = np.array([0., 0., 35*9.81, 0., 0., 0.])
f = H.T@np.linalg.solve(H@H.T, b)
check('SRB static equilibrium (synthetic symmetric stance)', np.max(abs(H@f-b)))
check('SRB symmetric normal-load split', np.max(abs(f.reshape(4,3)[:,2]-35*9.81/4)))

source = (Path(__file__).resolve().parents[1]/'Article.md').read_text()
tags = [int(x) for x in re.findall(r'\\tag\{(\d+)\}', source)]
assert tags == list(range(1, len(tags)+1))
assert len(tags) == source.count('$$')//2 == 45
slots = [int(x) for x in re.findall(r'FIGURE_SLOT:(\d+)', source)]
assert slots == [1,2,4,5,6,7,8,9]
for target in re.findall(r'!\[[^\]]*\]\(([^)]+)\)', source):
    assert (Path(__file__).resolve().parents[1]/target).is_file()
print('Article structure: PASS (45 numbered equations, 8 blank figure slots, image paths valid)')
