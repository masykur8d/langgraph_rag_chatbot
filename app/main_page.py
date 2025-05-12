import os
import asyncio

from nicegui import ui, app, run
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request

# Load environtment variables
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=env_path, override=True)

from state import State
from utils.python_utils import handle_audio_data
from utils.js_utils import audio_and_lenght_recording_utils
from utils.custom_css import slide_up_bounce, message_hover_animation, pulse_custom
from components.user_db import get_shop_information
from components.chat_message import Message
from components.chat_input import ChatInput

import admin_page


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_static_files('/icon', 'icon')

@ui.page('/{shop_name}', favicon='🚀', title='FMCAIサポートデスク')
async def page(shop_name : str, request: Request):
    # -------------------------- Starting app loding -------------------------- #
    with ui.card().tight().classes('fixed-center') as startup_element:
        with ui.column().classes('fixed-center'):
            ui.spinner('comment', size='13em', color="deep-purple")

    # -------------------------- Checking shop name -------------------------- #
    if shop_name is None:
        return

    shop_information = await run.io_bound(get_shop_information, shop_name)
    if (
        not shop_information 
        or shop_information.disabled 
        or shop_name != shop_information.shop_name_en
    ):
        return
    
    # -------------------------- Initialize page -------------------------- #
    ui.page_title(title=shop_information.shop_name_en)
    ui.add_head_html(slide_up_bounce)
    ui.add_head_html(audio_and_lenght_recording_utils)
    ui.add_head_html(pulse_custom)
    ui.on('audio_data', lambda e: handle_audio_data(event=e, client_state=client_state, chat_input=chat_input))

    ui.add_css(r'a:link, a:visited {color: inherit !important; text-decoration: none; font-weight: 500}')
    ui.query('.q-page').classes('flex')
    ui.query('.nicegui-content').classes('w-full')

    # -------------------------- Dialog section -------------------------- #
    with ui.dialog().props('persistent') as reset_dialog, ui.card():
        ui.markdown('チャットを初めからやります？')
        with ui.row().classes('w-full'):
            ui.space()
            ui.button('適用', color='teal', on_click=lambda: ui.navigate.reload())
            ui.button('キャンセル', on_click=lambda: reset_dialog.close())

    @ui.refreshable
    async def player_pop_up(audio_path : str, dialog_open : bool = False):
        with ui.dialog().props('position="bottom"') as player_dialog, ui.card():
            with ui.column(align_items='center').classes('w-full'):
                ui.markdown(content=shop_information.bot_name)
                from_text_audio = ui.audio(src=audio_path)
                from_text_audio.on('ended', lambda: player_dialog.close())

        if dialog_open:
            player_dialog.open()
            await asyncio.sleep(0.3)
            from_text_audio.play()

    await player_pop_up('', False)

    # -------------------------- Initialize objects -------------------------- #
    client_state = State(
        shop_name=shop_name,
        vector_db_namespace=shop_information.vector_db_namespace,
        openai_chat_prompt=shop_information.openai_chat_prompt,
        openai_speech_prompt=shop_information.openai_speech_prompt,
        player_pop_up=player_pop_up,
    )
    await client_state.initialize()
        
    # -------------------------- Header section -------------------------- #
    with ui.header(bordered=True).classes('items-center text-black bg-white h-[5rem]'), ui.column(align_items='center').classes('w-full max-w-3xl mx-auto'):
        with ui.row(align_items='center').classes('w-full no-wrap items-center'):
            with ui.avatar(color="white", rounded=True):
                ui.image(source='/icon/bot_icon.png')
                ui.badge(color='green').props('floating rounded').classes('animate-bounce')
            ui.markdown(f'{shop_information.bot_name}<br>**{shop_information.shop_name_jp}**')
            ui.space()
            with ui.column(align_items='center'):
                ui.button(icon='restart_alt', on_click=lambda: reset_dialog.open()).props('flat size="lg" padding="xs md"')

    await ui.context.client.connected(timeout=120)
    startup_element.clear()


    # -------------------------- Message body secton -------------------------- #
    message_container = ui.column().classes('w-full max-w-2xl mx-auto flex-grow items-stretch')
    with message_container:
        response_first_message = Message(avatar='/icon/bot_icon.png', name=shop_information.bot_name, stamp=client_state.get_time_stamp(), sent=False, client_state=client_state).classes(message_hover_animation)
        response_first_text = ''
        async for i in client_state.stream_manual_message(message=shop_information.first_message):
            response_first_text += i
            with response_first_message.add_slot('default'):
                response_first_message.stored_text = response_first_text
                ui.markdown(response_first_text)

    # -------------------------- Footer section -------------------------- #
    with ui.footer(bordered=True).classes('bg-white').style('animation: slideUpBounce 0.5s ease-in-out forwards;'), ui.column(align_items='center').classes('w-full max-w-3xl mx-auto'):
        chat_input =  ChatInput(message_container=message_container, shop_information=shop_information, client_state=client_state)


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(reload=True, port=408, storage_secret=os.getenv('NICEGUI_SECRET_KEY'), language='ja')