import re
from typing import Literal, Union, List, Optional

from nicegui import ui, app, run

from state import State
from langgraph.graph.graph import CompiledGraph

from components.user_db import get_shop_information, User
from utils.custom_css import slide_up_bounce, message_hover_animation, pulse_custom
from components.chat_message import Message
from state import State

def is_japanese(text: str) -> bool:
    japanese_pattern = re.compile(r'[\u3040-\u30FF\u4E00-\u9FAF]')
    return bool(japanese_pattern.search(text))

class ChatInput(ui.row):
    def __init__(
            self, 
            *, 
            wrap = True, 
            align_items = 'center',
            message_text: Optional[str] = None,
            message_container : ui.column,
            shop_information: User,
            client_state: State,
        ):
        super().__init__(
            wrap=wrap, 
            align_items=align_items
        )

        self.message_text = message_text
        self.message_container = message_container
        self.shop_information = shop_information
        self.client_state = client_state

        with self.classes('w-full no-wrap items-center'):
            with ui.input(placeholder="質問を入力してください！").props('autogrow filled clearable').classes("w-full") as input_question:
                with input_question.add_slot('append'):
                    self.send_button = ui.button(
                        text='送信', 
                        color='teal', 
                        on_click=self.send_message,
                    ).classes('ml-3')
                with input_question.add_slot('prepend'):                    
                    self.record_button = ui.button(
                        icon='mic', 
                        color='primary',
                        on_click=self.toggle_record_button,
                    ).props('flat size="lg" padding="xs xs"')
            self.input_question = input_question

    # -------------------------- Function to update ui -------------------------- #
    async def send_message(self) -> None:
        question = getattr(self.input_question, 'value', '')
        if question is None:
            return
        elif len(question) == 0:
            ui.notify('質問を入力してから送信ボタンを押してください！', type='warning', close_button=True, position='top')
            return
        elif len(question) <= 2:
            ui.notify('質問を細かく書いてください！', type='warning', close_button=True, position='top')
            return

        self.send_button.props(add='disable loading')
        is_japanese_text = await run.cpu_bound(is_japanese, question)
        if not is_japanese_text:
            self.send_button.props(remove='disable loading')
            ui.notify('日本語で書いてください！', type='warning', close_button=True, position='top')
            return

        self.input_question.value = ''
        with self.message_container:
            Message(text=question, avatar='/icon/user_icon.png', name='あなた', sent=True, stamp=self.client_state.get_time_stamp(), client_state=self.client_state).props('bg-color="amber-7"').classes(message_hover_animation)
            response_message = Message(avatar='/icon/bot_icon.png', name=self.shop_information.bot_name, sent=False, stamp=self.client_state.get_time_stamp(), client_state=self.client_state).classes(message_hover_animation)
            with response_message:
                with ui.column(align_items='center').classes('w-full'):
                    ui.spinner(type='dots', size='3rem')
            ui.run_javascript('window.scrollTo(0, document.body.scrollHeight)')

        inputs = {
            "messages": [
                ("user", f"{question}"),
            ]
        }

        response = ''
        
        async for msg, metadata in self.client_state.graph.astream(inputs, stream_mode="messages", config=self.client_state.memory_config):
            if (
                msg.content 
                and (metadata["langgraph_node"] == 'generate' or metadata["langgraph_node"] == 'query_or_respond')
            ):
                response += msg.content
                with response_message.add_slot('default'):
                    response_message.stored_text = response
                    ui.markdown(response)
                ui.run_javascript('window.scrollTo(0, document.body.scrollHeight)')

        self.send_button.props(remove='disable loading')


    async def toggle_record_button(self) -> None:
        if not self.client_state.is_recording:
            # Initialize
            self.client_state.toggle_recording_status()

            # Change record button appearance
            self.record_button.icon = 'stop_circle'
            self.record_button._props['color'] = 'red'
            self.record_button.classes(add='pulse-custom')

            # Disable send button for safety
            self.send_button.props(add='disable')

            # Change input placeholder
            self.input_question.set_value('')
            self.input_question._props['placeholder'] = '声で質問してください！'
            self.input_question.update()

            # Star the js for recording
            ui.run_javascript("startRecording()")
        else:
            # Initialize
            self.client_state.toggle_recording_status()

            # Star the js for recording
            ui.run_javascript("stopRecording()")

            # Change record button appearance back
            self.record_button.icon = 'mic'
            self.record_button._props['color'] = 'primary'
            self.record_button.classes(remove='pulse-custom')

            # Enabled send button for safety
            self.send_button.props(remove='disable')

            # Change input placeholder
            self.input_question.set_value('')
            self.input_question._props['placeholder'] = '質問を入力してください！'
            self.input_question.update()