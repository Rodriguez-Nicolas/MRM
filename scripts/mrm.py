# GNU GENERAL PUBLIC LICENSE
# MRM: módulo para el cálculo hidrológico por el Método Racional Modificado
# Copyright (C) <2022>  Juan F. Weber <jweber at frc dot utn dot edu dot ar>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

########################################################################

import numpy as np
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use('TkAgg')
import PySimpleGUI as sg


########################################################################

def GeneraH(C, i, A, d, tc, D):
    '''
	Funcion GeneraH
	genera hidrograma de descarga segun el Metodo Racional Modificado
	------ DATOS
	*C: coeficiente del Método Racional (ad.)
	i: intensidad de lluvia (mm/h)
	*A: area de la cuenca (ha)
	d: duracion de la lluvia (min)
	*tc: tiempo de concentracion de la cuenca (min)
	D: duracion de la simulacion (min)
	------ RESULTADO
	Q = [[t0, t1, t2, ..., tn]
		 [Q0, Q1, Q2, ..., Qn]]
	ti en min ; Qi en m³/s
	------
	Autor: Juan F. Weber
	Fecha: oct'22
	'''

    L = [[0.], [0.]]  # lista de resultados
    Qp = C * i / (1000 * 3600) * A * 10000  # caudal pico s/ metodo Racional
    if d <= tc:
        L[0].append(d)
        L[1].append(Qp * d / tc)  # Q maximo (menor a Qp)
        L[0].append(2 * d)
        L[1].append(0)  # vaciado del hidrograma
    else:
        L[0].append(tc)
        L[1].append(Qp)  # Q pico (inicio del plafon)
        L[0].append(d)
        L[1].append(Qp)  # Q pico (fin del plafon)
        L[0].append(d + tc)
        L[1].append(0)  # vaciado del hidrograma

    L[0].append(D)
    L[1].append(0)  # extension del hidrograma hasta D

    #print(L)

    Q = np.array(L)  # conversion a array de Numpy

    return Q


########################################################################	

def TrasladaH(Qe, tr):
    '''
	Funcion TrasladaH
	traslada hidrograma de descarga segun el Metodo Racional Modificado
	------ DATOS

	tr = tiempo de retardo en min
	*Qe: array de Numpy
	Qe = [[t0, t1, t2, ..., tn]
		 [Q0, Q1, Q2, ..., Qn]]
	t en min ; Qi en m³/s
	------ RESULTADO
	Qs: array de Numpy
	Qs = [[t0+tr, t1+tr, t2+tr, ..., tn+tr]
		  [   Q0,    Q1,    Q2, ...,    Qn]]
	t en min ; Qi en m³/s
	------
	Autor: Juan F. Weber
	Fecha: oct'22
	'''

    Qs = np.ndarray.copy(Qe)
    D = Qs[0, -1]  # conserva t final (duracion D)
    Qs[0] += tr  # traslada el hidrograma
    Qs[0, -1] = D  # corrige el t final a D
    #  se agrega el origen del hidrograma
    Qs = np.column_stack((np.array((0, 0)), Qs))

    return Qs


########################################################################

def SumaH(Q1, *Qs):
    '''
    Funcion SumaH
    suma (superpone) hidrogramas de descarga segun el
    Metodo Racional Modificado en confluencias
    ------ DATOS
    Q1, Q2, Q3, ...: arrays de Numpy
    Qi = [[t0, t1, t2, ..., tn]
          [Q0, Q1, Q2, ..., Qn]]
    ti en min ; Qi en m³/s
    ------ RESULTADO
    Q: array de Numpy
    Q = [[t0, t1, t2, ..., tn]
         [Q0, Q1, Q2, ..., Qn]]
    t en min ; Qi en m³/s
    ------
    Autor: Juan F. Weber
    Fecha: oct'22
    '''
    Q = Q1
    for Q2 in Qs:
        # interpola Q en Q2  y lo suma a Q2 --> Q3
        Qtemp = np.vstack((Q[0], np.interp(Q[0], Q2[0], Q2[1])))
        Q3 = np.vstack((Q[0], Q[1] + Qtemp[1]))

        # interpola Q2 en Q y lo suma a Q --> Q4
        Qtemp = np.vstack((Q2[0], np.interp(Q2[0], Q[0], Q[1])))
        Q4 = np.vstack((Q2[0], Q2[1] + Qtemp[1]))

        # concatena los dos arrays
        Q5 = np.column_stack((Q3, Q4))

        # ordena el resultado
        ind = np.argsort(Q5.T[:, 0]);
        Q6 = Q5.T[ind];
        Q6 = Q6.T

        # simplifica la geometria
        (f, c) = np.shape(Q6)
        ind = []
        for i in range(c - 1):
            if Q6[0, i] == Q6[0, i + 1]:
                ind = ind + [i]

        Q = np.delete(Q6, ind, 1)

    return Q


########################################################################

def grafica(Q, nombre=''):
    if nombre != '':
        plt.plot(Q[0], Q[1], linewidth=3, label=nombre)
    else:
        plt.plot(Q[0], Q[1], linewidth=3)
    plt.ylabel('Q (m³/s)')
    plt.xlabel('t (min)')
    plt.grid()
    if nombre != '':
        plt.legend()

    return


########################################################################

def MuestraH(Q, nombre=''):
    '''
	Funcion MuestraH
	presenta en una ventana grafica el hidrograma de descarga
	como tabla y, opcionalmente, como grafico
	------ DATOS
	Q: array de Numpy
	Q = [[t0, t1, t2, ..., tn]
		 [Q0, Q1, Q2, ..., Qn]]
	ti en min ; Qi en m³/s
	nombre: nombre de la gráfica en la leyenda - si no se indica
	no se agrega leyenda
	------ RESULTADOS
	tabla
	t (min)	Q (m³/s)
	grafico con MatPlotLib.Pyplot haciendo clic en <<grafico>>
	------
	Autor: Juan F. Weber
	Fecha: dic'22
	'''
    ## construyendo la tabla como texto
    N = len(Q[0])
    texto = 't (min)\tQ (m³/s)\n'
    for i in range(0, N):
        texto += ('%.2f\t%.4f\n' % (Q[0, i], Q[1, i]))

    sg.theme('DarkAmber')  # colores

    layout = [[sg.Multiline(texto, size=(40, None), font='Courier 12',
                            write_only=True)], [sg.Button('Ok'), sg.Button('Grafico')]]

    window = sg.Window(nombre, layout)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Ok':
            break
        elif event == 'Grafico':
            grafica(Q, nombre)
            plt.show(block=False)

    window.close()