from io import BytesIO
from openai import OpenAI

client = OpenAI()

def transcribe_file(audio_file: BytesIO) -> str:
    """
    Converts speech to text using Whisper (ja = Japanese).
    """
    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language="ja",
    )
    return transcription.text

def generate_corrected_transcript(audio_file: BytesIO, openai_speech_prompt : str) -> str:
    """
    1. Convert speech to text (Japanese).
    2. Use langdetect to check if the text is Japanese.
    3. If not Japanese, return "日本語で質問してください！".
    4. Otherwise, pass the transcription to ChatGPT with the system prompt,
       and get back the corrected text.
    """
    # Step 1: Transcribe
    transcription_text = transcribe_file(audio_file)

    # Step 2: Send to ChatGPT for correction
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # or whichever GPT-based model you have
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": openai_speech_prompt
            },
            {
                "role": "user",
                "content": transcription_text
            }
        ]
    )

    # Step 3: Return only the corrected text
    return response.choices[0].message.content