import re
import base64
from io import BytesIO
from datetime import datetime

from pydub import AudioSegment
from nicegui import run, events

from components.openai_speech_to_text import generate_corrected_transcript
from state import State
from components.chat_input import ChatInput

localeText = {
    "lessThan": "未満(指定の値より小さい)",
    "greaterThan": "指定の値より大きい",
    "lessThanOrEqual": "以下(指定の値より小さい、またはそれと等しい)",
    "greaterThanOrEqual": "以上(指定の値より大きい、またはそれと等しい)",
    "inRange": "範囲選択",
    "inRangeStart": "指定の値から始まる",
    "inRangeEnd": "指定の値で終わる",
    "contains": "指定の文字を含む",
    "notContains": "指定の文字を含まない",
    "startsWith": "指定の文字から始まる",
    "endsWith": "指定の文字で終わる",
    "applyFilter": "フィルターを適用",
    "resetFilter": "フィルターをリセット",
    "clearFilter": "フィルターを解除",
    "cancelFilter": "フィルターをキャンセル",
    "columns": "表示項目選択",
    "filters": "フィルター",
    "equals": "指定の値(文字)と等しい",
    "notEqual": "指定の値(文字)と等しくない",
    "blank": "空白",
    "notBlank": "空白以外",
    "noRowsToShow": "アカウントをダウンロードしてください。"
}

def convert_base64_to_bytesio(byte_file: bytes, mime_type: str) -> BytesIO:
    """
    Convert raw base64 data into a BytesIO with the correct file extension
    based on the mime_type from the browser.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Decide extension based on mime type
    ext = "webm"
    if "mp4" in mime_type:
        ext = "mp4"

    file_name = f"audio_{timestamp}.{ext}"
    audio_content = base64.b64decode(byte_file)
    audio_file = BytesIO(audio_content)
    audio_file.name = file_name
    return audio_file

def convert_to_wav(in_file: BytesIO, mime_type: str) -> BytesIO:
    """
    Use pydub + FFmpeg to convert the input file to .wav.
    The 'format' param depends on the mime_type from the front end.
    """
    in_file.seek(0)

    # map our mime_type to pydub's format argument
    if "mp4" in mime_type:
        pydub_format = "mp4"
    else:
        pydub_format = "webm"

    # Load the audio data
    audio_segment = AudioSegment.from_file(in_file, format=pydub_format)

    # Export to WAV in memory
    wav_file = BytesIO()
    wav_file.name = in_file.name.rsplit(".", 1)[0] + ".wav"
    audio_segment.export(wav_file, format="wav")
    wav_file.seek(0)
    return wav_file

async def handle_audio_data(
    event: events.GenericEventArguments, 
    client_state: State,
    chat_input: ChatInput,
) -> None:
    """Process and store audio data received from the frontend."""

    chat_input.record_button.props(add='loading disable')

    audio_base64 = event.args.get("audio")
    audio_length: float = event.args.get("duration")
    mime_type = event.args.get("mimeType", "audio/webm")  # default to webm if not given

    if audio_base64:
        client_state.is_processing_audio = True

        # 1) Convert base64 -> in-memory file
        original_file = await run.cpu_bound(convert_base64_to_bytesio, audio_base64, mime_type)
        # 2) Convert in-memory file -> WAV
        wav_file = await run.cpu_bound(convert_to_wav, original_file, mime_type)

        if audio_length > 1:
            # 3) Transcribe the WAV file
            text_from_speech = await run.io_bound(generate_corrected_transcript, wav_file, client_state.openai_speech_prompt)
            client_state.last_text_from_speech = text_from_speech
            chat_input.input_question.set_value(value=text_from_speech)

        client_state.is_processing_audio = False
    
    chat_input.record_button.props(remove='loading disable')