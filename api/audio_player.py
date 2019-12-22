from concurrent.futures import ThreadPoolExecutor
import os

import pyaudio
from pydub.utils import make_chunks

from pydub import AudioSegment

from utils.logger import log

player = pyaudio.PyAudio()
pool = ThreadPoolExecutor(1)


class AudioPlayer:
    def __init__(self, music_file_path, buffer_time=500):
        self.basename = os.path.basename(music_file_path)
        self.format = os.path.splitext(self.basename)[-1][1:]

        # load music into memory
        self.sound = AudioSegment.from_file(music_file_path, self.format)

        # prepare player
        self.stream = player.open(format=player.get_format_from_width(self.sound.sample_width),
                                  channels=self.sound.channels,
                                  rate=self.sound.frame_rate,
                                  output=True)

        self.buffer_time = buffer_time
        self.chunks = make_chunks(self.sound, self.buffer_time)

        self.current_chunk_idx = 0
        self.is_playing = False
        self.is_paused = False
        self.is_stopped = False

        # preprocess the whole sound
        self.sound = self.preprocess(self.sound)

    @staticmethod
    def preprocess(audio_seg):
        # TODO: add plugin later, such as volume gain, fading, etc.
        return audio_seg

    @staticmethod
    def onplay_process(audio_seg):
        # TODO: add plugin later, such as volume gain, fading, etc.
        return audio_seg

    def play(self, start_at: int = 0):
        def _proc(start_at):
            if start_at == 0:
                log.info('play {}'.format(self.basename))
            elif start_at > 0:
                log.info('continue {}'.format(self.basename))

            self.current_chunk_idx = start_at

            self.is_playing = True

            # for chunk in self.chunks[start_at:]:
            while True:
                chunk = self.chunks[self.current_chunk_idx]

                chunk = self.onplay_process(chunk)

                self.stream.write(chunk.raw_data)  # play sound

                self.current_chunk_idx += 1
                if self.current_chunk_idx == len(self.chunks[start_at:]):
                    self.current_chunk_idx = 0
                    self.is_playing = False
                    log.info('finished {}'.format(self.basename))
                    break

                if self.is_paused:
                    self.is_playing = False
                    log.info('paused {}'.format(self.basename))
                    break

                if self.is_stopped:
                    self.stream.stop_stream()
                    self.stream.close()
                    self.is_playing = False
                    log.info('stopped {}'.format(self.basename))

        if not self.is_stopped and not self.is_playing:
            pool.submit(_proc, start_at)
        else:
            log.warn('can\'t play the same song simultaneously')

    def pause(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            log.info('pause {}'.format(self.basename))
            return
        else:
            self.play(self.current_chunk_idx)

    def stop(self):
        self.is_stopped = True
        log.info('stop {}'.format(self.basename))


if __name__ == '__main__':
    import time

    ap = AudioPlayer('downloads/hanser.mp3')

    ap.play(150)
    time.sleep(5)
    ap.pause()
    time.sleep(5)
    ap.pause()

    ap.play(375)

    ap.play(0)
    time.sleep(5)

    ap.pause()
    time.sleep(2)

    ap.pause()
    time.sleep(5)

    ap.stop()
    ap = None
