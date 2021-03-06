#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Wed Aug 1 13:53:21 2018

@author: cardoso

Define subclase mesh_O.
"""

import numpy as np
import matplotlib.pyplot as plt

from mesh import mesh
import mesh_su2
import sys

np.set_printoptions(threshold=np.sys.maxsize)

class mesh_O(mesh):
    """
    Clase para generar mallas tipo O y otros calculos de utilidad sobre
        las mismas
    ...

    Atributos
    ----------
    R : float64
        Radio de la frontera externa en la parte circular. La parte rectangular
            se define en funcion de este parametro
    N : int
        Numero de divisiones en el eje eta.
    airfoil : airfoil
        Objeto de la clase airfoil que define toda la frontera interna
    from_file : boolean
        La malla se crea a partir de una malla almacenada en un archivo con
            extension ".txt_mesh" o se genera en ejecucion.

    Metodos
    -------
    fronteras(airfoil_x, airfoil_y):
        Genera las fronteras interna y externa de la malla
    gen_Laplace(metodo='SOR', omega=1):
        Genera la malla mediante la solucion de la ecuacion de Laplace
    gen_Poisson(metodo='SOR', omega=1, a=0, c=0, linea_xi=0,
                    aa=0, cc=0, linea_eta=0):
        Genera la malla mediante la solucion de la ecuacion de Poisson
    gen_Poisson_v_(self, metodo='SOR', omega=1, a=0, c=0, linea_xi=0,
                    aa=0, cc=0, linea_eta=0):
        Genera la malla mediante la solucion de la ecuacion de Poisson.
        Utiliza vectorizacion, divide la malla en secciones, tanto en xi como
        en eta.
    gen_Poisson_n(self, metodo='SOR', omega=1, a=0, c=0, linea_xi=0,
                    aa=0, cc=0, linea_eta=0):
        Genera la malla mediante la solucion de la ecuacion de Poisson
        Utiliza la libreria numba para acelerar la ejecucion
    to_su2(filename):
        Convierte la malla a formato de SU2
    """

    def __init__(self, R, N, airfoil, from_file=False):
        M = np.shape(airfoil.x)[0]
        mesh.__init__(self, R, M, N, airfoil)
        self.tipo = 'O'
        self.fronteras(airfoil.x, airfoil.y)

    # importación de métodos de vectorizado y con librería numba
    from .mesh_o_poisson_performance import gen_Poisson_v_, gen_Poisson_n
    from .mesh_o_laplace_performance import gen_Laplace_v_, gen_Laplace_n

    def fronteras(self, airfoil_x, airfoil_y):
        """
        Genera las fronteras interna y externa de la malla
        ...

        Parametros
        ----------
        airfoil_x : numpy.array
            Coordenadas en el eje X de los puntos que definen al perfil alar
        airfoil_y : numpy.array
            Coordenadas en el eje Y de los puntos que definen al perfil alar

        Return
        ------
        None
        """

        R = self.R

        # cargar datos del perfil
        perfil_x    = airfoil_x
        perfil_y    = airfoil_y
        points      = np.shape(perfil_x)[0]
        points      = (points + 1) // 2

        # frontera externa
        theta   = np.linspace(0, np.pi, points)
        theta2  = np.linspace(np.pi, 2 * np.pi, points)
        theta   = np.concatenate((theta, theta2[1:]))
        del theta2

        x = R * np.cos(theta)
        y = R * np.sin(theta)

        x = np.flip(x, 0)
        y = np.flip(y, 0)

        # primera columna FI (perfil), ultima columna FE
        self.X[:, -1]   = x
        self.Y[:, -1]   = y
        self.X[:, 0]    = perfil_x
        self.Y[:, 0]    = perfil_y

        return

    # funcion para generar mallas mediante  ecuación de Laplace.
    def gen_Laplace(self, metodo='SOR', omega=1):
        """
        Resuelve la ecuacion de Laplace para generar la malla.

        Metodo clasico, con for loops anidados.
        ...

        Parametros
        ----------
        metodo : str
            Metodo iterativo de solucion. Jacobi (J), Gauss Seidel (GS) y
            sobrerelajacion (SOR)
        omega : float64
            Valor utilizado para acelerar o suavizar la solucion. Solo se
            utiliza si metodo == 'SOR'
            omega < 1 ---> suaviza la solucion
            omega = 1 ---> metodod Gauss Seidel
            omega > 1 ---> acelera la solucion

        Return
        ------
        None
        """

        # se genera malla antes por algún método algebráico
        self.gen_TFI()

        # se inician variables
        Xn  = self.X
        Yn  = self.Y
        Xo  = np.copy(Xn)
        Yo  = np.copy(Yn)
        m   = self.M
        n   = self.N

        d_eta   = self.d_eta
        d_xi    = self.d_xi

        # obteniendo el indice de la union de los perfiles
        if not self.airfoil_alone:
            union_start = 0
            while self.airfoil_boundary[union_start] != 0:
                union_start += 1

        print("Laplace:")
        # inicio del método iterativo
        for it in range(mesh.it_max):
            if (it % 1500 == 0):
                self.X = np.copy(Xn)
                self.Y = np.copy(Yn)
                self.plot()
                save = input("Save current Mesh: [Y/n]")
                if save == 'Y' or save == 'y':
                    name = input('name of mesh: ')
                    mallaNACA.to_su2(f"/home/desarrollo/garbage/{name}.su2")
                    mallaNACA.to_txt_mesh(
                        f"/home/desarrollo/garbage/{name}.txt_mesh")

            # printing info
            print('it = ' + str(it)
                  + ' err_x = ' + '{:.3e}'.format(abs(Xn - Xo).max())
                  + ' err_y = ' + '{:.3e}'.format(abs(Yn - Yo).max())
                  + '\t\t', end="\r")

            Xo = np.copy(Xn)
            Yo = np.copy(Yn)
            # si el método iterativo es Jacobi
            if metodo == 'J':
                X = Xo
                Y = Yo
            else:   # si el método es Gauss-Seidel o SOR
                X = Xn
                Y = Yn

            for j in range(1, n-1):
                for i in range(1, m-1):
                    x_eta   = (X[i, j+1] - X[i, j-1]) / 2 / d_eta
                    y_eta   = (Y[i, j+1] - Y[i, j-1]) / 2 / d_eta
                    x_xi    = (X[i+1, j] - X[i-1, j]) / 2 / d_xi
                    y_xi    = (Y[i+1, j] - Y[i-1, j]) / 2 / d_xi

                    alpha   = x_eta ** 2 + y_eta ** 2
                    beta    = x_xi * x_eta + y_xi * y_eta
                    gamma   = x_xi ** 2 + y_xi ** 2

                    Xn[i, j] = (d_xi * d_eta) ** 2\
                        / (2 * (alpha * d_eta ** 2 + gamma * d_xi ** 2))\
                        * (alpha / (d_xi ** 2) * (X[i+1, j] + X[i-1, j])
                            + gamma / (d_eta**2) * (X[i, j+1] + X[i, j-1])
                            - beta / (2 * d_xi * d_eta) * (X[i+1, j+1]
                                    - X[i+1, j-1] + X[i-1, j-1] - X[i-1, j+1]))
                    Yn[i, j] = (d_xi * d_eta) ** 2\
                        / (2 * (alpha * d_eta ** 2 + gamma * d_xi ** 2))\
                        * (alpha / (d_xi**2) * (Y[i+1, j] + Y[i-1, j])
                            + gamma / (d_eta**2) * (Y[i, j+1] + Y[i, j-1])
                            - beta / (2 * d_xi * d_eta) * (Y[i+1, j+1]
                                    - Y[i+1, j-1] + Y[i-1, j-1] - Y[i-1, j+1]))

                i           = m-1
                x_eta       = (X[i, j+1] - X[i, j-1]) / 2 / d_eta
                y_eta       = (Y[i, j+1] - Y[i, j-1]) / 2 / d_eta
                x_xi        = (X[1, j] - X[i-1, j]) / 2 / d_xi
                y_xi        = (Y[1, j] - Y[i-1, j]) / 2 / d_xi
                alpha       = x_eta ** 2 + y_eta ** 2
                beta        = x_xi * x_eta + y_xi * y_eta
                gamma       = x_xi ** 2 + y_xi ** 2
                Xn[i, j]    = (d_xi * d_eta) ** 2\
                    / (2 * (alpha * d_eta**2 + gamma * d_xi**2))\
                    * (alpha / (d_xi**2) * (X[1, j] + X[i-1, j])
                        + gamma / (d_eta**2) * (X[i, j+1] + X[i, j-1])
                        - beta / (2 * d_xi * d_eta) * (X[1, j+1] - X[1, j-1]
                                                + X[i-1, j-1] - X[i-1, j+1]))
            Xn[0, :] = Xn[-1, :]

            # seccion de union entre perfiles
            if not self.airfoil_alone:
                i = union_start
                while self.airfoil_boundary[i] == 0:
                    x_eta = (X[i, 1] - X[-i - 1, 1]) / 2 / d_eta
                    y_eta = (Y[i, 1] - Y[-i - 1, 1]) / 2 / d_eta
                    x_xi = (X[i+1, 0] - X[i-1, 0]) / 2 / d_xi
                    y_xi = (Y[i+1, 0] - Y[i-1, 0]) / 2 / d_xi

                    alpha = x_eta ** 2 + y_eta ** 2
                    beta = x_xi * x_eta + y_xi * y_eta
                    gamma = x_xi ** 2 + y_xi ** 2
                    I = x_xi * y_eta - x_eta * y_xi

                    # X[i, 0]    = (d_xi * d_eta) ** 2 \
                    #     / (2 * (alpha * d_eta ** 2 + gamma * d_xi ** 2))\
                    #     * (alpha / (d_xi ** 2) * (X[i+1, 0] + X[i-1, 0])
                    #         + gamma / (d_eta ** 2) * (X[i, 1] + X[-i -1, 1])
                    #         - beta / (2 * d_xi * d_eta) * (X[i+1, 1]
                    #                 - X[-i -2, 1] + X[-i, 1] - X[i-1, 1]))
                    Y[i, 0]    = (d_xi * d_eta) ** 2\
                        / (2 * (alpha * d_eta ** 2 + gamma * d_xi ** 2))\
                        * (alpha / (d_xi ** 2) * (Y[i+1, 0] + Y[i-1, 0])
                            + gamma / (d_eta ** 2) * (Y[i, 1] + Y[-i -1, 1])
                            - beta / (2 * d_xi * d_eta) * (Y[i+1, 1]
                                    - Y[-i -2, 1] + Y[-i, 1] - Y[i-1, 1]))

                    X[-i -1, 0] = X[i, 0]
                    Y[-i -1, 0] = Y[i, 0]
                    i += 1

            # se aplica sobre-relajacion si el metodo es SOR
            if metodo == 'SOR':
                Xn = omega * Xn + (1 - omega) * Xo
                Yn = omega * Yn + (1 - omega) * Yo

            if abs(Xn - Xo).max() < mesh.err_max\
                    and abs(Yn - Yo).max() < mesh.err_max:
                print(metodo + ': saliendo...')
                print('it=', it)
                break

        self.X = Xn
        self.Y = Yn
        return

    def gen_Poisson(self, metodo='SOR', omega=1, a=0, c=0, linea_xi=0,
                    aa=0, cc=0, linea_eta=0):
        """
        Resuelve la ecuacion de Poisson para generar la malla.

        Metodo clasico, con for loops anidados.
        ...

        Parametros
        ----------
        metodo : str
            Metodo iterativo de solucion. Jacobi (J), Gauss Seidel (GS) y
            sobrerelajacion (SOR)
        omega : float64
            Valor utilizado para acelerar o suavizar la solucion. Solo se
            utiliza si metodo == 'SOR'
            omega < 1 ---> suaviza la solucion
            omega = 1 ---> metodod Gauss Seidel
            omega > 1 ---> acelera la solucion
        a, c : float64
            valores ocupados para la funcion de forzado P, en el eje xi
        linea_xi : int
            linea  en el eje xi hacia la cual se realiza el forzado.
            0 <= linea_xi <= self.M
        aa, cc : float64
            valores ocupados para la funcion de forzado Q, en el eje eta
        linea_eta : int
            linea  en el eje eta hacia la cual se realiza el forzado.
            0 <= linea_eta <= self.N

        Return
        ------
        None
        """

        # se genera malla antes por algún método algebráico
        self.gen_TFI()

        # se inician variables
        Xn  = self.X
        Yn  = self.Y
        Xo = np.copy(Xn)
        Yo = np.copy(Yn)
        m   = self.M
        n   = self.N

        d_eta   = self.d_eta
        d_xi    = self.d_xi

        # parámetros de ecuación de Poisson
        P_ = np.arange(1, m)
        Q_ = np.arange(1, n)

        P_ = -a * (np.longdouble(P_ / (m-1) - linea_xi))\
                                / np.abs(np.longdouble(P_ / (m-1) - linea_xi))\
                                * np.exp(-c * np.abs(np.longdouble(P_ /
                                                         (m-1) - linea_xi)))
        Q_ = -aa * (np.longdouble(Q_ / (n-1) - linea_eta))\
                    / np.abs(np.longdouble(Q_ / (n-1) - linea_eta))\
                    * np.exp(-cc * np.abs(np.longdouble(Q_ / (n-1) - linea_eta)))
        mask = np.isnan(P_)
        P_[mask] = 0
        mask = np.isnan(Q_)
        Q_[mask] = 0

        # obteniendo el indice de la union de los perfiles
        if not self.airfoil_alone:
            union_start = 0
            while self.airfoil_boundary[union_start] != 0:
                union_start += 1

        mesh.it_max = 55000
        print("Poisson:")
        for it in range(mesh.it_max):
            if (it % 1500 == 0):
                self.X = np.copy(Xn)
                self.Y = np.copy(Yn)
                self.plot()
                save = input("Save current Mesh: [Y/n]")
                if save == 'Y' or save == 'y':
                    name = input('name of mesh: ')
                    mallaNACA.to_su2(f"/home/desarrollo/garbage/{name}.su2")
                    mallaNACA.to_txt_mesh(
                        f"/home/desarrollo/garbage/{name}.txt_mesh")

            # printing info
            print('it = ' + str(it) + ' aa = ' + str(aa) + ' cc = ' + str(cc)
                  + ' err_x = ' + '{:.3e}'.format(abs(Xn - Xo).max())
                  + ' err_y = ' + '{:.3e}'.format(abs(Yn - Yo).max())
                  + '\t\t', end="\r")
            Xo = np.copy(Xn)
            Yo = np.copy(Yn)
            # método iterativo Jacobi
            if metodo == 'J':
                X = Xo
                Y = Yo
            else:   # método Gauss-Seidel o SOR
                X = Xn
                Y = Yn

            for j in range(1, n-1):
                for i in range(1, m-1):
                    x_eta   = (X[i, j+1] - X[i, j-1]) / 2 / d_eta
                    y_eta   = (Y[i, j+1] - Y[i, j-1]) / 2 / d_eta
                    x_xi    = (X[i+1, j] - X[i-1, j]) / 2 / d_xi
                    y_xi    = (Y[i+1, j] - Y[i-1, j]) / 2 / d_xi

                    alpha   = x_eta ** 2 + y_eta ** 2
                    beta    = x_xi * x_eta + y_xi * y_eta
                    gamma   = x_xi ** 2 + y_xi ** 2
                    I       = x_xi * y_eta - x_eta * y_xi

                    Xn[i, j]    = (d_xi * d_eta) ** 2\
                        / (2 * (alpha * d_eta ** 2 + gamma * d_xi ** 2))\
                        * (alpha / (d_xi ** 2) * (X[i+1, j] + X[i-1, j])
                            + gamma / (d_eta ** 2) * (X[i, j+1] + X[i, j-1])
                            - beta / (2 * d_xi * d_eta) * (X[i+1, j+1]
                                    - X[i+1, j-1] + X[i-1, j-1] - X[i-1, j+1])
                            + I ** 2 * (P_[i-1] * x_xi + Q_[j-1] * x_eta))
                    Yn[i, j]    = (d_xi * d_eta) ** 2\
                        / (2 * (alpha * d_eta**2 + gamma * d_xi**2))\
                        * (alpha / (d_xi**2) * (Y[i+1, j] + Y[i-1, j])
                            + gamma / (d_eta**2) * (Y[i, j+1] + Y[i, j-1])
                            - beta / (2 * d_xi * d_eta) * (Y[i+1, j+1]
                                    - Y[i+1, j-1] + Y[i-1, j-1] - Y[i-1, j+1])
                            + I**2 * (P_[i-1] * y_xi + Q_[j-1] * y_eta))

                i       = m-1
                x_eta   = (X[i, j+1] - X[i, j-1]) / 2 / d_eta
                y_eta   = (Y[i, j+1] - Y[i, j-1]) / 2 / d_eta
                x_xi    = (X[1, j] - X[i-1, j]) / 2 / d_xi
                y_xi    = (Y[1, j] - Y[i-1, j]) / 2 / d_xi

                alpha   = x_eta ** 2 + y_eta ** 2
                beta    = x_xi * x_eta + y_xi * y_eta
                gamma   = x_xi ** 2 + y_xi ** 2
                I       = x_xi * y_eta - x_eta * y_xi

                Xn[i, j]    = (d_xi * d_eta) ** 2\
                    / (2 * (alpha * d_eta**2 + gamma * d_xi**2))\
                    * (alpha / (d_xi**2) * (X[1, j] + X[i-1, j])
                        + gamma / (d_eta**2) * (X[i, j+1] + X[i, j-1])
                        - beta / (2 * d_xi * d_eta)
                        * (X[1, j+1] - X[1, j-1] + X[i-1, j-1] - X[i-1, j+1])
                        + I**2 * (P_[i-1] * x_xi + Q_[j-1] * x_eta))

            Xn[0, :] = Xn[-1, :]

            # seccion de union entre perfiles
            if not self.airfoil_alone:
                i = union_start
                while self.airfoil_boundary[i] == 0:
                    x_eta = (X[i, 1] - X[-i - 1, 1]) / 2 / d_eta
                    y_eta = (Y[i, 1] - Y[-i - 1, 1]) / 2 / d_eta
                    x_xi = (X[i+1, 0] - X[i-1, 0]) / 2 / d_xi
                    y_xi = (Y[i+1, 0] - Y[i-1, 0]) / 2 / d_xi

                    alpha = x_eta ** 2 + y_eta ** 2
                    beta = x_xi * x_eta + y_xi * y_eta
                    gamma = x_xi ** 2 + y_xi ** 2
                    I = x_xi * y_eta - x_eta * y_xi

                    # X[i, 0]    = (d_xi * d_eta) ** 2 \
                    #     / (2 * (alpha * d_eta ** 2 + gamma * d_xi ** 2))\
                    #     * (alpha / (d_xi ** 2) * (X[i+1, 0] + X[i-1, 0])
                    #         + gamma / (d_eta ** 2) * (X[i, 1] + X[-i -1, 1])
                    #         - beta / (2 * d_xi * d_eta) * (X[i+1, 1]
                    #                 - X[-i -2, 1] + X[-i, 1] - X[i-1, 1]))
                    Y[i, 0]    = (d_xi * d_eta) ** 2\
                        / (2 * (alpha * d_eta ** 2 + gamma * d_xi ** 2))\
                        * (alpha / (d_xi ** 2) * (Y[i+1, 0] + Y[i-1, 0])
                            + gamma / (d_eta ** 2) * (Y[i, 1] + Y[-i -1, 1])
                            - beta / (2 * d_xi * d_eta) * (Y[i+1, 1]
                                    - Y[-i -2, 1] + Y[-i, 1] - Y[i-1, 1]))

                    X[-i -1, 0] = X[i, 0]
                    Y[-i -1, 0] = Y[i, 0]
                    i += 1

            # se aplica sobre-relajacion si el metodo es SOR
            if metodo == 'SOR':
                Xn = omega * Xn + (1 - omega) * Xo
                Yn = omega * Yn + (1 - omega) * Yo

            if abs(Xn - Xo).max() < mesh.err_max\
                    and abs(Yn - Yo).max() < mesh.err_max:
                print(metodo + ': saliendo...')
                print('it = ', it)
                break

        self.X = Xn
        self.Y = Yn
        return


    def gen_hyperbolic(self):
        '''
        Genera mallas hiperbólicas. Método de Steger

        TODO
        '''

        # se inician las variables características de la malla
        m       = self.M
        n       = self.N
        X       = self.X
        Y       = self.Y
        d_xi    = self.d_xi
        d_eta   = self.d_eta
        d_s1    = 0.001
        S       = np.zeros((m - 2, m - 2), dtype=object)
        L       = np.zeros((m - 2, m - 2), dtype=object)
        U       = np.zeros((m - 2, m - 2), dtype=object)
        R       = np.zeros((m - 2, 1), dtype=object)
        Z       = np.zeros((m - 2, 1), dtype=object)
        DD      = np.zeros((m - 2, 1), dtype=object)
        Fprev   = 0.000000005
        C = np.zeros((2, 2))

        for j in range(1, n):
            # se llena la matriz S y el vector DD
            for i in range(1, m-1):
                F = 0.5 * (((X[i, j - 1] - X[i - 1, j - 1]) ** 2
                            + (Y[i, j - 1] - Y[i - 1, j - 1]) ** 2) ** 0.5
                           + ((X[i + 1, j - 1] - X[i, j - 1]) ** 2
                              + (Y[i + 1, j - 1] - Y[i, j - 1]) ** 2) ** 0.5)
                F = F * d_s1 * (1 + 0.001) ** (j - 1)
                x_xi_k = (X[i + 1, j - 1] - X[i - 1, j - 1]) / 2 / d_xi
                y_xi_k = (Y[i + 1, j - 1] - Y[i - 1, j - 1]) / 2 / d_xi
                x_eta_k = - y_xi_k * F / (x_xi_k ** 2 + y_xi_k ** 2)
                y_eta_k = x_xi_k * F / (x_xi_k ** 2 + y_xi_k ** 2)
                B_1 = np.array([[x_xi_k, -y_xi_k], [y_xi_k, x_xi_k]])\
                    / (x_xi_k ** 2 + y_xi_k ** 2)
                A = np.array([[x_eta_k, y_eta_k], [y_eta_k, -x_eta_k]])
                C = B_1 @ A
                AA = - 1 / 2 / d_xi * C
                BB = np.identity(2) / d_eta
                CC = -AA
                dd = B_1 @ np.array([[0], [F + Fprev]])\
                    + np.array([[X[i, j - 1]], [Y[i, j - 1]]]) / d_eta
                if i == 1:
                    dd -= (AA @ np.array([[X[0, j]], [Y[0, j]]]))
                    S[0, 0] = BB
                    S[0, 1] = CC
                elif i == m - 2:
                    dd -= (CC @ np.array([[X[m - 1, j]], [Y[m - 1, j]]]))
                    S[m - 3, m - 4] = AA
                    S[m - 3, m - 3] = BB
                else:
                    S[i - 1, i - 2] = AA
                    S[i - 1, i - 1] = BB
                    S[i - 1, i] = CC
                DD[i - 1, 0] = dd
            # se llenan las matrices L y U
            for i in range(m - 2):
                if i == 0:
                    L[0, 0] = S[0, 0]
                    U[0, 0] = np.identity(2)
                    U[0, 1] = np.linalg.inv(S[0, 0]) @ S[0, 1]
                elif i == m - 3:
                    L[m - 3, m - 4] = S[m - 3, m - 4]
                    L[m - 3, m - 3] = S[m - 3, m - 3]\
                        - S[m - 3, m - 4] @ U[m - 4, m - 3]
                    U[m - 3, m - 3] = np.identity(2)
                else:
                    L[i, i - 1] = S[i, i - 1]
                    L[i, i]     = S[i, i] - S[i, i - 1] @ U[i - 1, i]
                    U[i, i]     = np.identity(2)
                    U[i, i + 1] = np.linalg.inv(L[i, i]) @ S[i, i + 1]
            # se obtienen los valores del vector Z
            i = 0
            Z[0, 0] = np.linalg.inv(L[0, 0]) @ DD[0, 0]
            for i in range(1, m - 2):
                Z[i, 0] = np.linalg.inv(L[i, i])\
                        @ (DD[i, 0] - L[i, i - 1] @ Z[i - 1, 0])

            # se obtienen los valores del vector R
            i       = m - 3
            R[i, 0] = Z[i, 0]
            for i in range(m - 4, -1, -1):
                R[i, 0] = Z[i, 0] - U[i, i + 1] @ Z[i + 1, 0]

            # se asignan las coordenadas X y Y
            for i in range(1, m - 1):
                X[i, j] = R[i - 1, 0][0]
                Y[i, j] = R[i - 1, 0][1]
            x_xi        = (X[1, j - 1] - X[-2, j - 1]) / 2 / d_xi
            y_xi        = (Y[1, j - 1] - Y[-2, j - 1]) / 2 / d_xi
            X[0, j]     = X[0, j - 1] - d_eta / 2 / d_xi * F\
                / (x_xi ** 2 + y_xi ** 2)
            X[0, j]     *= (Y[1, j - 1] - Y[-2, j - 1])
            X[-1, j]    = X[0, j]
            Fprev       = F
        return

    def gen_parabolic(self):
        '''
        Genera malla resolviendo un sistema de ecuaciones parabólicas
        Basado en el reporte técnico de Siladic

        TODO
        '''

        m = self.M
        n = self.N
        X = self.X
        Y = self.Y

        weight      = 1.9
        delta_limit = self.R - X[0, 0]
        x_line      = np.zeros(n, dtype='float64')
        h           = delta_limit * (1 - weight) / (1 - weight ** ((n - 1)))
        x_line[-1]  = self.R
        x_line[0]   = X[0, 0]
        dd          = x_line[0]

        for i in range(0, n - 1):
            x_line[i]   = dd
            dd          += h * weight ** i

        X[0, :]     = x_line
        X[-1, :]    = x_line

        delta_limit = 1
        G_line      = np.zeros(n, dtype='float64')
        h           = delta_limit * (1 - weight) / (1 - weight ** (n - 1))
        G_line[-1]  = 1
        G_line[0]   = 0
        dd          = G_line[0]

        for i in range(n - 1):
            G_line[i]   = dd
            dd          += h * weight ** i

        # variables del método de solución
        R_          = np.zeros((m - 2,), dtype=object)
        Y_          = np.zeros((m - 2,), dtype=object)
        delta_Q     = np.zeros((m - 2,), dtype=object)
        A_          = np.empty((m-2,), dtype=object)
        B_          = np.empty((m-2,), dtype=object)
        C_          = np.empty((m-2,), dtype=object)
        alpha_      = np.empty((m-2,), dtype=object)
        beta_       = np.empty((m-2,), dtype=object)
        XO          = np.empty((m,), dtype=object)
        YO          = np.empty((m,), dtype=object)

        # resolver ecuaciones gobernantes
        # A * x[i - i, j] + B x[i, j] + C x[i + 1, j] = Dx
        # A * y[i - i, j] + B y[i, j] + C y[i + 1, j] = Dy

        # A = 2 * alpha / (F[i - 1] * (F[i] + F[i - 1]))
        # C = 2 * alpha / (F[i] * (F[i] + F[i - 1]))
        # B = -2 * alpha / (F[i] + F[i - 1]) * (1 / F[i] + 1 / F[i - 1])\
        #       -2 * gamma / (G[j] + g[j - 1]) * (x[i, j - 1] / g[j - 1]\
        #       + XO[i, j+1] / G[j])
        # Ds = -beta * (SO[i + 1, j + 1] - SO[i - 1, j + 1] - s[i + 1, j - 1]\
        #           + s[i - 1, j - 1]) / (F[i] + F[i - 1]) / (G[j] + g[j - 1])\
        #           - 2 * gamma / (G[j] + g[j - 1]) * (s[i, j - 1] / g[j - 1]\
        #           SO[i, j + 1] / G[j])

        # alpha = x_eta ** 2 + y_eta ** 2
        # beta = x_xi * x_eta + y_xi * y_eta
        # gamma = x_xi ** 2 + y_xi ** 2

        # x_xi = (x[i + 1, j] - x[i - 1, j]) / (F[i] + F[i - 1])
        # x_eta = (XO[i, j + 1] - x[i, j - 1]) / (g[j - 1] + G[j])

        # F[*] = deltas en direccion xi
        # G y g = deltas en direccion eta
        # XO y YO = valores de x[i, j + 1] y y[i, j + 1] interpolados entre
        #       las fronteras
        for j in range(1, n - 1):
            Gj      = x_line[-1] - x_line[j]
            gj_1    = x_line[j] - x_line[j - 1]

            ###############################################################
            #
            #   Se calculan valores XO y YO imponiendo ortogonalidad
            #
            ###############################################################
            dist = (X[0, -1] - X[0, 0]) ** 2 + (Y[0, -1] - Y[0, 0]) ** 2
            dist **= 0.5
            # se calcula pendiente del cuerpo para obtener la recta normal
            if abs(Y[1, 0] - Y[-2, 0]) >= 0.01\
                    and abs(X[1, 0] - X[-2, 0]) >= 0.01:
                pendiente = (Y[1, 0] - Y[-2, 0])\
                    / (X[1, 0] - X[-2, 0])
                pendiente = - 1 / pendiente
                a_      = 1 + 1 / pendiente ** 2
                b_      = - 2 * Y[0, 0] / pendiente ** 2 - 2 * Y[0, 0]
                c_      = (1 + 1 / pendiente ** 2) * Y[0, 0] ** 2 - dist ** 2
                y_pos   = (-b_ + (b_ ** 2 - 4 * a_ * c_) ** 0.5) / 2 / a_
                y_neg   = (-b_ - (b_ ** 2 - 4 * a_ * c_) ** 0.5) / 2 / a_
                b_recta = Y[0, 0] - pendiente * X[0, 0]
                x_pos   = (y_pos - b_recta) / pendiente
                x_neg   = (y_neg - b_recta) / pendiente
                x_neg   = (y_neg - b_recta) / pendiente
                XO[0]   = x_pos
                YO[0]   = y_pos
            elif abs(Y[1, 0] - Y[-2, 0]) < 0.01:
                XO[0] = X[0, 0]
                YO[0] = Y[0, 0] + dist

            elif abs(X[1, 0] - X[-2, 0]) < 0.01:
                YO[0] = Y[0, 0]
                XO[0] = X[0, 0] + dist

            XO[-1] = XO[0]
            YO[-1] = YO[0]

            for i in range(1, m - 1):
                # se calcula radio desde [i, 0] hasta [i, -1]
                dist = (X[i, -1] - X[i, 0]) ** 2 + (Y[i, -1] - Y[i, 0]) ** 2
                dist **= 0.5
                # se calcula pendiente del cuerpo para obtener la recta normal
                # si no son aprox 0 se calcula pendiente, si no se dan los
                # valores directo, según sea el caso
                if abs(Y[i + 1, 0] - Y[i - 1, 0]) >= 0.01\
                        and abs(X[i + 1, 0] - X[i - 1, 0]) >= 0.01:
                    pendiente = (Y[i + 1, 0] - Y[i - 1, 0])\
                        / (X[i + 1, 0] - X[i - 1, 0])
                    pendiente = - 1 / pendiente
                    a_ = 1 + 1 / pendiente ** 2
                    b_ = - 2 * Y[i, 0] / pendiente ** 2 - 2 * Y[i, 0]
                    c_ = (1 + 1 / pendiente ** 2) * Y[i, 0] ** 2 - dist ** 2
                    y_pos = (-b_ + (b_ ** 2 - 4 * a_ * c_) ** 0.5) / 2 / a_
                    y_neg = (-b_ - (b_ ** 2 - 4 * a_ * c_) ** 0.5) / 2 / a_
                    b_recta = Y[i, 0] - pendiente * X[i, 0]
                    x_pos   = (y_pos - b_recta) / pendiente
                    x_neg   = (y_neg - b_recta) / pendiente
                    if i <= m // 2:
                        YO[i] = y_neg
                        XO[i] = x_neg
                    else:
                        YO[i] = y_pos
                        XO[i] = x_pos

                elif abs(Y[i + 1, 0] - Y[i - 1, 0]) < 0.01:
                    XO[i] = X[i, 0]
                    if i <= m // 2:
                        YO[i] = Y[i, 0] - dist
                    else:
                        YO[i] = Y[i, 0] + dist

                elif abs(X[i + 1, 0] - X[i - 1, 0]) < 0.01:
                    YO[i] = Y[i, 0]
                    if i <= m // 2:
                        XO[i] = X[i, 0] - dist
                    else:
                        XO[i] = X[i, 0] + dist
            ###############################################################
            #
            #   Termina calculo de valores XO y YO
            #
            ###############################################################

            for i in range(1, m - 1):
                ###############################################################
                #
                #   Se calculan las funciones F como:
                #       F = sqrt(deltaX ** 2 + deltaY ** 2)
                #   Siladic página 44 del texto
                #   Aparentemente solo en j-1
                #
                ###############################################################
                Fi      = ((X[i + 1, j - 1] - X[i, j - 1]) ** 2
                      + (Y[i + 1, j - 1] - Y[i, j - 1]) ** 2) ** 0.5
                Fi_1    = ((X[i, j - 1] - X[i - 1, j - 1]) ** 2
                        + (Y[i, j - 1] - Y[i - 1, j - 1]) ** 2) ** 0.5

                x_xi    = (X[i + 1, j - 1] - X[i - 1, j - 1]) / (Fi + Fi_1)
                y_xi    = (Y[i + 1, j - 1] - Y[i - 1, j - 1]) / (Fi + Fi_1)
                x_eta   = (XO[i] - X[i, j - 1]) / (gj_1 + Gj)
                y_eta   = (YO[i] - Y[i, j - 1]) / (gj_1 + Gj)

                alpha   = x_eta ** 2 + y_eta ** 2
                beta    = -2 * (x_xi * x_eta + y_xi * y_eta)
                gamma   = x_xi ** 2 + y_xi ** 2

                A   = 2 * alpha / Fi_1 / (Fi + Fi_1)
                B   = -2 * alpha / (Fi + Fi_1) * (1 / Fi + 1 / Fi_1)\
                    - 2 * gamma / (Gj + gj_1) * (1 / Gj + 1 / gj_1)
                C   = 2 * alpha / Fi / (Fi + Fi_1)
                Dx  = - beta * (XO[i + 1] - XO[i - 1]
                               - X[i + 1, j - 1] + X[i - 1, j - 1])\
                    / (Fi + Fi_1) / (Gj + gj_1) - 2 * gamma / (Gj + gj_1)\
                    * (X[i, j - 1] / gj_1 + XO[i] / Gj)
                Dy  = - beta * (YO[i + 1] - YO[i - 1]
                               - Y[i + 1, j - 1] + Y[i - 1, j - 1])\
                    / (Fi + Fi_1) / (Gj + gj_1) - 2 * gamma / (Gj + gj_1)\
                    * (Y[i, j - 1] / gj_1 + YO[i] / Gj)
                # se comienzan a crear las submatrics de la solución
                # S_ * delta_Q = R
                #   S = matriz tridiagonal formada por submatrices A, B y C
                #       para  cada nivel
                # S = LU
                #   L = matriz A * alpha_
                #   U = I * beta_
                # R == [Dx, Dy]
                A_[i - 1] = np.array(([[A, 0], [0, A]]))
                B_[i - 1] = np.array(([[B, 0], [0, B]]))
                C_[i - 1] = np.array(([[C, 0], [0, C]]))
                ###############################################################
                #
                #   Los resultados de A_, B_, C_, D_ parecen tener coherencia
                #   Para un perfil simétrico el valor 0 y el m-3 son iguales
                #
                #   En el caso de R, los valores de Dy son simétricos y de
                #   sentido opuesto, los de Dx son simétricos
                ###############################################################
                if i - 1 == 0:
                    alpha_[0]   = B_[0]
                    beta_[0]    = np.linalg.inv(B_[0]) @ C_[0]
                    beta_[0]    = np.matmul(np.linalg.inv(B_[0]), C_[0])
                else:
                    alpha_[i - 1]   = B_[i - 1] - A_[i - 1] @ beta_[i - 2]
                    beta_[i - 1]    = np.linalg.inv(alpha_[i - 1]) @ C_[i - 1]

                R_[i - 1] = np.array([[Dx], [Dy]])

            # se resuelve LY_ = R
            #   se obtiene vector Y_
            Y_[0] = np.linalg.inv(alpha_[0]) @ R_[0]

            for i in range(1, m - 2):
                Y_[i] = np.linalg.inv(alpha_[i]) @ (R_[i] - A_[i] @ Y_[i - 1])
            # se resuelve Y_ = U_ * delta_Q
            # se obtienen valores de delta_Q que son el resultado final
            delta_Q[m - 3] = Y_[m - 3]

            for i in range(m - 4, -1, -1):
                delta_Q[i] = Y_[i] - beta_[i] @ delta_Q[i + 1]

            for i in range(0, m - 2):
                X[i + 1, j] = delta_Q[i][0, 0]
                Y[i + 1, j] = delta_Q[i][1, 0]
            print(delta_Q)
        return

    def tensor(self):
        """
        Calcula el tensor metrico de la malla
        ...

        Parametros
        ----------
        None

        Return
        ------
        (g11, g22, g12, J, x_xi, x_eta, y_xi, y_eta, A, B, C1) : numpy.array
            Matrices con los valores de la metrica de la transformacin para
            todos los nodos de la malla
        """

        '''
            Calcula el tensor métrico de la transformación para ambas
                transformaciones, directa e indirecta
            Calcula el Jacobiano de la matriz de transformación
            Calcula el valor discretizado de las derivadas parciales:
                x_xi
                x_eta
                y_xi
                y_eta
        '''

        # se definen vairables de la malla
        X       = self.X
        Y       = self.Y
        M       = self.M
        N       = self.N
        d_xi    = self.d_xi
        d_eta   = self.d_eta

        x_xi    = np.zeros((M, N))
        x_eta   = np.zeros((M, N))
        y_xi    = np.zeros((M, N))
        y_eta   = np.zeros((M, N))

        # cálculo de derivadas parciales
        # nodos internos
        x_eta[:-1, 1:-1] = (X[:-1, 2:] - X[:-1, :-2]) / 2 / d_eta
        y_eta[:-1, 1:-1] = (Y[:-1, 2:] - Y[:-1, :-2]) / 2 / d_eta

        x_eta[:-1, 0]   = (X[:-1, 1] - X[:-1, 0]) / d_eta
        x_eta[:-1, -1]  = (X[:-1, -1] - X[:-1, -2]) / d_eta
        x_eta[-1, :]    = x_eta[0, :]
        y_eta[:-1, 0]   = (Y[:-1, 1] - Y[:-1, 0]) / d_eta
        y_eta[:-1, -1]  = (Y[:-1, -1] - Y[:-1, -2]) / d_eta
        y_eta[-1, :]    = y_eta[0, :]

        x_xi[1:-1, :] = (X[2:, :] - X[:-2, :]) / 2 / d_xi
        y_xi[1:-1, :] = (Y[2:, :] - Y[:-2, :]) / 2 / d_xi
        x_xi[0, :]  = (X[1, :] - X[-2, :]) / 2 / d_xi
        y_xi[0, :]  = (Y[1, :] - Y[-2, :]) / 2 / d_xi
        x_xi[-1, :] = x_xi[0, :]
        y_xi[-1, :] = y_xi[0, :]

        # obteniendo los tensores de la métrica
        J       = (x_xi * y_eta) - (x_eta * y_xi)
        g11I    = x_xi ** 2 + y_xi ** 2
        g12I    = x_xi * x_eta + y_xi * y_eta
        g22I    = x_eta ** 2 + y_eta ** 2
        g11     = g22I / J ** 2
        g12     = -g12I / J ** 2
        g22     = g11I / J ** 2

        C1      = g11I
        A       = g22I
        B       = g12I

        return (g11, g22, g12, J, x_xi, x_eta, y_xi, y_eta, A, B, C1)

    def to_su2(self, filename):
        """
        Exporta la malla a un archivo de texto en formato de SU2.
        ...

        Parametros
        ----------
        filename : str
            nombre del archivo en el cual se exportara la malla.
            Debe incluir el path (relativo o absoluto)

        Return
        ------
        None
        """

        if self.airfoil_alone == True:
            mesh_su2.to_su2_mesh_o_airfoil(self, filename)
        else:
            mesh_su2.to_su2_mesh_o_airfoil_n_flap(self, filename)

        return
