"""API package initialization"""

from app.api import auth, public, admin, investor, files

__all__ = [
    "auth",
    "public",
    "admin",
    "investor",
    "files",
]
