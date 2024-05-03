from hackathon.stt import STTBase
import openai
import os


class OpenAISTT(STTBase):
    def __init__(self, api_key):
        super().__init__()
        if api_key is None:
            api_key = os.getenv('OPENAI_API_KEY')
            assert isinstance(api_key, str)

        openai.api_key = api_key
        self.client = openai.Audio

    async def get_text(self, audio_data):
        with open(audio_data, 'rb') as audio_file:
            response = await self.client.transcribe(
                model="whisper-large",
                file=audio_file
            )
            return response['text']