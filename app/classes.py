import time
from app import socketio, app


class Manager:

    @staticmethod
    def create_config(config):

        del app.ecoe_rounds[:]

        for round_id in config['ruedas']:
            app.ecoe_rounds.append(Round(round_id, config['planificaciones'], config['vueltas']))


class Round:

    def __init__(self, id, schedules, num_reruns):
        self.id = id
        self.namespace = '/round%d' % id
        self.chrono = Chrono(id)
        self.schedules = schedules
        self.num_reruns = num_reruns

    def start(self):

        for reruns in range(self.num_reruns):

            for schedule in self.schedules:

                self.chrono.play(duration=schedule['duracion'], events=schedule['eventos'], stage=schedule['fase'])
                socketio.sleep(0.5)
                self.chrono.reset()

        socketio.emit('end', {'data': 'Fin rueda %s' % self.id}, namespace=self.namespace)


class Chrono:

    CREATED = 0
    RUNNING = 1
    PAUSED = 2
    FINISHED = 3

    def __init__(self, id, minutes=0, seconds=0):
        self.id = id
        self.namespace = '/round%d' % id
        self.minutes = minutes
        self.seconds = seconds
        self.state = Chrono.CREATED

    def reset(self):

        self.state = Chrono.CREATED
        self.minutes = 0
        self.seconds = 0

    def play(self, duration, events, stage):

        self.activate()

        for t in range(duration + 1):

            if t % 60 == 0 and self.seconds == 59:
                self.minutes += 1
                self.seconds = 0
            else:
                self.seconds = t % 60

            socketio.emit('tic_tac',
                          {
                              'minutes': '{:02d}'.format(self.minutes),
                              'seconds': '{:02d}'.format(self.seconds),
                              'stopped': 'S' if self.is_paused() else 'N',
                              'stage': stage
                          },
                          namespace=self.namespace)

            while self.is_paused():
                socketio.sleep(0.5)

            # send events
            for e in events:
                if e['t'] == t:
                    print (time.strftime("%H:%M:%S") + " [%s] Rueda %d enviando evento en t = %d para %s" % (stage, self.id, t, ','.join(map(str, e['estaciones']))))
                    socketio.emit('evento',
                                  {
                                      'data': e['accion'],
                                      'target': ','.join(map(str, e['estaciones']))
                                  },
                                  namespace=self.namespace)

            if t == duration:
                self.stop()
                break

            socketio.sleep(1)

    def activate(self):
        self.state = Chrono.RUNNING

    def stop(self):
        self.state = Chrono.FINISHED

    def pause(self):
        self.state = Chrono.PAUSED

    def is_paused(self):
        return self.state == Chrono.PAUSED
