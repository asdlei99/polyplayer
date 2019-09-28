import os
import types

import requests
from music_dl import config
from music_dl.source import MusicSource

from log import log

class MusicDL:
    def __init__(self, download_dir='downloads/', lyrics=True, cover=True):
        self.ms = MusicSource()
        config.init()

        self.song_list = []
        self.change_dl_dir(download_dir)

        config.set('lyrics', bool(lyrics))
        config.set('cover', bool(cover))

    def change_dl_dir(self, download_dir):
        self.download_dir = download_dir
        os.makedirs(self.download_dir, exist_ok=True)
        config.set('outdir', self.download_dir)

    def search(self, keyword, sources='all'):
        if sources == 'all':
            sources = ['baidu', 'netease', 'qq', 'kugou', 'migu']
        elif isinstance(sources, str):
            sources = [sources]
        elif isinstance(sources, tuple) or isinstance(sources, list):
            pass
        else:
            log.error('music sources type error.')
            raise ValueError

        self.song_list = self.ms.search(keyword, sources)
        return self.song_list

    def download(self, idx):
        song = self.song_list[idx]
        song.download_song = types.MethodType(download_song, song)  # replace method
        song.download()


def download_song(self):
    if self.song_url:
        download_file(self.song_url, self.song_fullname, stream=True)

    if self.lyrics_url and config.get('lyrics'):
        self._download_file(self.lyrics_url, self.lyrics_fullname, stream=False)

    if self.cover_url and config.get('cover'):
        self._download_file(self.cover_url, self.cover_fullname, stream=False)


def download_file(url, output_path, stream=True):
    if not url:
        log.error("URL is empty.")
        return
    try:
        r = requests.get(
            url,
            stream=stream,
            headers=config.get("wget_headers"),
            proxies=config.get("proxies"),
        )
        if stream:
            # implement cache playing later
            total_size = int(r.headers["content-length"])
            with open(output_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                f.close()
        else:
            with open(output_path, "wb") as f:
                f.write(r.content)
                f.close()
    except Exception as e:
        log.error(e)


if __name__ == '__main__':
    mdl = MusicDL()
    mdl.search('泡沫')

    mdl.download(0)
    mdl.download(1)
