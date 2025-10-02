from pydantic import BaseModel, Field

class Reqinvocations(BaseModel):
    voice_id: str  = Field( description="Voice ID", example="39251bb8-8cea-59f1-9f3b-e4f255b8875b")
    language: str = Field( description="Text language", example="en_US")
    emotion: str = Field("neutral", description="emotion", example="neutral")
    text: str = Field( description="Text to synthesize into speech",example="How are things with you lately? I’d love to hear what you’ve been up to.")