"""Authorization domain models for user identity and context.

This module defines the UserContext which is passed through the retrieval pipeline
to ensure that evidence is filtered based on the requester's identity and roles.
"""

from pydantic import BaseModel, Field

class UserContext(BaseModel):
    """The identity and attributes of the user making a request.

    This context is used by the AuthorizationEngine to determine access to chunks.
    """
    user_id: str
    roles: tuple[str, ...] = Field(default=(), description="Roles assigned to the user (e.g., 'employee', 'hr', 'admin').")
    department: str | None = Field(default=None, description="The user's primary department.")
    tenant_id: str = Field(default="nexacore", description="The tenant the user belongs to.")
