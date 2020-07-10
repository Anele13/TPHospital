from flask import Flask, render_template,request
import numpy as np
import statistics as stats
import json
app = Flask(__name__)

class Paciente():
    def __init__(self,prefijo,tipo):
        self.prefijo = prefijo
        self.tiempoLlegada = round(np.random.poisson(220)) #llegada de pacienes con media=220 y poisson
        self.tipo = tipo
        if tipo == "INTERNACION":
            self.duracionInternacion = round(np.random.uniform(1,3)) * (24*60)
        else: # operacion
            self.duracionInternacion = round(np.random.uniform(2,5)) * (24*60) #2 y 5 días para pacientes operados 
            self.duracionOperacion = np.random.uniform(1,6) * 60


class Cama():
    def __init__(self, id):
        self.id = id
        self.ocupada = False
        self.contador_ocupacion = 0
    
    def marcarOcupada(self):
        self.ocupada = True
    
    def marcarDesocupada(self):
        self.ocupada = False
    
    def actualizar_ocupacion(self):
        self.contador_ocupacion += 1


class Quirofano():
    def __init__(self,id):
        self.id = id
        self.ocupado = False
        self.abierto = True
        self.tiempoOcupacion = 0
    
    def marcarOcupado(self):
        self.ocupado = True
    
    def marcarDesocupado(self):
        self.ocupado = False
    
    def actualizarTiempoOcupacion(self, tiempo):
        self.tiempoOcupacion += tiempo


class Evento():
    def __init__(self, _id, nombre, objeto, arribo, duracion):
        self.id = _id
        self.nombre = nombre
        self.arribo = arribo
        self.duracion = duracion
        self.tiempo_fin = arribo + duracion
        self.objeto = objeto
        
    def __repr__(self):
        return "f{self.id} - {self.nombre} - arribo: {self.arribo} - duracion: {self.duracion} - termina: {self.tiempo_fin}\n"


class EventoFinalizacion(Evento):
    def __init__(self, evento_inicio, **kwargs):
        Evento.__init__(self,**kwargs)
        self.evento_inicio = evento_inicio
    
    def __repr__(self):
        return "f{self.id} - {self.nombre} a {self.evento_inicio.id} - inicia: {self.arribo} - duracion: {self.duracion} - termina: {self.tiempo_fin}\n"


def hayCamaLibre(lista_camas):
    """
    Consulta si hay una cama libre
    """
    return any(not cama.ocupada for cama in lista_camas)


def hayQuirofanoLibre(lista_quirofanos):
    """
    Consulta si hay un quirofano libre
    """
    return any(not quirofano.ocupado for quirofano in lista_quirofanos)


def ordenarEventos(fel):
    """
    Ordena la lista de eventos por tiempod de arribo
    """
    fel.sort(key=lambda evento: evento.arribo)
    return fel


def removerEvento(fel, evento):
    """
    remueve el siguiente evento de la FEL
    """
    if evento in fel:
        fel.remove(evento)
    return ordenarEventos(fel)

def crearFEL(paciente, cantidad_pacientes):
    """
    Crea la FEL con eventos de arribo paciente segun el tipo
    de paciente y la cantidad de pacientes que arriban
    """
    lista_eventos = []
    for i in range(cantidad_pacientes):
        lista_eventos.append()
    return ordenarEventos(lista_eventos)


def agregar_eventos_llegada(fel, prefijo, cantidad_pacientes, solo_operacion):
    """
    En este caso corrida va a ir a la par con el reloj
    """
    contador_tipo_paciente = {"OPERACION":0,"INTERNACION":0}
    #Inicializamos la fel
    for id_paciente in range(cantidad_pacientes): 
        tipoPaciente = None
        indicador = round(np.random.uniform(0,100))
        
        if (indicador <= 20): #el 20% de los pacientes vienen a operarse
            tipoPaciente = "OPERACION"
        else: #el restante 80% solo viene a internarse
            tipoPaciente= "INTERNACION"

        contador_tipo_paciente[tipoPaciente] = contador_tipo_paciente[tipoPaciente]+1
        paciente = Paciente("f{prefijo}-C{id_paciente}",tipoPaciente)

        if solo_operacion:
            if (tipoPaciente == "OPERACION"):
                evento = Evento(paciente.prefijo, "INGRESA_PACIENTE", paciente, paciente.tiempoLlegada, 0)
                agregarEventoAFel(evento, fel)
        else:
            evento = Evento(paciente.prefijo, "INGRESA_PACIENTE", paciente, paciente.tiempoLlegada, 0)
            agregarEventoAFel(evento, fel)

    return fel, contador_tipo_paciente


def inicializar_camas(cantidad_camas):
    lista_camas = []
    #Inicializamos las camas
    for i in range(cantidad_camas):
        lista_camas.append(Cama(i))
    return lista_camas

    
def getCamaLibre(lista_camas):
    for cama in lista_camas:
        if (not cama.ocupada): 
            return cama


def getQuirofanoLibre(lista_quirofanos):
    for quirofano in lista_quirofanos:
        if (not quirofano.ocupado): 
            return quirofano


def agregarEventoAFel(evento, fel):
    """
    Esta funcion agrega eventos al diccionario fel. Si el diccionario
    tiene eventos en la lista, agrega el evento a la lista existente.
    la clave de la fel es el tiempo de llegada del evento que es un entero
    """
    lista_eventos = fel.get(evento.arribo, None)
    if lista_eventos:
        fel[evento.arribo].append(evento) #agrego el evento a la lista de eventos existente
    else:
        fel[evento.arribo]=[evento] #agrego la lista de eventos para ese momento de reloj en la fel


def modificar_horario_eventos(fel,tope_reloj):
    fel2 = {}
    for k in fel:
        for e in fel[k]:
            e.arribo -= tope_reloj
            agregarEventoAFel(e,fel2)
    return fel2


def inicializar_quirofanos(cant):
    lista_quirofanos = []
    for i in range(cant):
        lista_quirofanos.append(Quirofano(i))
    return lista_quirofanos


def operar(fel, quirofano, e, reloj):
    paciente = e.objeto
    quirofano.marcarOcupado()
    quirofano.actualizarTiempoOcupacion(paciente.duracionOperacion)
    evento_fin_operacion = EventoFinalizacion(evento_inicio=e, #evento_inicio es el evento arribo relacionado al evento Fin
                                            nombre="FINALIZA_OPERACION", 
                                            objeto=quirofano, 
                                            _id="f{i}{j}",
                                            arribo=reloj + paciente.duracionOperacion, 
                                            duracion=paciente.duracionOperacion) 
    agregarEventoAFel(evento_fin_operacion, fel)


def internar(fel, cama, e, reloj):
    paciente = e.objeto
    cama.marcarOcupada()
    cama.actualizar_ocupacion()
    evento_fin_internacion = EventoFinalizacion(evento_inicio=e, #evento_inicio es el evento arribo relacionado al evento Fin
                                                nombre="FINALIZA_INTERNACION", 
                                                objeto=cama, 
                                                _id="f{i}{j}",
                                                arribo=reloj + paciente.duracionInternacion, 
                                                duracion=paciente.duracionInternacion) 
    agregarEventoAFel(evento_fin_internacion, fel)


def getEventosPorCondicion(lista_eventos):
    """
    Esta funcion sirve para determinar cuales eventos de una lista de eventos 
    en un instante de reloj son para ser realizados en las actividades de 
    quirofano libre o cama libre.
    """
    eventos_internarse=[]
    eventos_operarse = []
    eventos_fin_internacion = []
    eventos_fin_operacion = []

    for evento in lista_eventos:
        if evento.nombre == "INGRESA_PACIENTE":
            if evento.objeto.tipo == "INTERNACION":
                eventos_internarse.append(evento)
            else:
                eventos_operarse.append(evento)
        
        elif evento.nombre == "INICIA_OPERACION":
            eventos
        
        elif evento.nombre == "FINALIZA_OPERACION":
            eventos_fin_operacion.append(evento)
        
        else: # FIN DE INTERNACION o Alta de un paciente
            eventos_fin_internacion.append(evento)
    return eventos_internarse, eventos_operarse, eventos_fin_internacion, eventos_fin_operacion



def simulacion(indicador, cant_experimentos, cant_corridas, cant_pacientes, cant_quirofanos, cant_camas, apertura_quirofano, cierre_quirofano):    # Esqueleto para simulación con escaneo de actividades
    APERTURA = apertura_quirofano * 60
    CIERRE = cierre_quirofano * 60
    delta = 1 # Incremento para el valor del reloj
    tope_reloj = 24*60 # Definimos un punto para cortar la ejecución, en este caso 24 hs (en minutos)
    esperas = [] #Espera por una cama experimento
    esperas_camas = []
    esperas_quirofanos = []
    camas_desocupadas = []
    lista_quirofanos = inicializar_quirofanos(cant_quirofanos)
    contador_tipo_paciente = {"OPERACION":0,"INTERNACION":0}
    lista_pacientes_no_atendidos = []
    lista_pacientes_no_operados = []


    for i in range(cant_experimentos):
        fel ={}
        espera_camas = []
        espera_quirofanos = []
        cant_camas_desocupadas = 0
        lista_camas =inicializar_camas(cant_camas)
        pacientes_no_atendidos = []
        pacientes_no_operados = []

        for j in range(cant_corridas):
            prefijo = "f{i}{j}" # un prefijo para identificar los eventos de cada experimento/corrida
            fel, contador_paciente = agregar_eventos_llegada(fel, prefijo, cant_pacientes, indicador)
            cola_camas = []
            cola_quirofanos = []
            reloj = list(sorted(fel))[0] # Iniciamos/reiniciamos el reloj

            while reloj <= tope_reloj and len(fel) != 0:
                # Obtenemos todos los eventos diferenciados desde la lista de eventos
                eventos_internarse, eventos_operarse, eventos_fin_internacion, eventos_fin_operacion = getEventosPorCondicion(fel[reloj])
                
                # Si hay eventos de finalizacion los hago primero para poder seguir procesando nuevas llegadas
                if (eventos_fin_internacion or eventos_fin_operacion):
                    for evento in eventos_fin_internacion:
                        cama = evento.objeto #si evento es fin de internacion el objeto es una cama
                        cama.marcarDesocupada()
                        if len(cola_camas) != 0:#Si hay un paciente esperando lo interno
                            e = cola_camas[0]
                            internar(fel, cama, e, reloj)
                            espera_camas.append(reloj - e.objeto.tiempoLlegada)
                            cola_camas.remove(e)
                            if e.objeto.tipo == "OPERACION":
                                e.objeto.tiempoLlegada = reloj
                                cola_quirofanos.append(e)
                                
                        
                    for evento in eventos_fin_operacion:
                        quirofano = evento.objeto #si evento es fin de operacion el objetoes un quirofano
                        quirofano.marcarDesocupado()
                        if len(cola_quirofanos) != 0 and (APERTURA >= reloj <= CIERRE):#asigno quirofano
                            e = cola_quirofanos[0]
                            operar(fel, quirofano, e, reloj)
                            espera_quirofanos.append(reloj - e.objeto.tiempoLlegada)
                            cola_quirofanos.remove(e)
                            

                    # Procesamos eventos que ocurren en este momento de reloj
                    # y que puedan procesarse bajo esta condicion
                if hayCamaLibre(lista_camas):
                    for e in eventos_internarse:
                        cama = getCamaLibre(lista_camas)
                        if cama != None: 
                            internar(fel, cama, e, reloj)
                            espera_camas.append(reloj - e.objeto.tiempoLlegada)
                        else:
                            cola_camas.append(e)
                else:#Ponemos a los pacientes en espera
                    for e in eventos_internarse:
                        cola_camas.append(e)
                    
                if hayQuirofanoLibre(lista_quirofanos) and hayCamaLibre(lista_camas) and (APERTURA >= reloj <= CIERRE) :
                    # Ejecutamos actividad con todos los eventoss
                    for e in eventos_operarse:
                        paciente = e.objeto
                        quirofano = getQuirofanoLibre(lista_quirofanos)
                        cama = getCamaLibre(lista_camas)
                        if cama!= None:
                            internar(fel, cama, e, reloj)
                            espera_camas.append(reloj - e.objeto.tiempoLlegada)
                            if quirofano != None:
                                operar(fel, quirofano, e, reloj)
                                espera_quirofanos.append(reloj - e.objeto.tiempoLlegada)
                            else: 
                                cola_quirofanos.append(e)
                        else:
                            cola_camas.append(e)
                else:#Ponemos a los pacientes en espera de una cama o quirofano
                    if not hayCamaLibre(lista_camas):
                        for e in eventos_internarse:
                            cola_camas.append(e)
                    else:
                        for e in eventos_operarse:
                            cola_quirofanos.append(e)
                        
                
                # Retiramos eventos procesados de la fel para el instante correspondiente
                fel.pop(reloj)
                
                if (len(fel)!= 0):
                    reloj = list(sorted(fel))[0] # Avanzamos el reloj al siguiente incremento.
                    if reloj > tope_reloj:
                        fel = modificar_horario_eventos(fel,tope_reloj)

                pacientes_no_atendidos.append(len(cola_camas))
                pacientes_no_operados.append(len(cola_quirofanos))

            # Finalizó el procesamiento para esta corrida, hacemos la estadistica necesaria por corrida aqui
            for cama in lista_camas:
                if cama.contador_ocupacion == 0:
                    cant_camas_desocupadas +=1
            
            for k,v in contador_paciente.items():
                contador_tipo_paciente[k] = contador_tipo_paciente[k] + v
            

        # Finalizó el procesamiento para este experimento, hacemos la estadistica necesaria por experimento aqui
        lista_pacientes_no_atendidos.append(round(sum(pacientes_no_atendidos)/len(pacientes_no_atendidos),2))
        lista_pacientes_no_operados.append(round(sum(pacientes_no_operados)/len(pacientes_no_operados),2))
        if (espera_quirofanos and espera_camas):
            espera = round((stats.mean(espera_camas) + stats.mean(espera_quirofanos)),2)
            esperas_camas.append(round(stats.mean(espera_camas),2))
            esperas_quirofanos.append(round(stats.mean(espera_quirofanos),2))
            esperas.append(espera)
        camas_desocupadas.append(round((cant_camas_desocupadas / cant_corridas),2))

        
    return lista_pacientes_no_operados, lista_pacientes_no_atendidos, esperas, esperas_camas, esperas_quirofanos, camas_desocupadas, lista_quirofanos, contador_tipo_paciente


@app.route('/iniciar_simulacion',methods=['POST'])
def iniciar_simulacion():
    cant_experimentos = int(request.form.get('cant_experimentos'))
    cant_corridas = int(request.form.get('cant_corridas'))
    cant_pacientes = int(request.form.get('cant_pacientes'))
    cant_quirofanos = int(request.form.get('cant_quirofanos'))
    cant_camas = int(request.form.get('cant_camas'))
    cierre = int(request.form.get('cierre'))
    apertura = int(request.form.get('apertura'))
    indicador = request.form.get('indicador')
    if (indicador):
        indicador = True
    else:
        indicador = False
    
    indicador = False

    lista_pacientes_no_operados, lista_pacientes_no_atendidos, esperas, esperas_camas, esperas_quirofanos, camas_desocupadas, lista_quirofanos, contador_tipo_paciente = simulacion(indicador, cant_experimentos,cant_corridas, cant_pacientes, cant_quirofanos, cant_camas, apertura, cierre)
    _cierre = cierre * 60
    _apertura = apertura * 60
    tiempo_total = np.abs((_cierre - _apertura) * (cant_experimentos * cant_corridas))
    ocupacion_quirofanos = {q.id: round(((q.tiempoOcupacion/tiempo_total)*100),2) for q in lista_quirofanos}


    tope = cant_corridas * cant_experimentos * cant_pacientes
    contexto = {"lista_pacientes_no_operados":lista_pacientes_no_operados,
                "lista_pacientes_no_atendidos":lista_pacientes_no_atendidos,
                "esperas":esperas,
                "esperas_camas":esperas_camas,
                "esperas_quirofanos":esperas_quirofanos,
                "camas_desocupadas":camas_desocupadas,
                "lista_quirofanos":lista_quirofanos,
                "porcentaje_camas_desocupadas":round(stats.mean(camas_desocupadas))/cant_camas * 100,
                "ocupacion_quirofanos" : json.dumps(ocupacion_quirofanos),
                "tiempo_total":tiempo_total,
                "contador_tipo_paciente": json.dumps({k:round((v/tope*100),2) for k,v in contador_tipo_paciente.items()}),
                "cant_experimentos":cant_experimentos,
                "cant_corridas":cant_corridas,
                "cant_pacientes":cant_pacientes,
                "cant_quirofanos":cant_quirofanos,
                "cant_camas":cant_camas,
                "apertura":apertura,
                "cierre":cierre}
    return render_template('index.html',contexto=contexto, ocupacion_quirofanos=json.dumps(ocupacion_quirofanos))


@app.route("/")
def main():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)