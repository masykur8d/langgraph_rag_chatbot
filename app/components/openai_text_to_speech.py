import aiofiles
import tempfile

from openai import AsyncOpenAI

client = AsyncOpenAI()

async def text_to_speech(text: str) -> str:
    """Generate speech asynchronously and stream it to a temporary file while playing it in NiceGUI."""
    
    temp_audio_path = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
    
    async with client.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice="shimmer",
        input=text,
        response_format='mp3'
    ) as response:
        
        async with aiofiles.open(temp_audio_path, 'wb') as f:
            async for chunk in response.iter_bytes():
                await f.write(chunk)

    return temp_audio_path