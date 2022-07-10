import os
import sys
import requests
import json
import time
import base64
from abc import ABCMeta, abstractmethod

import streamlit as st

from media_server.media_service import MediaService

class MediaClient(metaclass=ABCMeta):
    def __init__(self):
        self.MEDIA_BACKEND_STARTED = False
        self.MEDIA_SOURCES = []
        self.MEDIA_SOURCE = None
        self.MEDIA_FILTER = None
        self.MEDIA_LIST = []
        self.MEDIA_LIST_SORT = True
        self.MEDIA_LIST_DATE_SORT = True
        self.MEDIA_LIST_SORT_ASC = False
        self.NUM_IMAGES = int(st.secrets['DEFAULT_NUM_IMAGES'])

    @abstractmethod
    def initialize_media_backend(self):
        pass
    @abstractmethod
    def get_media_sources(self):
        pass
    @abstractmethod
    def get_media_list(self, media_source, media_filter, sort_flag, sort_by_date_flag, ascending):
        pass
    @abstractmethod
    def initialize_media_resources(self):
        pass
    @abstractmethod
    def get_media(self, source, media):
        pass
    @abstractmethod
    def get_media_b64(self, source, media):
        pass
    @abstractmethod
    def get_media_full_path(self, source, media):
        pass
    @abstractmethod
    def shutdown():
        pass

class MediaServiceClient(MediaClient):
    def __init__(self):
        super().__init__()

    def initialize_media_backend(self):
        self.MEDIA_SERVICE = MediaService()
        self.MEDIA_BACKEND_STARTED = True

    @st.experimental_memo(show_spinner=False)
    def get_media_sources(_self):
        return _self.MEDIA_SERVICE.media_sources()['media_sources']

    @st.experimental_memo(show_spinner=False)
    def get_media_list(
        _self,
        media_source='DEFAULT', 
        media_filter=None, 
        sort_flag=False, 
        sort_by_date_flag=True, 
        ascending=False
    ):
        filter_string = media_filter if media_filter else ''
        media_list_resp = _self.MEDIA_SERVICE.media_list(
            source=media_source, 
            filter_string=filter_string, 
            sort_flag=sort_flag, 
            sort_by_date_flag=sort_by_date_flag,
            ascending=ascending
        )
        media_list = media_list_resp['media_list']
        media_filter = media_list_resp['media_filter']
        return media_list, media_filter

    def initialize_media_resources(self):
        self.MEDIA_SOURCES = self.get_media_sources()
        if self.MEDIA_SOURCES:
            self.MEDIA_SOURCE = list(self.MEDIA_SOURCES.keys())[0]
            self.MEDIA_LIST, self.MEDIA_FILTER = self.get_media_list(
                media_source=self.MEDIA_SOURCE,
                media_filter=None, 
                sort_flag=self.MEDIA_LIST_SORT,
                sort_by_date_flag=self.MEDIA_LIST_DATE_SORT,
                ascending=self.MEDIA_LIST_SORT_ASC
            )

    @st.experimental_memo(show_spinner=False, max_entries=10000, ttl=3600)
    def get_media(_self, source, media):
        media_bytes = _self.MEDIA_SERVICE.media(source=source, media_file=media, encode=False)
        return media_bytes

    @st.experimental_memo(show_spinner=False, max_entries=10000, ttl=3600)
    def get_media_b64(_self, source, media):
        media_b64 = _self.MEDIA_SERVICE.media(source=source, media_file=media, encode=True)
        return media_b64

    def get_media_full_path(self, source, media):
        media_path = self.MEDIA_SERVICE.media_full_path(source=source, media_file=media)['media_full_path']
        return media_path

    def shutdown(self):
        self.MEDIA_SERVICE = MediaService()

class RemoteMediaServerClient(MediaClient):
    def __init__(self):
        super().__init__()
        self.MEDIA_SERVER_HOST = st.secrets['MEDIA_SERVER']['HOST']
        self.MEDIA_SERVER_PORT = st.secrets['MEDIA_SERVER']['PORT']
        self.HTTP_PROTOCOL = st.secrets['MEDIA_SERVER']['HTTP_PROTOCOL']
        self.BASE_URL = f'{self.HTTP_PROTOCOL}://{self.MEDIA_SERVER_HOST}:{self.MEDIA_SERVER_PORT}'

    def initialize_media_backend(self):
         # as this is a remote server scenario, assume it has started
        self.MEDIA_BACKEND_STARTED = True

    @st.experimental_memo(show_spinner=False)
    def get_media_sources(_self):
        return json.loads(requests.get(f'{_self.BASE_URL}/media_sources').text)['media_sources']

    @st.experimental_memo(show_spinner=False)
    def get_media_list(
        _self,
        media_source='DEFAULT', 
        media_filter=None, 
        sort_flag=False, 
        sort_by_date_flag=True, 
        ascending=False
    ):
        filter_param  = f'filter_string={media_filter}' if media_filter else ''
        sort_param  = f'sort_flag={sort_flag}'
        sort_by_date_param  = f'sort_by_date_flag={sort_by_date_flag}'
        ascending_param  = f'ascending={ascending}'
        params = f'{sort_param}&{sort_by_date_param}&{ascending_param}'
        params = f'{filter_param}&{params}' if filter_param else params
        media_list_resp = json.loads(requests.get(f'{_self.BASE_URL}/media_list/{media_source}?{params}').text)
        media_list = media_list_resp['media_list']
        media_filter = media_list_resp['media_filter']
        return media_list, media_filter

    def initialize_media_resources(self):
        self.MEDIA_SOURCES = self.get_media_sources()
        if self.MEDIA_SOURCES:
            self.MEDIA_SOURCE = list(self.MEDIA_SOURCES.keys())[0]
            self.MEDIA_LIST, self.MEDIA_FILTER = self.get_media_list(
                media_source=self.MEDIA_SOURCE,
                media_filter=None, 
                sort_flag=self.MEDIA_LIST_SORT,
                sort_by_date_flag=self.MEDIA_LIST_DATE_SORT,
                ascending=self.MEDIA_LIST_SORT_ASC
            )

    @st.experimental_memo(show_spinner=False, max_entries=10000, ttl=3600)
    def get_media(_self, source, media):
        media_bytes = requests.get(f'{_self.BASE_URL}/media/{source}/{media}').content
        return media_bytes
    
    @st.experimental_memo(show_spinner=False, max_entries=10000, ttl=3600)
    def get_media_b64(_self, source, media):
        media_bytes = requests.get(f'{_self.BASE_URL}/media/{source}/{media}').content
        media_b64 = base64.b64encode(media_bytes).decode('utf-8')
        return media_b64

    def get_media_full_path(self, source, media):
        media_full_path = json.loads(
            requests.get(f'{self.BASE_URL}/media_full_path/{source}/{media}').text
        )['media_full_path']
        return media_full_path

    def shutdown(self):
        print('NOT SAFE:')
        print('- Shut down the remote server manually with:', f'{self.BASE_URL}/shutdown')
        print('- Then restart the server and refreh the browser window.')

# This class delgates most of its work to its parent RemoteMediaServerClient,
# except for the backend initializer
class EmbeddedMediaServerClient(RemoteMediaServerClient):
    def __init__(self):
        super().__init__()

    def initialize_media_backend(self):

        if self.MEDIA_BACKEND_STARTED:
            return

        import subprocess
        import threading

        def _run(job):
            print (f'\nRunning job: {job}\n')
            proc = subprocess.Popen(job)
            proc.wait()
            return proc

        # Can use either of these job specs below

        # [1] sys.executable ensures we use the same Python environment that Streamlit is running under
        job = [f'{sys.executable}', os.path.join('media_server', 'media_server.py'), self.MEDIA_SERVER_HOST, str(self.MEDIA_SERVER_PORT)]

        # [2] For Streamlit cloud I'm trying to run uvicorn directly to avoid importing uvicorn
        # in media_server.py which seemed to fail!
        # job = ['uvicorn', 'media_server:app', '--host', self.MEDIA_SERVER_HOST, '--port', str(self.MEDIA_SERVER_PORT)]

        # server thread will remain active as long as streamlit thread is running, or is manually shutdown
        thread = threading.Thread(name='Media Server', target=_run, args=(job,), daemon=False)
        thread.start()

        time.sleep(5)
        self.MEDIA_BACKEND_STARTED = True

    @st.experimental_memo(show_spinner=False)
    def get_media_sources(_self):
        return super().get_media_sources()

    @st.experimental_memo(show_spinner=False)
    def get_media_list(
        _self,
        media_source='DEFAULT', 
        media_filter=None, 
        sort_flag=False, 
        sort_by_date_flag=True, 
        ascending=False
    ):
        return super().get_media_list(
            media_source=media_source, 
            media_filter=media_filter, 
            sort_flag=sort_flag, 
            sort_by_date_flag=sort_by_date_flag, 
            ascending=ascending
        )

    def initialize_media_resources(self):
        return super().initialize_media_resources()

    @st.experimental_memo(show_spinner=False, max_entries=10000, ttl=3600)
    def get_media(_self, source, media):
        return super().get_media(source, media)
    
    @st.experimental_memo(show_spinner=False, max_entries=10000, ttl=3600)
    def get_media_b64(_self, source, media):
        return super().get_media_b64(source, media)

    def get_media_full_path(self, source, media):
        return super().get_media_full_path(source, media)

    def shutdown(self):
        requests.get(f'{self.BASE_URL}/shutdown')
        time.sleep(1)

class MediaClientFactory:
    @staticmethod
    def GetMediaClient() -> MediaClient:
        if st.secrets['MEDIA_SERVER']['MODE'] == 'remote_server':
            return RemoteMediaServerClient()
        elif st.secrets['MEDIA_SERVER']['MODE'] == 'embedded_server':
            return EmbeddedMediaServerClient()
        elif st.secrets['MEDIA_SERVER']['MODE'] == 'service_object':
            return MediaServiceClient()
