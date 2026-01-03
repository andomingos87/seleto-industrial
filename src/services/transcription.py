"""
Audio transcription service using OpenAI Whisper API.
"""

import asyncio
import tempfile
from pathlib import Path
from typing import Optional

import httpx
from openai import AsyncOpenAI

from src.config.settings import settings
from src.utils.logging import get_logger, log_api_call

logger = get_logger(__name__)


class TranscriptionService:
    """Service for transcribing audio messages."""

    def __init__(self):
        """Initialize transcription service with OpenAI client."""
        if not settings.OPENAI_API_KEY:
            logger.warning("OpenAI API key not configured, transcription will fail")
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

    async def transcribe_audio_from_url(
        self,
        audio_url: str,
        mime_type: Optional[str] = None,
        duration_seconds: Optional[float] = None,
    ) -> Optional[str]:
        """
        Download audio from URL and transcribe using Whisper API.

        Args:
            audio_url: URL of the audio file to download
            mime_type: MIME type of the audio (e.g., "audio/ogg", "audio/mpeg")
            duration_seconds: Duration of audio in seconds (for logging)

        Returns:
            Transcribed text if successful, None otherwise
        """
        if not self.client:
            logger.error("OpenAI client not initialized, cannot transcribe audio")
            return None

        try:
            # Log audio processing start
            logger.info(
                "Starting audio transcription",
                extra={
                    "audio_url": audio_url,
                    "mime_type": mime_type,
                    "duration_seconds": duration_seconds,
                },
            )

            # Download audio file
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(audio_url)
                response.raise_for_status()

                # Determine file extension from MIME type or URL
                extension = self._get_extension_from_mime_type(mime_type) or ".ogg"
                if not extension.startswith("."):
                    extension = f".{extension}"

                # Save to temporary file
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=extension, mode="wb"
                ) as tmp_file:
                    tmp_file.write(response.content)
                    tmp_file_path = tmp_file.name

            try:
                # Transcribe using OpenAI Whisper
                with open(tmp_file_path, "rb") as audio_file:
                    transcript = await self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language="pt",  # Portuguese
                    )

                transcribed_text = transcript.text

                logger.info(
                    "Audio transcription completed",
                    extra={
                        "audio_url": audio_url,
                        "duration_seconds": duration_seconds,
                        "transcription_length": len(transcribed_text),
                    },
                )

                return transcribed_text

            finally:
                # Clean up temporary file
                try:
                    Path(tmp_file_path).unlink()
                except Exception as e:
                    logger.warning(
                        f"Failed to delete temporary audio file: {e}",
                        extra={"tmp_file": tmp_file_path},
                    )

        except httpx.HTTPError as e:
            logger.error(
                f"Failed to download audio file: {e}",
                extra={"audio_url": audio_url},
                exc_info=True,
            )
            return None

        except Exception as e:
            logger.error(
                f"Failed to transcribe audio: {e}",
                extra={
                    "audio_url": audio_url,
                    "mime_type": mime_type,
                    "duration_seconds": duration_seconds,
                },
                exc_info=True,
            )
            return None

    def _get_extension_from_mime_type(self, mime_type: Optional[str]) -> Optional[str]:
        """
        Get file extension from MIME type.

        Args:
            mime_type: MIME type string (e.g., "audio/ogg", "audio/mpeg")

        Returns:
            File extension without dot (e.g., "ogg", "mp3") or None
        """
        if not mime_type:
            return None

        mime_to_ext = {
            "audio/ogg": "ogg",
            "audio/oga": "oga",
            "audio/mpeg": "mp3",
            "audio/mp3": "mp3",
            "audio/wav": "wav",
            "audio/webm": "webm",
            "audio/aac": "aac",
            "audio/m4a": "m4a",
        }

        # Try exact match first
        if mime_type in mime_to_ext:
            return mime_to_ext[mime_type]

        # Try partial match (e.g., "audio/ogg; codecs=opus")
        for mime, ext in mime_to_ext.items():
            if mime_type.startswith(mime):
                return ext

        return None


# Global service instance
transcription_service = TranscriptionService()


async def transcribe_audio(
    audio_url: str,
    mime_type: Optional[str] = None,
    duration_seconds: Optional[float] = None,
) -> Optional[str]:
    """
    Convenience function to transcribe audio from URL.

    Args:
        audio_url: URL of the audio file
        mime_type: MIME type of the audio
        duration_seconds: Duration in seconds

    Returns:
        Transcribed text or None if failed
    """
    return await transcription_service.transcribe_audio_from_url(
        audio_url, mime_type, duration_seconds
    )

