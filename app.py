from itertools import cycle

import streamlit as st

from media_server.media_service import MediaService

import streamlit_debug
streamlit_debug.set(flag=False, wait_for_client=True, host='localhost', port=8765)

# --------------------------------------------------------------------------------
# Set Streamlit page style

st.set_page_config(layout='wide', initial_sidebar_state='auto')

from style import set_page_container_style, hide_streamlit_styles
set_page_container_style(
    max_width = 1100, max_width_100_percent = True,
    padding_top = 30, padding_right = 0, padding_left = 30, padding_bottom = 0,
    color = 'white', background_color = 'black',
)
# hide_streamlit_styles()

# --------------------------------------------------------------------------------

state = st.session_state

if 'MEDIA_SERVICE' not in state:
    state.MEDIA_SERVICE = MediaService()
if 'MEDIA_SOURCES' not in state:
    state.MEDIA_SOURCES = []
if 'MEDIA_SOURCE' not in state:
    state.MEDIA_SOURCE = None
if 'MEDIA_FILTER' not in state:
    state.MEDIA_FILTER = None
if 'MEDIA_LIST' not in state:
    state.MEDIA_LIST = []

if 'MEDIA_LIST_SORT' not in state:
    state.MEDIA_LIST_SORT = True
if 'MEDIA_LIST_DATE_SORT' not in state:
    state.MEDIA_LIST_DATE_SORT = True
if 'MEDIA_LIST_SORT_ASC' not in state:
    state.MEDIA_LIST_SORT_ASC = False

if 'NUM_IMAGES' not in state:
    state.NUM_IMAGES = int(st.secrets['DEFAULT_NUM_IMAGES'])
if 'NUM_COLS' not in state:
    state.NUM_COLS = 5
if 'IMG_W' not in state:
    state.IMG_W = 512

if 'USE_PRESET' not in state:
    state.USE_PRESET = True
if 'SCREEN_WIDTH_OPTIONS' not in state:
    state.SCREEN_WIDTH_OPTIONS = st.secrets['DISPLAY_OPTIONS']['screen_widths']
if 'SCREEN_WIDTH_DEFAULT' not in state:
    state.SCREEN_WIDTH_DEFAULT = st.secrets['DISPLAY_OPTIONS']['default_screen_width']
if 'NUM_COLS_OPTIONS' not in state:
    state.NUM_COLS_OPTIONS = st.secrets['DISPLAY_OPTIONS']['num_columns']
if 'PRESETS' not in state:
    screen_width_options = st.secrets['DISPLAY_OPTIONS']['screen_widths']
    num_columns_options = st.secrets['DISPLAY_OPTIONS']['num_columns']
    all_computed_presets = {sw: {nc: str(int(int(sw)/int(nc))) for nc in num_columns_options} for sw in screen_width_options}
    default_screen_width = st.secrets['DISPLAY_OPTIONS']['default_screen_width']
    default_computed_presets = [f'{nc}, {cw}' for nc, cw in all_computed_presets[default_screen_width].items()]
    state.PRESETS = default_computed_presets
if 'PRESET_DEFAULT_INDEX' not in state:
    num_columns_options = st.secrets['DISPLAY_OPTIONS']['num_columns']
    default_num_columns = st.secrets['DISPLAY_OPTIONS']['default_num_columns']
    default_num_columns_index = num_columns_options.index(default_num_columns)
    state.PRESET_DEFAULT_INDEX = default_num_columns_index

if 'SHOW_CAPTIONS' not in state:
    state.SHOW_CAPTIONS = False
    
def test_compute_presets():
    screen_width_options = st.secrets['DISPLAY_OPTIONS']['screen_widths']
    num_columns_options = st.secrets['DISPLAY_OPTIONS']['num_columns']
    all_computed_presets = {sw: {nc: str(int(int(sw)/int(nc))) for nc in num_columns_options} for sw in screen_width_options}
    default_screen_width = st.secrets['DISPLAY_OPTIONS']['default_screen_width']
    default_computed_presets = [f'{nc}, {cw}' for nc, cw in all_computed_presets[default_screen_width].items()]
    default_num_columns = st.secrets['DISPLAY_OPTIONS']['default_num_columns']
    default_num_columns_index = num_columns_options.index(default_num_columns)
    default_preset = default_computed_presets[default_num_columns_index]

    print('screen_width_options = ', screen_width_options)
    print('num_columns_options = ', num_columns_options)
    print('all_computed_presets = ', all_computed_presets)
    print('default_screen_width = ', default_screen_width)
    print('default_computed_presets = ', default_computed_presets)
    print('default_num_columns = ', default_num_columns)
    print('default_num_columns_index = ', default_num_columns_index)
    print('default_preset = ', default_preset)

# test_compute_presets()

# --------------------------------------------------------------------------------

MS = state.MEDIA_SERVICE

# --------------------------------------------------------------------------------

@st.experimental_memo()
def get_media_sources():
    return MS.media_sources()['media_sources']

@st.experimental_memo()
def get_media_list(
    media_source='DEFAULT', 
    media_filter=None, 
    sort_flag=False, 
    sort_by_date_flag=True, 
    ascending=False
):
    filter_string = media_filter if media_filter else ''
    media_list_resp = MS.media_list(
        source=media_source, 
        filter_string=filter_string, 
        sort_flag=sort_flag, 
        sort_by_date_flag=sort_by_date_flag,
        ascending=ascending
    )
    media_list = media_list_resp['media_list']
    media_filter = media_list_resp['media_filter']
    return media_list, media_filter

def initialize_media_resources():
    state.MEDIA_SOURCES = get_media_sources()
    if state.MEDIA_SOURCES:
        state.MEDIA_SOURCE = list(state.MEDIA_SOURCES.keys())[0]
        state.MEDIA_LIST, state.MEDIA_FILTER = get_media_list(
            media_source=state.MEDIA_SOURCE,
            media_filter=None, 
            sort_flag=state.MEDIA_LIST_SORT,
            sort_by_date_flag=state.MEDIA_LIST_DATE_SORT,
            ascending=state.MEDIA_LIST_SORT_ASC
        )

if not state.MEDIA_SOURCE:
    initialize_media_resources()

# --------------------------------------------------------------------------------

@st.experimental_memo(show_spinner=False, max_entries=10000, ttl=3600)
def get_media(source, media):
    media_bytes = MS.media(source=source, media_file=media, encode=False)
    return media_bytes

@st.experimental_memo(show_spinner=False, max_entries=10000, ttl=3600)
def get_media_b64(source, media):
    media_b64 = MS.media(source=source, media_file=media, encode=True)
    return media_b64

def get_media_full_path(source, media):
    media_path = MS.media_full_path(source=source, media_file=media)['media_full_path']
    return media_path

# --------------------------------------------------------------------------------

def _recycle_media_service_cb():
    state.MEDIA_SERVICE = MediaService()
    state.MEDIA_SOURCE = None
    state.MEDIA_FILTER = None
    state.NUM_IMAGES = int(st.secrets['DEFAULT_NUM_IMAGES'])
    state.USE_PRESET = True
    state.SHOW_CAPTIONS = False
    state.MEDIA_LIST_SORT = True
    state.MEDIA_LIST_DATE_SORT = True
    state.MEDIA_LIST_SORT_ASC = False
    get_media_sources.clear()
    get_media_list.clear()

def _set_media_source_cb():
    state.MEDIA_SOURCE = state['media_source']
    state.MEDIA_FILTER = None
    state.NUM_IMAGES = state['num_images']
    state.USE_PRESET = True
    state.SHOW_CAPTIONS = False
    state.MEDIA_LIST_SORT = True
    state.MEDIA_LIST_DATE_SORT = True
    state.MEDIA_LIST_SORT_ASC = False
    state.MEDIA_LIST, state.MEDIA_FILTER = get_media_list(
        media_source=state.MEDIA_SOURCE, 
        media_filter=state.MEDIA_FILTER, 
        sort_flag=state.MEDIA_LIST_SORT,
        sort_by_date_flag=state.MEDIA_LIST_DATE_SORT,
        ascending=state.MEDIA_LIST_SORT_ASC
    )

def _set_media_controls_cb():
    state.MEDIA_SOURCE = state['media_source']
    state.MEDIA_FILTER = state['media_filter']
    state.NUM_IMAGES = state['num_images']
    state.USE_PRESET = state['use_preset']
    state.SHOW_CAPTIONS = state['show_captions']
    state.NUM_COLS = state['num_cols']
    state.IMG_W = state['img_w']
    state.MEDIA_LIST_SORT = state['media_list_sort']
    state.MEDIA_LIST_DATE_SORT = state['media_list_date_sort']
    state.MEDIA_LIST_SORT_ASC = state['media_list_sort_asc']
    state.MEDIA_LIST, state.MEDIA_FILTER = get_media_list(
        media_source=state.MEDIA_SOURCE, 
        media_filter=state.MEDIA_FILTER, 
        sort_flag=state.MEDIA_LIST_SORT,
        sort_by_date_flag=state.MEDIA_LIST_DATE_SORT,
        ascending=state.MEDIA_LIST_SORT_ASC
    )

# Prevents double clicking to make widget state stick
def _set_use_preset_cb():
    state.USE_PRESET = state['use_preset']

def _set_captions_cb():
    state.SHOW_CAPTIONS = state['show_captions']

def _set_num_cols_cb():
    state.NUM_COLS = state['num_cols']

def _set_img_w_cb():
    state.IMG_W = state['img_w']

def _set_screen_width_default_index_cb():
    state.SCREEN_WIDTH_DEFAULT = state['screen_width_choice']

    screen_width_options = st.secrets['DISPLAY_OPTIONS']['screen_widths']
    num_columns_options = st.secrets['DISPLAY_OPTIONS']['num_columns']
    all_computed_presets = {sw: {nc: str(int(int(sw)/int(nc))) for nc in num_columns_options} for sw in screen_width_options}
    default_screen_width = state.SCREEN_WIDTH_DEFAULT
    default_computed_presets = [f'{nc}, {cw}' for nc, cw in all_computed_presets[default_screen_width].items()]
    state.PRESETS = default_computed_presets

# Prevents double selecting to make widget state stick
def _set_preset_default_index_cb():
    state.PRESET_DEFAULT_INDEX = state.PRESETS.index(state['preset_choice'])
    # print(state.PRESET_DEFAULT_INDEX)

# --------------------------------------------------------------------------------

def main():
    c1, c2, c3 = st.sidebar.columns([3,3,2])
    c1.image('./images/app_logo.png')
    c2.write('&nbsp;')
    c2.image('./images/a12i_logo_grey.png')

    # NOTE: number_input widgets are sometimes prone to misinterpreting state values as float, so I force them to be int

    with st.sidebar:
        with st.form(key='media_selection_form', clear_on_submit=False):
            state.MEDIA_SOURCE = st.selectbox(
                '✨ Select media source', 
                options=list(state.MEDIA_SOURCES.keys()),
                key='media_source'
            )
            state.NUM_IMAGES = st.number_input(
                'Max images', 0, int(st.secrets['MAX_NUM_IMAGES']), int(state.NUM_IMAGES), 
                100, key='num_images', help='A value of zero will not impose a limit on the number of images pulled')
            if st.form_submit_button('Apply', on_click=_set_media_source_cb):
                st.experimental_rerun()

        with st.expander('📅 Media settings', expanded=False):
            with st.form(key='media_controls_form', clear_on_submit=False):
                state.MEDIA_FILTER = st.text_input('🔎 Filter keyword', state.MEDIA_FILTER, key='media_filter', help='Keyword will be used to match filenames')
                c1, c2 = st.columns(2)
                state.MEDIA_LIST_SORT = c1.checkbox('Sort', state.MEDIA_LIST_SORT, key='media_list_sort')
                state.MEDIA_LIST_SORT_ASC = c2.checkbox('Ascending', state.MEDIA_LIST_SORT_ASC, disabled=(not state.MEDIA_LIST_SORT), key='media_list_sort_asc')
                state.MEDIA_LIST_DATE_SORT = c1.checkbox('By date', state.MEDIA_LIST_DATE_SORT, disabled=(not state.MEDIA_LIST_SORT), key='media_list_date_sort')
                st.caption('Sort by date and ascending only work if sort is enabled')
                if st.form_submit_button('Apply', on_click=_set_media_controls_cb):
                    st.experimental_rerun()

        with st.expander('👀 Layout settings', expanded=True):
            state.SHOW_CAPTIONS = st.checkbox('Show captions', state.SHOW_CAPTIONS, on_change=_set_captions_cb, key='show_captions')
            state.USE_PRESET = st.checkbox('Use presets', state.USE_PRESET, on_change=_set_use_preset_cb, key='use_preset')
            if state.USE_PRESET:
                st.selectbox(
                    'What is your screen width?', options=state.SCREEN_WIDTH_OPTIONS,
                    index=state.SCREEN_WIDTH_OPTIONS.index(state.SCREEN_WIDTH_DEFAULT),
                    on_change=_set_screen_width_default_index_cb,
                    help='Pixel width of your device, including compensation for scale factor',
                    key='screen_width_choice'
                )
                preset_choice = st.selectbox(
                    'Choose a preset', options=state.PRESETS,
                    index=state.PRESET_DEFAULT_INDEX,
                    on_change=_set_preset_default_index_cb,
                    help='Number of columns and image width',
                    key='preset_choice'
                )
                state.NUM_COLS = int(preset_choice.split(',')[0].strip())
                state.IMG_W = int(preset_choice.split(',')[1].strip())
                st.markdown('---')
                # Must ensure these keyed widgets are created in both branches as other callbacks use their so they need to exist 
                state.NUM_COLS = st.number_input('Number columns', 1, 80, int(state.NUM_COLS), 1, on_change=_set_num_cols_cb, key='num_cols',
                    disabled=True, help='To make manual adjustments, uncheck presets')
                state.IMG_W = st.number_input('Image width', 32, 3200, int(state.IMG_W), 32, on_change=_set_img_w_cb, key='img_w',
                    disabled=True, help='To make manual adjustments, uncheck presets')
            else:
                state.NUM_COLS = st.number_input('Number columns', 1, 80, int(state.NUM_COLS), 1, on_change=_set_num_cols_cb, key='num_cols')
                state.IMG_W = st.number_input('Image width', 32, 3200, int(state.IMG_W), 32, on_change=_set_img_w_cb, key='img_w')

        with st.expander('🌀 Recycle media service'):
            st.caption('Use this to reload external media config (toml) file changes')
            st.button(
                'Recycle',
                on_click=_recycle_media_service_cb,
            )

    media_list, _media_filter = get_media_list(
        media_source=state.MEDIA_SOURCE,
        media_filter=state.MEDIA_FILTER,
        sort_flag=state.MEDIA_LIST_SORT,
        sort_by_date_flag=state.MEDIA_LIST_DATE_SORT,
        ascending=state.MEDIA_LIST_SORT_ASC
    )
    working_media_list = media_list[:int(state.NUM_IMAGES)] if int(state.NUM_IMAGES) > 0 else media_list
    images = {media: media for media in working_media_list}

    cols = cycle(st.columns(int(state.NUM_COLS)))
    for img, caption in images.items():
        if not 'http' in img:
            image_bytes = get_media(source=state.MEDIA_SOURCE, media=img)
            image = image_bytes
        else:
            image = img

        try:
            if state.SHOW_CAPTIONS:
                next(cols).image(image, width=int(state.IMG_W), output_format='auto', caption=caption)
            else:
                next(cols).image(image, width=int(state.IMG_W), output_format='auto')
        except Exception as ex:
            print(f'Skipping {caption}\n', str(ex))
            pass

# -----------------------------------------------------------------------------

def about():
    st.sidebar.markdown('---')
    st.sidebar.info('''
        (c) 2022. CloudOpti Ltd. All rights reserved.
        
        [GitHub repo](https://github.com/asehmi/st-media-service)
    ''')

# -----------------------------------------------------------------------------

if __name__ == '__main__':
    main()
    about()
