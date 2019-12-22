from concurrent.futures import ThreadPoolExecutor
import dataset

"""
zerorpc communication
"""

class DB:
    def __init__(self, db_filepath):
        self.db_filepath = db_filepath
        self.pool = ThreadPoolExecutor(1)
        self.pool.submit(self.connect)

    def connect(self):
        self.db = dataset.connect('sqlite:///' + self.db_filepath)

    def insert(self, table_name, **kwargs):
        self.db[table_name].insert(**kwargs)

    def find_one(self, table_name, **kwargs):
        return self.db[table_name].find_one(**kwargs)


# def after_download(**kwargs):
#     table = db['cache']
#     table.insert(kwargs)


if __name__ == '__main__':
    # data = {
    #     'title': 'test',
    #     'artist': 'zylo117',
    #     'album': 'polyplayer',
    #     'duration': '0:03:00',
    #     'filesize': '3.25',
    #     'source': 'qq'
    # }
    # after_download(**data)
    # for cache in db['cache']:
    #     print(cache)
    # table = db['cache']
    # data = table.find_one(title='test1')
    # print()
    db = DB('polyplayer.db')
    db.connect()
