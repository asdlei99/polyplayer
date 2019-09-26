import os

from music_dl import config
from music_dl.source import MusicSource


class MusicDL:
    def __init__(self, download_dir='downloads/', lyrics=True, cover=True):
        self.ms = MusicSource()
        config.init()

        self.song_list = []
        self.change_dl_dir(download_dir)

        if lyrics:
            config.set('lyrics', True)
        if cover:
            config.set('cover', True)

    def change_dl_dir(self, download_dir):
        self.download_dir = download_dir
        os.makedirs(self.download_dir, exist_ok=True)
        config.set('outdir', self.download_dir)

    def search(self, keyword):
        keyword = '泡沫'
        source = ['baidu', 'netease', 'qq', 'kugou']

        self.song_list = self.ms.search(keyword, source)

    def download(self, idx):
        self.song_list[idx].download()


if __name__ == '__main__':
    mdl = MusicDL()
    mdl.search('泡沫')

    mdl.download(0)
    mdl.download(1)
