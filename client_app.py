from itertools import cycle

import streamlit as st

from media_client import MediaClientFactory

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

if 'MEDIA_CLIENT' not in state:
    state.MEDIA_CLIENT = MediaClientFactory.GetMediaClient()

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

if 'PACKED_LAYOUT' not in state:
    state.PACKED_LAYOUT = False
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

# Initialization will occur if ever MEDIA_BACKEND_STARTED flag is reset and Streamlit reruns

mc = state.MEDIA_CLIENT

if (not mc.MEDIA_BACKEND_STARTED):
    mc.initialize_media_backend()
    st.experimental_rerun()
else:
    mc.MEDIA_BACKEND_STARTED = True

if mc.MEDIA_BACKEND_STARTED and (not mc.MEDIA_SOURCE):
    mc.initialize_media_resources()

# --------------------------------------------------------------------------------

def _recycle_media_service_cb():
    mc.get_media_sources.clear()
    mc.get_media_list.clear()
    mc.shutdown()

    state.USE_PRESET = True
    state.PACKED_LAYOUT = False
    state.SHOW_CAPTIONS = False

def _set_media_source_cb():
    mc.MEDIA_SOURCE = state['media_source']
    mc.MEDIA_FILTER = None
    mc.NUM_IMAGES = state['num_images']
    mc.MEDIA_LIST_SORT = True
    mc.MEDIA_LIST_DATE_SORT = True
    mc.MEDIA_LIST_SORT_ASC = False
    mc.MEDIA_LIST, mc.MEDIA_FILTER = mc.get_media_list(
        media_source=mc.MEDIA_SOURCE, 
        media_filter=mc.MEDIA_FILTER, 
        sort_flag=mc.MEDIA_LIST_SORT,
        sort_by_date_flag=mc.MEDIA_LIST_DATE_SORT,
        ascending=mc.MEDIA_LIST_SORT_ASC
    )

    state.USE_PRESET = True
    state.PACKED_LAYOUT = False
    state.SHOW_CAPTIONS = False

def _set_media_controls_cb():
    mc.MEDIA_SOURCE = state['media_source']
    mc.MEDIA_FILTER = state['media_filter']
    mc.NUM_IMAGES = state['num_images']
    mc.MEDIA_LIST_SORT = state['media_list_sort']
    mc.MEDIA_LIST_DATE_SORT = state['media_list_date_sort']
    mc.MEDIA_LIST_SORT_ASC = state['media_list_sort_asc']
    mc.MEDIA_LIST, mc.MEDIA_FILTER = mc.get_media_list(
        media_source=mc.MEDIA_SOURCE, 
        media_filter=mc.MEDIA_FILTER, 
        sort_flag=mc.MEDIA_LIST_SORT,
        sort_by_date_flag=mc.MEDIA_LIST_DATE_SORT,
        ascending=mc.MEDIA_LIST_SORT_ASC
    )

    state.USE_PRESET = state['use_preset']
    state.PACKED_LAYOUT = state['packed_layout']
    state.SHOW_CAPTIONS = state['show_captions']
    state.NUM_COLS = state['num_cols']
    state.IMG_W = state['img_w']

# Prevents double clicking to make widget state stick
def _set_packed_layout_cb():
    state.PACKED_LAYOUT = state['packed_layout']

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
            mc.MEDIA_SOURCE = st.selectbox(
                '✨ Select media source', 
                options=list(mc.MEDIA_SOURCES.keys()),
                key='media_source'
            )
            mc.NUM_IMAGES = st.number_input(
                'Max images', 0, int(st.secrets['MAX_NUM_IMAGES']), int(mc.NUM_IMAGES), 
                100, key='num_images', help='A value of zero will not impose a limit on the number of images pulled')
            if st.form_submit_button('Apply', on_click=_set_media_source_cb):
                st.experimental_rerun()

        with st.expander('📅 Media settings', expanded=False):
            with st.form(key='media_controls_form', clear_on_submit=False):
                mc.MEDIA_FILTER = st.text_input('🔎 Filter keyword', mc.MEDIA_FILTER, key='media_filter', help='Keyword will be used to match filenames')
                c1, c2 = st.columns(2)
                mc.MEDIA_LIST_SORT = c1.checkbox('Sort', mc.MEDIA_LIST_SORT, key='media_list_sort')
                mc.MEDIA_LIST_SORT_ASC = c2.checkbox('Ascending', mc.MEDIA_LIST_SORT_ASC, disabled=(not mc.MEDIA_LIST_SORT), key='media_list_sort_asc')
                mc.MEDIA_LIST_DATE_SORT = c1.checkbox('By date', mc.MEDIA_LIST_DATE_SORT, disabled=(not mc.MEDIA_LIST_SORT), key='media_list_date_sort')
                st.caption('Sort by date and ascending only work if sort is enabled')
                if st.form_submit_button('Apply', on_click=_set_media_controls_cb):
                    st.experimental_rerun()

        with st.expander('👀 Layout settings', expanded=True):
            state.PACKED_LAYOUT = st.checkbox(
                'Packed layout', state.PACKED_LAYOUT,
                on_change=_set_packed_layout_cb,
                help='Pack images or display in a regular grid',
                key='packed_layout'
            )
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

        if (mc.MEDIA_BACKEND_STARTED):
            with st.expander('🌀 Recycle media server'):
                st.caption('Use this to reload external media config (toml) file changes')
                st.button(
                    'Recycle',
                    help='Be sure you really want to do this!',
                    on_click=_recycle_media_service_cb,
                )

    num_images = int(mc.NUM_IMAGES)
    num_cols = int(state.NUM_COLS)
    img_w = int(state.IMG_W)

    media_list, _media_filter = mc.get_media_list(
        media_source=mc.MEDIA_SOURCE,
        media_filter=mc.MEDIA_FILTER,
        sort_flag=mc.MEDIA_LIST_SORT,
        sort_by_date_flag=mc.MEDIA_LIST_DATE_SORT,
        ascending=mc.MEDIA_LIST_SORT_ASC
    )
    working_media_list = media_list[:num_images] if num_images > 0 else media_list
    images = {media: media for media in working_media_list}

    cols = cycle(st.columns(num_cols))
    for i, (img, caption) in enumerate(images.items()):
        if not 'http' in img:
            image_bytes = mc.get_media(source=mc.MEDIA_SOURCE, media=img)
            image = image_bytes
        else:
            image = img

        try:
            if state.SHOW_CAPTIONS:
                next(cols).image(image, width=img_w, output_format='auto', caption=caption)
            else:
                next(cols).image(image, width=img_w, output_format='auto')
            if (num_cols > 0) and (not state.PACKED_LAYOUT) and ((i % num_cols) == (num_cols - 1)):
                cols = cycle(st.columns(num_cols))
        except Exception as ex:
            print(f'Skipping {caption}\n', str(ex))
            pass

# -----------------------------------------------------------------------------

def about():
    st.sidebar.markdown('---')
    st.sidebar.info('''
        (c) 2022. CloudOpti Ltd. All rights reserved.
        
        [GitHub repo](https://github.com/asehmi/media-explorer-app)
    ''')

# -----------------------------------------------------------------------------

if __name__ == '__main__':
    main()
    about()
