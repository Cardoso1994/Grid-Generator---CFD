#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Apr 17 13:35:19 2018

@author: cardoso

Define clase airfoil. Genera perfiles a partir de una nube de puntos
Subclase NACA4 para creación de perfiles NACA serie 4
"""

import numpy as np
import matplotlib.pyplot as plt

# clase general de perfiles
class airfoil(object):
    def __init__(self, c):
        '''
        c = cuerda [m]
        x e y = coordenadas de la nube de puntos que describe el perfil
        '''
        self.c = c
        self.x = None
        self.y = None
        self.alone = True

    # se crea un perfil a partir de un archivo con la nube de puntos
    def create(self, filename):
        '''
        filename = nombre del archivo con los datos del perfil a importar
        '''
        c = self.c
        perf = np.loadtxt(filename)
        x = perf[:, 0]
        y = perf[:, 1]
        del (perf)

        # origen del sistema de coordenadas coincide con c/4
        x -= 0.25
        x *= c
        y *= c

        perfil = np.zeros((np.shape(x)[0], 2))
        perfil[:, 0] = x
        perfil[:, 1] = y
        # titulo = filename[: -4]
        np.savetxt('perfil_final.txt', perfil)
        self.x = perfil[:, 0]
        self.y = perfil[:, 1]
        '''points = np.shape(perfil)[0]
        points = (points + 1) // 2'''
        return

    def size(self):
        return np.size(self.x)

    def plot(self):
        '''
            grafica el perfil aerodinámico
        '''
        plt.figure('perfil')
        plt.axis('equal')
        plt.plot(self.x, self.y, 'b')
        plt.show()

    def rotate(self, degrees):
        '''
            rotación del perfil por 'degrees' grados en sentido horario
                (rotación positiva de perfiles aerodinámicos)
        '''
        size = self.size()
        rads = degrees * np.pi / 180 * -1

        for i in range(size):
            x = np.cos(rads) * self.x[i] - np.sin(rads) * self.y[i]
            y = np.sin(rads) * self.x[i] + np.cos(rads) * self.y[i]
            self.x[i] = x
            self.y[i] = y
        self.y -= self.y[0]
        perfil = np.zeros((np.shape(self.x)[0], 2))
        perfil[:, 0] = self.x
        perfil[:, 1] = self.y
        # titulo = filename[: -4]
        np.savetxt('perfil_final.txt', perfil)

    def join(self, other, dx, dy=0, join_section=4):
        '''
            une dos perfiles aerodinámicos. Para el análisis de external
                airfoil flaps
            self = perfil aerodinámico [airfoil]
            other = flap [airfoil]
            dx y dy = distancias en x e y respectivamente entre borde de
                salida del perfil y borde de ataque del flap
            join_section = número de puntos que unen al perfil y al flap
        '''
        self.alone = False
        join_section += 2
        x_airfoil = self.x
        y_airfoil = self.y
        x_flap = other.x
        y_flap = other.y
        size_airfoil = np.shape(x_airfoil)[0]
        size_flap = np.shape(x_flap)[0]

        #reajustando en Y
        dy_flap = y_flap[size_flap // 2]
        dy_total = dy_flap + dy
        y_airfoil += dy_total

        # reajustando en X
        dx_air = -x_flap[size_flap // 2] + x_airfoil[0]
        dx_total = dx_air + dx
        x_flap += dx_total
        x_join = np.linspace(x_flap[size_flap // 2], x_airfoil[0],
                             num=join_section)
        y_join = np.linspace(y_flap[size_flap // 2], y_airfoil[0],
                             num=join_section)

        x_total = x_flap[:size_flap // 2 + 1]
        y_total = y_flap[:size_flap // 2 + 1]
        x_total = np.concatenate((x_total, x_join[1:-1]))
        y_total = np.concatenate((y_total, y_join[1:-1]))
        x_total = np.concatenate((x_total, x_airfoil))
        y_total = np.concatenate((y_total, y_airfoil))
        x_total = np.concatenate((x_total, np.flip(x_join)[1:-1]))
        y_total = np.concatenate((y_total, np.flip(y_join)[1:-1]))
        x_total = np.concatenate((x_total, x_flap[size_flap // 2:]))
        y_total = np.concatenate((y_total, y_flap[size_flap // 2:]))

        self.x = x_total
        self.y = y_total
        perfil = np.zeros((np.shape(x_total)[0], 2))
        perfil[:, 0] = self.x
        perfil[:, 1] = self.y
        # titulo = filename[: -4]
        np.savetxt('perfil_final.txt', perfil)


class NACA4(airfoil):
    '''
        subclase de airfoil.
        Genera perfiles de la serie NACA de 4 dígitos
    '''
    def __init__(self, m, p, t, c):
        '''
            m = combadura máxima, se divide entre 100
            p = posición de la combadura máxima, se divide entre 10
            t = espesor máximo del perfil, en porcentaje de la cuerda
            c = cuerda del perfil [m]
        '''
        airfoil.__init__(self, c)
        self.m = m / 100
        self.p = p / 10
        self.t = t / 100

    def create_linear(self, points):
        '''
        Crea un perfil NACA4 con una distribución lineal

        points = número de puntos para el perfil
        '''
        points = (points + 1) // 2
        m = self.m
        p = self.p
        t = self.t
        c = self.c

        # distribución de los puntos en x a lo largo de la cuerda
        xc = np.linspace(0, 1, points)
        yt = np.zeros((points, ))
        yc = np.zeros((points, ))
        xu = np.zeros((points, ))
        xl = np.zeros((points, ))
        yl = np.zeros((points, ))
        theta = np.zeros((points, ))
        dydx = np.zeros((points, ))

        a0 = 0.2969
        a1 = -0.126
        a2 = -0.3516
        a3 = 0.2843
        # a4 = -0.1036
        a4 = -0.1015

        # calculo de la distribución de espesor
        yt = 5 * t * (a0 * xc ** 0.5 + a1 * xc + a2 * xc ** 2 + a3 * xc ** 3
                      + a4 * xc ** 4)

        # si es perfil simétrico
        if m == 0 and p == 0:
            xc *= c
            yt *= c

            xu = np.copy(xc)
            yu = np.copy(yt)
            xl = np.copy(xc)
            yl = -yt
        else:
            # cálculo línea de combadura media
            for i in range(points):
                if xc[i] <= p:
                    yc[i] = (m / p**2) * (2 * p * xc[i] - xc[i]**2)
                    dydx[i] = 2 * m / p**2 * (p - xc[i])
                else:
                    yc[i] = m / (1 - p)**2 * ((1 - 2*p) + 2 * p * xc[i]
                                              - xc[i] ** 2)
                    dydx[i] = 2 * m / (1 - p)**2 * (p - xc[i])

            theta = np.arctan(dydx)
            xu = xc - yt * np.sin(theta)
            xl = xc + yt * np.sin(theta)
            yu = yc + yt * np.cos(theta)
            yl = yc - yt * np.cos(theta)

            # escalamiento a la dimension de la cuerda
            xu *= c
            yu *= c
            xl *= c
            yl *= c
            xc *= c
            yc *= c
            yt *= c

        # ajuste para que el origen del sistema de coordenadas coincida con c/4
        xu -= c / 4
        xl -= c / 4
        xc -= c / 4

        # exportar los datos a un archivo txt
        xuf = np.copy(xu)
        xuf = np.flip(xuf, 0)
        yuf = np.copy(yu)
        yuf = np.flip(yuf, 0)
        xlf = np.copy(xl[1:])
        ylf = np.copy(yl[1:])
        xp = np.concatenate((xuf, xlf))
        yp = np.concatenate((yuf, ylf))

        # se invierten para que comience el perfil por el intrados
        # pasando al extrados  SENTIDO HORARIO
        xp = np.flip(xp, 0)
        yp = np.flip(yp, 0)
        perfil = np.zeros((np.shape(xp)[0], 2))

        perfil[:, 0] = xp
        perfil[:, 1] = yp
        np.savetxt('perfil_final.txt', perfil)
        self.x = perfil[:, 0]
        self.y = perfil[:, 1]

        return

    def create_sin(self, points):
        '''
        Crea un perfil NACA4 con una distribución no lineal mediante una
        función senoidal.
        Mayor densidad de puntos en bordes de ataque y de salida

        points = número de puntos para el perfil
        '''
        points = (points + 1) // 2
        m = self.m
        p = self.p
        t = self.t
        c = self.c

        # distribución de los puntos en x a lo largo de la cuerda
        beta = np.linspace(0, np.pi, points)
        xc = (1 - np.cos(beta)) / 2
        yt = np.zeros((points, ))
        yc = np.zeros((points, ))
        xu = np.zeros((points, ))
        xl = np.zeros((points, ))
        yl = np.zeros((points, ))
        theta = np.zeros((points, ))
        dydx = np.zeros((points, ))

        a0 = 0.2969
        a1 = -0.126
        a2 = -0.3516
        a3 = 0.2843
        # a4 = -0.1036
        a4 = -0.1015

        # calculo de la distribución de espesor
        yt = 5 * t * (a0 * xc ** 0.5 + a1 * xc + a2 * xc ** 2 + a3 * xc ** 3
                      + a4 * xc ** 4)

        # si es perfil simétrico
        if m == 0 and p == 0:
            xc *= c
            yt *= c

            xu = np.copy(xc)
            yu = np.copy(yt)
            xl = np.copy(xc)
            yl = -yt
        else:
            # cálculo línea de combadura media
            for i in range(points):
                if xc[i] <= p:
                    yc[i] = (m / p**2) * (2 * p * xc[i] - xc[i]**2)
                    dydx[i] = 2 * m / p**2 * (p - xc[i])
                else:
                    yc[i] = m / (1 - p)**2 * ((1 - 2*p) + 2 * p * xc[i]
                                              - xc[i] ** 2)
                    dydx[i] = 2 * m / (1 - p)**2 * (p - xc[i])

            theta = np.arctan(dydx)
            xu = xc - yt * np.sin(theta)
            xl = xc + yt * np.sin(theta)
            yu = yc + yt * np.cos(theta)
            yl = yc - yt * np.cos(theta)

            # escalamiento a la dimension de la cuerda
            xu *= c
            yu *= c
            xl *= c
            yl *= c
            xc *= c
            yc *= c
            yt *= c

        # ajuste para que el origen del sistema de coordenadas coincida con c/4
        xu -= c / 4
        xl -= c / 4
        xc -= c / 4
        # exportar los datos a un archivo txt
        xuf = np.copy(xu)
        xuf = np.flip(xuf, 0)
        yuf = np.copy(yu)
        yuf = np.flip(yuf, 0)
        xlf = np.copy(xl[1:])
        ylf = np.copy(yl[1:])
        xp = np.concatenate((xuf, xlf))
        yp = np.concatenate((yuf, ylf))

        # se invierten para que comience el perfil por el intrados
        # pasando al extrados  SENTIDO HORARIO
        xp = np.flip(xp, 0)
        yp = np.flip(yp, 0)
        perfil = np.zeros((np.shape(xp)[0], 2))

        perfil[:, 0] = xp
        perfil[:, 1] = yp
        perfil[0, 1] = 0
        perfil[-1, 1] = 0
        np.savetxt('perfil_final.txt', perfil)
        self.x = perfil[:, 0]
        self.y = perfil[:, 1]

        return


class cilindro(airfoil):
    def __init__(self, c):
        airfoil.__init__(self, c)

    def create(self, points):
        theta = np.linspace(2 * np.pi, np.pi, points)
        theta2 = np.linspace(np.pi, 0, points)
        theta = np.concatenate((theta, theta2[1:]))
        del(theta2)
        x = self.c * np.cos(theta)
        y = self.c * np.sin(theta)

        cilindro = np.zeros((np.shape(x)[0], 2))
        cilindro[:, 0] = x
        cilindro[:, 1] = y

        np.savetxt('cilindro.txt', cilindro)
        self.x = x
        self.y = y
