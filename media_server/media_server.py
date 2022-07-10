import os
import sys
from typing import Union
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, RedirectResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import toml

from media_service import MediaService

dir = os.path.abspath(os.path.dirname(__file__))

# Access secret config vars
server_settings = toml.load(os.path.join(dir, 'media_server.toml'))
HOST = server_settings['HOST']
PORT = server_settings['PORT']

CORS_ALLOW_ORIGINS = ['http://{HOST}, https://{HOST}, http://localhost, http://localhost:4010, http://localhost:8765']

class MediaServerAPI_Wrapper(FastAPI):

    def __init__(self):
        """
        Initializes a custom FastAPI instance to serve media (image) files.
        """
        print('Initializing MediaServerAPI_Wrapper...')
        
        super().__init__()

        MS = MediaService()

        origins = CORS_ALLOW_ORIGINS

        self.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        def custom_openapi():
            from fastapi.openapi.utils import get_openapi

            print('Running custom_openapi...')
            
            if self.openapi_schema:
                return self.openapi_schema

            openapi_schema = get_openapi(
                title="MediaServerAPI_Wrapper",
                version='1.0',
                description="<em><h2>Simple Media Server API</h2><em>",
                routes=self.routes,
            )
            openapi_schema["info"]["x-logo"] = {
                "url": "https://avatars.githubusercontent.com/u/138668"
            }
            self.openapi_schema = openapi_schema
            return self.openapi_schema

        self.openapi = custom_openapi
        
        @self.get("/")
        async def home():
            return RedirectResponse(url='/docs', status_code=307)

        @self.get("/media_full_path/{source}/{media_file}")
        async def media_full_path(source: str, media_file: str):
            try:
                return JSONResponse(
                    MS.media_full_path(source=source, media_file=media_file),
                    status_code=200
                )
            except Exception as e:
                return Response(str(e), status_code=404)

        @self.get("/media/{source}/{media_file}")
        async def media(source: str, media_file: str, encode: bool = False):
            try:
                content = MS.media(source=source, media_file=media_file, encode=encode)
                content_type = MS.content_type(source=source, media_file=media_file)
                return Response(content, media_type=content_type, status_code=200)
            except Exception as e:
                return Response(str(e), status_code=404)

        @self.get("/delete_media/{source}/{media_file}")
        def delete_media(source: str, media_file: str):
            try:
                return Response(
                    MS._rename_file_with_prefix(source, media_file, 'DEL'),
                    status_code=200
                )
            except Exception as e:
                return Response(str(e), status_code=404)

        @self.get("/favorite_media/{source}/{media_file}")
        def favorite_media(source: str, media_file: str):
            try:
                return Response(
                    MS._rename_file_with_prefix(source, media_file, 'FAV'),
                    status_code=200
                )
            except Exception as e:
                return Response(str(e), status_code=404)

        @self.get("/media_sources")
        async def media_sources():
            return JSONResponse(MS.media_sources(), status_code=200)

        @self.get("/media_list/{source}")
        async def media_list(
            source: str, 
            filter_string: Union[str, None] = None, 
            sort_flag: bool = False,
            sort_by_date_flag: bool = True,
            ascending: bool = False
        ):
            try:
                return JSONResponse(
                    MS.media_list(
                        source=source, 
                        filter_string=filter_string, 
                        sort_flag=sort_flag, 
                        sort_by_date_flag=sort_by_date_flag, 
                        ascending=ascending
                    ),
                    status_code=200
                )
            except Exception as e:
                return Response(str(e), status_code=500)

        # Add shutdown event (would only be of any use in a multi-process, not multi-thread situation)
        @self.get("/shutdown")
        async def shutdown():
            import time
            import psutil
            import threading

            def suicide():
                time.sleep(1)
                myself = psutil.Process(os.getpid())
                myself.kill()

            try:
                threading.Thread(target=suicide, daemon=True).start()
                msg = '>>> Successfully killed API <<<'
                print(msg)
                return Response(msg, status_code=200)
            except Exception as e:
                return Response(str(e), status_code=500)

"""
Simple bootstrapper intended to be used used to start the API as a daemon process
"""
app = MediaServerAPI_Wrapper()

# Wrapping uvicorn import in try/except as have issues in Streamlit cloud
# The test client application runs uvicorn directly with media_server:app
def start(host=HOST, port=PORT):
    try:
        import uvicorn
        from pathlib import Path
        uvicorn.run(f'{Path(__file__).stem}:app', host=host, port=port) # reload=True, workers=2
    except Exception as msg:
        print('EXCEPTION ecountered running uvicorn!')
        print(str(msg))
        print('Try running the app from command line:\n')
        print(f'   $ uvicorn media_server:app --host {host} --port {port}\n')

if __name__ == "__main__":
    if len(sys.argv) > 2:
        start(host=sys.argv[1], port=int(sys.argv[2]))
    else:
        start()
