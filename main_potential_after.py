#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 18 00:33:47 2018

@author: cardoso
"""

import numpy as np
import matplotlib.pyplot as plt

import airfoil
import mesh
import mesh_c
import mesh_o
import mesh_su2
from potential import potential_flow_o, potential_flow_o_esp, velocity,\
                        pressure, streamlines
import helpers

#           variables de flujo
t_inf = 300
p_inf = 101300
v_inf = 10 # [m / s]

alfa = 0

gamma = 1.4
cp = 1006
Rg = cp * (gamma - 1) / gamma
d_inf = p_inf / (Rg * t_inf)
h_inf = cp * t_inf
c_inf = (gamma * p_inf / d_inf) ** 0.5

h0 = h_inf + 0.5 * v_inf ** 2
d0 = d_inf / (1 - 0.5 * v_inf ** 2 / h0)
p0 = p_inf * (d0 / d_inf) ** gamma

mach_inf = v_inf / c_inf

path_esp = '/home/cardoso/'

mallaNACA = helpers.from_txt_mesh(filename='./potential_test/mallaNACA.txt_mesh')

phi = np.genfromtxt('./potential_test/phi.csv', delimiter=',')
f = open("./potential_test/C.csv", "r")
C = np.genfromtxt('./potential_test/C.csv', delimiter=',')
theta = np.genfromtxt('./potential_test/theta.csv', delimiter=',')

X = np.genfromtxt(path_esp + 'Tesis_base/Potencial/potential_test/X.csv', delimiter=',')
Y = np.genfromtxt(path_esp + 'Tesis_base/Potencial/potential_test/Y.csv', delimiter=',')
phi_es = np.genfromtxt(path_esp + 'Tesis_base/Potencial/potential_test/phi.csv', delimiter=',')
C_es = np.genfromtxt(path_esp + 'Tesis_base/Potencial/potential_test/C.csv', delimiter=',')
theta_es = np.genfromtxt(path_esp + 'Tesis_base/Potencial/potential_test/theta.csv', delimiter=',')

plt.figure('potential')
plt.contour(mallaNACA.X, mallaNACA.Y, phi, 45)
plt.contour(X, Y, phi_es, 45)
plt.plot(mallaNACA.X[:, 0], mallaNACA.Y[:, 0], 'k')
plt.plot(mallaNACA.X[:, -1], mallaNACA.Y[:, -1], 'k')
plt.axis('equal')
plt.colorbar()

(u, v) = velocity(alfa, C, mach_inf, theta, mallaNACA, phi, v_inf)

(cp, p) = pressure(u, v, v_inf, d_inf, gamma, p_inf, p0, d0, h0)

(psi, mach) = streamlines(u, v, gamma, h0, d0, p, mallaNACA)

# X_tmp = np.copy(mallaNACA.X)
# Y_tmp = np.copy(mallaNACA.Y)
# mallaNACA.X = np.flip(X)
# mallaNACA.Y = np.flip(Y)
# theta_es = np.flip(theta_es)
# phi_es = np.flip(phi_es)
# (u_es, v_es) = velocity(alfa, C_es, mach_inf, theta_es, mallaNACA, phi_es, v_inf)
# (cp_es, p) = pressure(u_es, v_es, v_inf, d_inf, gamma, p_inf, p0, d0, h0)
# mallaNACA.X = X_tmp
# mallaNACA.Y = Y_tmp
# X = np.flip(X)
# Y = np.flip(Y)
# theta_es = np.flip(theta_es)
# phi_es = np.flip(phi_es)

plt.figure('velocity')
plt.quiver(mallaNACA.X[:, 1:-1], mallaNACA.Y[:, 1:-1], u[:, 1:-1], v[:, 1:-1], scale=90, scale_units='x')
# plt.quiver(X[:, 1:-1], Y[:, 1:-1], u_es[:, 1:-1], v_es[:, 1:-1], scale=90, scale_units='x', color='red')
plt.plot(mallaNACA.X[:, 0], mallaNACA.Y[:, 0], 'k')
plt.plot(mallaNACA.X[:, -1], mallaNACA.Y[:, -1], 'k')
plt.axis('equal')

plt.figure('pressure')
plt.plot(mallaNACA.X[:, 0], mallaNACA.Y[:, 0], 'k')
plt.contour(mallaNACA.X, mallaNACA.Y, cp, 64)
# plt.contour(X, Y, cp_es, 64)
plt.axis('equal')

plt.figure('streamlines')
plt.plot(mallaNACA.X[:, 0], mallaNACA.Y[:, 0], 'k')
plt.contour(mallaNACA.X, mallaNACA.Y, np.real(psi), 50)
plt.axis('equal')

plt.draw()
plt.show()
