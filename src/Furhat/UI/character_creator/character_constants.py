from __future__ import annotations

from typing import Any

FURHAT_REALTIME_DEFAULT_HOST = "127.0.0.1"

DEFAULT_CHARACTER_TEMPLATE: dict[str, Any] = {
    "id": "",
    "name": "",
    "voiceId": "English (United States): AndrewNeural (Male, Microsoft Azure)",
    "voiceExpressivity": False,
    "inputLanguageId": "en-US",
    "gender": "Male",
    "faceId": "adult-Alex",
    "agentName": "Pepper",
    "description": "",
    "expressiveness": 1.1,
    "expressivenessFrequency": 8.0,
    "externalLinks": [],
    "category": "Private",
    "initiative": "User",
    "openingLine": "",
    "useCamera": False,
    "canEndConversation": True,
    "disengagementThreshold": "Medium",
    "useHeadPose": False,
    "logInteractions": False,
    "actionSchema": [],
}

FALLBACK_FACE_OPTIONS = [
    "adult-Alex",
    "adult-Isabel",
    "adult-Sam",
    "adult-Tiago",
    "adult-Yumi",
    "child-Luke",
    "child-Maya",
]

FALLBACK_VOICE_OPTIONS = [
    "English (United States): AndrewNeural (Male, Microsoft Azure)",
    "English (United States): JennyNeural (Female, Microsoft Azure)",
    "English (United States): GuyNeural (Male, Microsoft Azure)",
    "English (United Kingdom): RyanNeural (Male, Microsoft Azure)",
    "English (United Kingdom): SoniaNeural (Female, Microsoft Azure)",
]

FALLBACK_LANGUAGE_OPTIONS = ["en-US", "en-GB", "es-ES", "fr-FR", "de-DE", "it-IT"]
FALLBACK_GENDER_OPTIONS = ["Male", "Female", "Neutral"]
FALLBACK_CATEGORY_OPTIONS = ["Private", "Public"]
FALLBACK_INITIATIVE_OPTIONS = ["User", "System"]
FALLBACK_DISENGAGEMENT_OPTIONS = ["Low", "Medium", "High"]
