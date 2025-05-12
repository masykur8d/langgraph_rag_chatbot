from io import BytesIO
from typing import Literal, Union, List, Optional

from nicegui import ui

from components.openai_text_to_speech import text_to_speech
from state import State

class Message(ui.chat_message):
    def __init__(self,
                 text: Union[str, List[str]] = ...,  # ✅ Default matches ui.chat_message
                 sent: bool = False,
                 avatar: Optional[str] = None,
                 name: Optional[str] = None,
                 stamp: Optional[str] = None,
                 message_type: Literal['text', 'audio'] = "text",
                 sender_type: Literal['chat_bot_message', 'human_message'] = "human_message",
                 message_text_to_speech: Optional[BytesIO] = None,
                 message_audio_path: Optional[str] = None,
                 message_audio_to_text: Optional[str] = None,
                 client_state: State = None,
                 *args, **kwargs):  
        """Custom chat message that supports text, audio, and additional metadata."""

        self.stored_text = text if isinstance(text, str) else " ".join(text) if isinstance(text, list) else ""

        super().__init__(text=text, avatar=avatar, name=name, stamp=stamp, sent=sent, *args, **kwargs)  

        self.message_type = message_type
        self.sender_type = sender_type
        self.message_text_to_speech = message_text_to_speech
        self.message_audio_path = message_audio_path
        self.message_audio_to_text = message_audio_to_text
        self.client_state = client_state

        with self.add_slot('name'):
            with ui.row(align_items='center').classes('w-full').style('gap: 0rem'):
                if sent:
                    ui.space()
                ui.markdown(content=name)
                if not sent:
                    tts_trigger_button = ui.button(icon='volume_up', on_click=lambda: self.get_audio_from_text_file_path()).props('flat padding="xs xs"')
                    self.tts_trigger_button = tts_trigger_button


    async def get_audio_from_text_file_path(self):
        self.tts_trigger_button.props(add='disable loading')
        if not self.message_audio_path:
            self.message_audio_path = await text_to_speech(text=self.stored_text)
        self.client_state.player_pop_up.refresh(self.message_audio_path, True)
        self.tts_trigger_button.props(remove='disable loading')


    def speak(self):
        """Use JavaScript SpeechSynthesis API for text-to-speech."""
        js_code = f'''
        var msg = new SpeechSynthesisUtterance("{self.text[0]}");
        msg.lang = "ja-JP";  // ✅ Set to Japanese
        window.speechSynthesis.speak(msg);
        '''
        ui.run_javascript(js_code)  # ✅ Run JavaScript to trigger TTS
