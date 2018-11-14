#!/usr/bin/env python
"""
galaxy-fuse.py will mount Galaxy datasets for direct read access using FUSE.

galaxy-fuse was written by Dr David Powell and began life at
https://github.com/drpowell/galaxy-fuse .

- Modified December 2016 by Madison Flannery
- Overhauled November 2018 by Helena Rasche
"""

from errno import ENOENT
from stat import S_IFDIR, S_IFREG
import re
import time
import os
import argparse
import requests
import cachetools
import logging

from fuse import FUSE, FuseOSError, Operations, LoggingMixIn

from bioblend import galaxy
logging.basicConfig(filename="bioblend.log", level=logging.DEBUG)

# number of seconds to cache history/dataset lookups
CACHE_TIME = 60
DS_CACHE_ENTS = 2048
BYTES_CACHE_ENTS = 64
DIR_CACHE_ENTS = 64

DIRMODE = 0o555
FILEMODE = 0o444
USE_FILENAME = True
NOW = time.time()
SEPARATOR = '__'


def escape(path):
    # Remove any bad chars
    return re.sub(r'[^A-Za-z0-9_. -]', '', path)


# Split a path into hash of components
def path_type(path):
    parts = path.split('/')
    parts = list(map(escape, [x for x in path.split('/') if len(x) > 0]))

    if path == '/':
        return 'root', {}

    if path == '/histories':
        # histories/
        return 'histories', {}

    if parts[0] != 'histories':
        return 'unknown', {}

    if len(parts) == 2:
        # histories/<history_name>
        return 'datasets', {'history': parse_name_with_id(parts[1])[1]}

    if len(parts)== 3:
        # Path: histories/<history_name>/<data_name>
        #    OR histories/<history_name>/<collection_name>
        if parts[2][-3:] == '_dc':
            return 'hdc', {
                'history': parse_name_with_id(parts[1])[1],
                'collection': parse_name_with_id(parts[2])[1],
            }
        else:
            return 'hda', {
                'history': parse_name_with_id(parts[1])[1],
                'dataset': parse_name_with_id(parts[2])[1],
            }

    if len(parts) == 4:
        # Path: histories/<history_name>/<coll_name>/<dataset_name>
        if parts[2][-3:] == '_dc':
            return 'hdcc', {
                'history': parse_name_with_id(parts[1])[1],
                'collection': parse_name_with_id(parts[2])[1],
                'collection2': parse_name_with_id(parts[3])[1],
            }
        else:
            return 'hdcd', {
                'history': parse_name_with_id(parts[1])[1],
                'collection': parse_name_with_id(parts[2])[1],
                'dataset': parse_name_with_id(parts[3])[1],
            }

    if len(parts) == 5:
        # Path: histories/<history_name>/<hdc_name>/<hdc_name>/<dataset_name>
        return 'hdcd', {
            'history': parse_name_with_id(parts[1])[1],
            'collection': parse_name_with_id(parts[2])[1],
            'dataset': parse_name_with_id(parts[3])[1],
        }

    return ('unknown', {})


def parse_name_with_id(fname):
    if USE_FILENAME:
        if fname[-3:] == '_dc':
            fname = fname[:-3]

        idx = fname.rindex(SEPARATOR)
        return fname[:idx], fname[idx + len(SEPARATOR):]
    else:
        if fname.endswith('_dc'):
            return ('', fname[3:])
        return ('', fname)


def fname(obj, attr='id'):
    if USE_FILENAME:
        if 'name' not in obj:
            obj['name'] = obj['element_identifier']
        n = '{name} {sep}{id}'.format(sep=SEPARATOR, **obj)
    else:
        n = obj[attr]

    if obj.get('history_content_type', None) == 'dataset_collection' or obj.get('element_type', None) == 'dataset_collection':
        n += '_dc'

    return n

# Smaller since needs to hold real bytes of files
bytes_cache = cachetools.LRUCache(BYTES_CACHE_ENTS)
datasets_cache = cachetools.TTLCache(DS_CACHE_ENTS, CACHE_TIME)
filtered_datasets_cache = cachetools.TTLCache(DS_CACHE_ENTS, CACHE_TIME)
all_datasets_cache = cachetools.TTLCache(DS_CACHE_ENTS, CACHE_TIME)
datasets_for_history_cache = cachetools.TTLCache(DS_CACHE_ENTS, CACHE_TIME)
collections_cache = cachetools.TTLCache(DS_CACHE_ENTS, CACHE_TIME)
histories_cache = cachetools.TTLCache(DS_CACHE_ENTS, CACHE_TIME)
directory_cache = cachetools.TTLCache(DIR_CACHE_ENTS, CACHE_TIME)


class Context(LoggingMixIn, Operations):
    'Prototype FUSE to galaxy histories'

    def __init__(self, url, api_key):
        self.gi = galaxy.GalaxyInstance(url=url, key=api_key)

    def getattr(self, path, fh=None):
        try:
            return self._getattr(path, fh=fh)
        except Exception as e:
            print(e)

    @cachetools.cached(directory_cache)
    def _getattr(self, path, fh=None):
        (object_type, kw) = path_type(path)
        print('getattr', object_type, path, kw)

        if object_type in ('root', 'histories', 'datasets'):
            st = {
                'st_mode': S_IFDIR | DIRMODE,
                'st_nlink': 2,
                'st_ctime': NOW,
                'st_mtime': NOW,
                'st_atime': NOW,
            }

        elif object_type == 'hda':
            # Dataset or collection
            d = self._dataset(kw['history'], kw['dataset'])
            d_size = d.get('file_size', 0)
            if 'update_time' in d:
                t = time.mktime(time.strptime(d['update_time'],'%Y-%m-%dT%H:%M:%S.%f'))
            else:
                t = NOW

            st = {
                'st_mode': (S_IFREG | 0o444),
                'st_nlink': 1,
                'st_size': d_size,
                'st_ctime': t,
                'st_mtime': t,
                'st_atime': t,
            }
        elif object_type == 'hdc' or object_type == 'hdcc':
            d = self._dataset_collections(kw['history'], kw['collection'])

            d_size = d.get('file_size', 0)
            if 'update_time' in d:
                t = time.mktime(time.strptime(d['update_time'],'%Y-%m-%dT%H:%M:%S.%f'))
            else:
                t = NOW

            # An HDC
            st = {
                'st_mode': S_IFDIR | 0o555,
                'st_nlink': 2,
                'st_ctime': t,
                'st_mtime': t,
                'st_atime': t,
            }
        elif object_type == 'hdcd':
            # A file within a collection, will be a symlink to a galaxy dataset.
            d = self._dataset(kw['history'], kw['dataset'], display=False)
            d_size = d['file_size']
            t = time.mktime(time.strptime(d['update_time'],'%Y-%m-%dT%H:%M:%S.%f'))

            st = {
                'st_mode': (S_IFREG | 0o444),
                'st_nlink': 1,
                'st_size': d_size,
                'st_ctime': t,
                'st_mtime': t,
                'st_atime': t,
            }
        else:
            raise FuseOSError(ENOENT)
        return st

    @cachetools.cached(bytes_cache)
    def read(self, path, size, offset, fh):
        (object_type, kw) = path_type(path)
        print('read', path, size, offset, object_type, kw)
        url = self.gi.url + '/histories/{history}/contents/{dataset}/display?key={key}'.format(key=self.gi.key, **kw)

        headers = {'Range': 'bytes=%s-%s' % (offset, offset + size - 1)}
        print("curl %s -H 'Range: %s'" % (url, headers['Range']))
        r = requests.get(url, headers=headers)
        print(len(r.content))
        return r.content

    # Lookup all histories in galaxy; cache
    @cachetools.cached(histories_cache)
    def _histories(self):
        return self.gi.histories.get_histories()

    # Find a specific history by name
    @cachetools.cached(histories_cache)
    def _history(self, history):
        return self.gi.histories.show_history(history)

    # Lookup visible datasets in the specified history; cache
    # This will not return deleted or hidden datasets.
    @cachetools.cached(filtered_datasets_cache)
    def _filtered_datasets(self, history_id):
        return self.gi.histories.show_history(history_id, contents=True, details='all', deleted=False, visible=True)

    # Lookup all datasets in the specified history; cache
    # This will return hidden datasets. Will not return deleted datasets.
    @cachetools.cached(all_datasets_cache)
    def _all_datasets(self, history_id):
        return self.gi.histories.show_history(history_id, contents=True, details='all', deleted=False)

    @cachetools.cached(datasets_for_history_cache)
    def _fetch_datasets_for_history(self, history_id, deleted=False, visible=True):
        return self.gi.histories.show_history(history_id, contents=True,
                                              details='all', deleted=deleted,
                                              visible=visible)

    @cachetools.cached(collections_cache)
    def _dataset_collections(self, history_id, dataset_collection_id):
        return self.gi.histories.show_dataset_collection(history_id, dataset_collection_id)

    @cachetools.cached(datasets_cache)
    def _dataset(self, history_id, dataset_id, display=True):
        history = self._history(history_id)

        if display:
            ds = self._filtered_datasets(history['id'])
        else:
            ds = self._all_datasets(history['id'])

        d = list(filter(lambda x: x['id'] == dataset_id, ds))

        if len(d) == 0:
            raise FuseOSError(ENOENT)

        if len(d) > 1:
            print("Too many datasets with that name and ID")

        return d[0]

    def readdir(self, path, fh):
        try:
            return self._readdir(path, fh)
        except Exception as e:
            print(e)

    # read directory contents
    def _readdir(self, path, fh):
        (object_type, kw) = path_type(path)
        found_objects = ['.', '..']
        print('readdir', path, kw, object_type)

        if object_type == 'root':
            found_objects.append('histories')

        elif object_type == 'histories':
            for history in self._histories():
                found_objects.append(fname(history))

        elif object_type == 'datasets':
            history = self._history(kw['history'])
            datasets = self._filtered_datasets(history['id'])

            # Count duplicates
            for dataset in datasets:
                found_objects.append(fname(dataset))

        elif object_type == 'hdc':
            # This is a dataset collection
            collection = self._dataset_collections(kw['history'], kw['collection'])
            if collection['collection_type'] not in ('paired', 'list', 'list:paired'):
                print("Unsupported collection type")
                return found_objects

            if collection['collection_type'] == 'list:paired':
                for dc in collection['elements']:
                    found_objects.append(fname(dc))
            else:
                for dataset in collection['elements']:
                    found_objects.append(fname(dataset['object']))
        elif object_type == 'hdcc':
            # This is a dataset collection
            collection = self._dataset_collections(kw['history'], kw['collection'])
            if collection['collection_type'] not in ('paired', 'list', 'list:paired'):
                print("Unsupported collection type")
                return found_objects

            collection = [x for x in collection['elements'] if x['id'] == kw['collection2']][0]

            for dataset in collection['object']['elements']:
                found_objects.append(fname(dataset['object']))


        return found_objects

    # Disable unused operations:
    chmod = None
    chown = None
    create = None

    access = None
    flush = None
    getxattr = None
    listxattr = None
    open = None
    opendir = None
    release = None
    releasedir = None
    statfs = None


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Mount Galaxy Datasets for direct read access using FUSE.")
    parser.add_argument("url")
    parser.add_argument("apikey")
    parser.add_argument("-m", "--mountpoint", help="Directory under which to mount the Galaxy Datasets.")
    parser.add_argument("--human", action='store_true', help='Human readable names')
    args = parser.parse_args()

    USE_FILENAME = args.human

    # Create the directory if it does not exist
    if not os.path.exists(args.mountpoint):
        os.makedirs(args.mountpoint)

    fuse = FUSE(Context(args.url, args.apikey),
                args.mountpoint,
                foreground=True,
                ro=True, debug=False)
