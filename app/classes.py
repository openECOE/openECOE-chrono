import time
from app import socketio


class Round:

    def __init__(self, id, events):
        self.id = id
        self.namespace = '/round%d' % id
        self.chrono = None
        self.events = events

    def start(self):

        self.chrono.play(self.namespace, self.events)
        socketio.emit('end', {'data': 'Fin ecoe round %s' % self.id}, namespace=self.namespace)


class Chrono:

    CREATED = 0
    RUNNING = 1
    PAUSED = 2
    FINISHED = 3

    def __init__(self, id, duration, events=[], minutes=0, seconds=0):
        self.id = id
        self.duration = duration
        self.namespace = '/round%d' % id
        self.events = events
        self.minutes = minutes
        self.seconds = seconds
        self.state = Chrono.CREATED

    def play(self):

        self.activate()

        for t in range(self.duration + 1):

            if t % 60 == 0 and self.seconds == 59:
                self.minutes += 1
                self.seconds = 0
            else:
                self.seconds = t % 60

            socketio.emit('tic_tac',
                          {
                              'minutes': '{:02d}'.format(self.minutes),
                              'seconds': '{:02d}'.format(self.seconds),
                              'stopped': 'S' if self.is_paused() else 'N'
                          },
                          namespace=self.namespace)

            while self.is_paused():
                socketio.sleep(0.5)

            # send events
            for e in self.events:
                if e['t'] == t:
                    print (time.strftime("%H:%M:%S") + " Rueda %d enviando evento en t = %d para %s" % (self.id, t, ','.join(map(str, e['estaciones']))))
                    socketio.emit('evento',
                                  {
                                      'data': e['salida'],
                                      'target': ','.join(map(str, e['estaciones']))
                                  },
                                  namespace=self.namespace)

            if t == self.duration:
                self.stop()
                break

            socketio.sleep(1)

        socketio.emit('end', {'data': 'Round %s ended' % self.id}, namespace=self.namespace)

    def activate(self):
        self.state = Chrono.RUNNING

    def stop(self):
        self.state = Chrono.FINISHED

    def pause(self):
        self.state = Chrono.PAUSED

    def is_paused(self):
        return self.state == Chrono.PAUSED
