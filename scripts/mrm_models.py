from mrm import GeneraH, TrasladaH, SumaH

class interface_elemento:
    def calcular_hidrograma(self, duracion_simulacion):
        pass

class Precipitacion:
    def __init__(self, identificador, intensidad, duracion):
        self.id = identificador # string que identifica una lluvia
        self.i = intensidad  # intensidad de la lluvia (mm/h)
        self.d = duracion  # duracion de la lluvia (min)

    def get_intensidad(self):
        return self.i

    def get_duracion(self):
        return self.d


class Subcuenca(interface_elemento):
    def __init__(self, identificador, area, coheficiente_c, tiempo_de_concentracion):
        self.id = identificador     # String que identifica la subcuenca
        self.A = area  # Area de la subcuenca (ha)
        self.C = coheficiente_c  # Coheficiente del metodo racional (ad.)
        self.tc = tiempo_de_concentracion  # Tiempo de concentracion de la cuenca (min)
        self.P = None  # Objeto preciopitacion asociado a la cuenca

    def set_precipitacion(self, precipitacion):
        self.P = precipitacion

    def calcular_hidrograma(self, duracion_simulacion):
        q = GeneraH(self.C, self.P.get_intensidad(), self.A, self.P.get_duracion(), self.tc, duracion_simulacion)
        return q


class Canal(interface_elemento):
    def __init__(self, tiempo_de_retardo):
        self.tr = tiempo_de_retardo  # Tiempo de retardo (min)
        self.Qe = None

    def set_entrada(self, entrada):  # Union de entrada al canal
        self.Qe = entrada

    def calcular_hidrograma(self, duracion_simulacion):
        qs = TrasladaH(self.Qe, self.tr)
        return qs

class Union:
    def __init__(self):
        self.Sn = []  # Array de subcuencas y canales de entrada

    def set_entrada(self, entrada):
        self.Sn.append(entrada)

    def sumar_hidrogrmas(self, duracion_simulacion):
        hidrogramas = []
        for s in self.Sn:
            hidrogramas.append(s.calcular_hidrograma(duracion_simulacion))
        q = SumaH(*hidrogramas)
        return q
