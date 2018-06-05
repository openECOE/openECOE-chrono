import time
from app import socketio, app
import json
import os


class Manager:

    @staticmethod
    def create_config(config):

        del app.ecoe_rounds[:]

        for round_id in config['rounds_id']:
            app.ecoe_rounds.append(Round(round_id, config['schedules'], config['reruns']))

        with open('ecoe_config.json', 'w') as f:
            json.dump(config, f)

    @staticmethod
    def load_status_from_file(filename):

        status = {}

        try:
            with open(filename, 'r') as json_file:
                status = json.load(json_file)
        except FileNotFoundError:
            pass

        return status

    @staticmethod
    def delete_file(filename):

        try:
            os.remove(filename)
        except:
            pass


class Round:

    CREATED = 0
    RUNNING = 1
    ABORTED = 2

    def __init__(self, id, schedules, num_reruns):
        self.id = id
        self.namespace = '/round%d' % id
        self.chrono = Chrono(id, self.namespace)
        self.schedules = schedules
        self.num_reruns = num_reruns
        self.state = Round.CREATED

    def abort(self):
        self.state = Round.ABORTED

    def is_aborted(self):
        return self.state == Round.ABORTED

    def dump(self, current_rerun, current_idx_schedule):

        status = {
            'state': self.state,
            'current_rerun': current_rerun,
            'current_idx_schedule': current_idx_schedule
        }

        with open(self.status_filename, 'w') as f:
            json.dump(status, f)

    @property
    def status_filename(self):
        return 'round.%d.status' % self.id

    def start(self, state=RUNNING, current_rerun=1, idx_schedule=0):

        self.state = state

        for n_rerun in range(current_rerun, self.num_reruns + 1):

            for idx, schedule in enumerate(self.schedules[idx_schedule:]):

                if self.is_aborted():
                    break

                socketio.emit('init_stage', {'num_rerun': n_rerun, 'total_reruns': self.num_reruns}, namespace=self.namespace)
                self.dump(n_rerun, idx)

                self.chrono.play(schedule, current_rerun=n_rerun, total_reruns=self.num_reruns)

                socketio.sleep(1)
                self.chrono.reset()

            # reset index for next iteration
            idx_schedule = 0

            if self.is_aborted():
                socketio.emit('aborted', {}, namespace=self.namespace)
                break

        if not self.is_aborted():
            socketio.emit('end_round', {'data': 'Fin rueda %s' % self.id}, namespace=self.namespace)

        Manager.delete_file(self.status_filename)


class Chrono:

    CREATED = 0
    RUNNING = 1
    PAUSED = 2
    FINISHED = 3

    def __init__(self, id, namespace, minutes=0, seconds=0):
        self.id = id
        self.namespace = namespace
        self.minutes = minutes
        self.seconds = seconds
        self.state = Chrono.CREATED

    def reset(self):

        self.state = Chrono.CREATED
        self.minutes = 0
        self.seconds = 0

    def dump(self):

        status = {
            'minutes': self.minutes,
            'seconds': self.seconds,
            'state': self.state
        }

        with open(self.status_filename, 'w') as f:
            json.dump(status, f)

    @property
    def status_filename(self):
        return 'chrono.%d.status' % self.id

    def _create_tic_tac_dict(self, t, current_rerun, total_reruns, schedule):

        return {
            't': t,
            'minutes': '{:02d}'.format(self.minutes),
            'seconds': '{:02d}'.format(self.seconds),
            'stopped': 'S' if self.is_paused() else 'N',
            'num_rerun': current_rerun,
            'total_reruns': total_reruns,
            'stage': schedule
        }

    def play(self, schedule, current_rerun, total_reruns):

        duration = schedule['duration']
        events = schedule['events']
        stage_name = schedule['name']

        self.activate()

        start_second = self.minutes*60 + self.seconds

        for t in range(start_second, duration + 1):

            if self.state == Chrono.FINISHED:
                break

            if t % 60 == 0 and self.seconds == 59:
                self.minutes += 1
                self.seconds = 0
            else:
                self.seconds = t % 60

            tic_tac = self._create_tic_tac_dict(t, current_rerun, total_reruns, schedule)

            socketio.emit('tic_tac', tic_tac, namespace=self.namespace)
            self.dump()

            while self.is_paused():
                socketio.emit('tic_tac', tic_tac, namespace=self.namespace)
                socketio.sleep(0.5)

            # send events
            for e in events:
                if e['t'] == t:
                    # TODO: Change print values to UTF8 or use logger library
                    #print (time.strftime("%H:%M:%S") + " [%s] Rueda %d enviando evento en t = %d para %s" % (stage_name, self.id, t, ','.join(map(str, e['stations']))))
                    socketio.emit('evento',
                                  {
                                      'data': e['message'],
                                      'sound': e['sound'],
                                      'stage': schedule,
                                      'target': ','.join(map(str, e['stations']))
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
        Manager.delete_file(self.status_filename)

    def pause(self):
        self.state = Chrono.PAUSED

    def is_paused(self):
        return self.state == Chrono.PAUSED
