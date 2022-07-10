import os
from typing import Union
from mimetypes import guess_type
import toml
import glob
import base64

class MediaService():

    def __init__(self):
        """
        Initializes instance to serve media (image) files.
        """
        print('Initializing MediaService...')
        
        dir = os.path.abspath(os.path.dirname(__file__))
        if os.path.isfile(os.path.join(dir, 'media_service.toml')):
            service_settings = toml.load(os.path.join(dir, 'media_service.toml'))
        else:
            service_settings = toml.load(os.path.join(dir, 'media_service.toml'))

        self.MEDIA_SOURCES, self.MEDIA_TYPES = service_settings['MEDIA_SOURCES'], service_settings['MEDIA_TYPES']

    def _image_bytes(self, image):
        with open(image, 'rb') as image_f:
            image_bytes = image_f.read()
        return image_bytes

    def _image_base64(self, image):
        image_bytes = self._image_bytes(image)
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        return image_b64

    def _rename_file_with_prefix(self, source: str, media_file: str, prefix: str):
        media_source = self.MEDIA_SOURCES[source]
        media_folder = media_source['media_folder']

        src = os.path.join(media_folder, media_file)
        dest = os.path.join(media_folder, f'{prefix}_{media_file}')

        if not os.path.isfile(src):
            raise FileNotFoundError(src)
        
        try:
            os.rename(src, dest)
            print("Renamed:", src, 'to', dest)
        except Exception as e:
            raise e
        
        return True

    def media_full_path(self, source: str, media_file: str):
        media_source = self.MEDIA_SOURCES[source]
        media_folder = media_source['media_folder']

        filename = os.path.join(media_folder, media_file)

        if not os.path.isfile(filename):
            raise FileNotFoundError(filename)

        return {'media_full_path': filename}

    def content_type(self, source: str, media_file: str):
        media_source = self.MEDIA_SOURCES[source]
        media_folder = media_source['media_folder']

        filename = os.path.join(media_folder, media_file)

        content_type, _ = guess_type(filename)

        return content_type

    def media(self, source: str, media_file: str, encode: bool = False):
        media_source = self.MEDIA_SOURCES[source]
        media_folder = media_source['media_folder']

        filename = os.path.join(media_folder, media_file)

        if not os.path.isfile(filename):
            raise FileNotFoundError(filename)
        
        return self._image_base64(filename) if encode else self._image_bytes(filename)

    def delete_media(self, source: str, media_file: str):
        return self._rename_file_with_prefix(source, media_file, 'DEL')

    def favorite_media(self, source: str, media_file: str):
        return self._rename_file_with_prefix(source, media_file, 'FAV')

    def media_sources(self):
        return {'media_sources': self.MEDIA_SOURCES}

    def media_list(
        self, source: str, 
        filter_string: Union[str, None] = None,
        sort_flag: bool = False, 
        sort_by_date_flag: bool = True,
        ascending: bool = False
    ):
        source = source.replace('(', '').replace(')', '').replace('"', '').strip()

        # https://thispointer.com/python-get-list-of-files-in-directory-sorted-by-date-and-time/
        def _get_sorted(media_files):
            
            # sorted() sorts alphabetical + ascending by default
            # With a date key it does an ascending date sort
            # For descending (not ascending) we just reverse the list

            def _media_file_date(x):
                # Getting the last modified time of the file.
                return os.path.getmtime(x)

            if sort_flag and sort_by_date_flag:
                media_files = sorted(media_files, key=_media_file_date, reverse=(not ascending))
            elif sort_flag:
                media_files = sorted(media_files, reverse=(not ascending))

            return media_files

        def _get_media_list():
            media_source = self.MEDIA_SOURCES[source]
            media_files = []
            media_filter = filter_string if filter_string else media_source['media_filter']
            if media_source.get('media_folder', None):
                media_folder = media_source['media_folder']
                unfiltered_media_files = glob.glob(f'{media_folder}/*.*')
                for media_type in self.MEDIA_TYPES:
                    file_extension = media_type.split('/')[-1]
                    media_type_files = filter(lambda x: file_extension in x, unfiltered_media_files)
                    media_files.extend(media_type_files)
                media_files = _get_sorted(media_files)
                media_files = [url.replace(f'{media_folder}\\','').replace(f'{media_folder}/','') for url in media_files]
            elif media_source.get('media_links', None):
                media_files = media_source['media_links']

            if bool(media_filter):
                media_files = [media_file for media_file in media_files if media_filter in media_file]

            return media_files, media_filter

        media_files, media_filter = _get_media_list()

        return {'media_list': media_files, 'media_filter': media_filter}
