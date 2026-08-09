"""Central authorization engine for enforcing access control.

This module implements the 'Golden Rule' for document access: a chunk is accessible
if the user is the owner, has the required role, is in the allowed department,
or if the chunk is marked as public.
"""

from typing import Any

from hybridrag.authorization.models import UserContext
from hybridrag.domain import Chunk, Classification

# ChromaDB 'where' filter values are scalar / dict-of-dict. The set of keys
# we emit is heterogeneous (str, Classification, list-of-dicts), so we type
# the filter broadly instead of forcing a single value-type.
ChromaCondition = dict[str, Any]
ChromaFilter = dict[str, Any]


class AuthorizationEngine:
    """Logic for determining if a UserContext is authorized to access a Chunk."""

    @staticmethod
    def is_authorized(user_context: UserContext, chunk: Chunk) -> bool:
        """Check if the user is authorized to access a specific chunk.

        Authorization is granted if ANY of these conditions are met:
        1. Public access: classification is PUBLIC.
        2. Ownership: user_id matches owner_user_id.
        3. Strict Classification checks for CONFIDENTIAL and RESTRICTED.
        4. Departmental access: classification is DEPARTMENT_INTERNAL and departments match.
        5. General Role/Department access for non-strict documents.
        """
        # 1. Public Access
        if chunk.classification == Classification.PUBLIC:
            return True

        # 2. Ownership
        if chunk.owner_user_id and chunk.owner_user_id == user_context.user_id:
            return True

        # 3. Strict Classification Checks
        if chunk.classification == Classification.CONFIDENTIAL:
            # Confidential: User must be the owner OR (have role AND be in
            # an allowed department)
            has_role = any(role in chunk.allowed_roles for role in user_context.roles)
            dept_match = (
                user_context.department is not None
                and user_context.department in chunk.allowed_departments
            )
            return bool(has_role and dept_match)

        if chunk.classification == Classification.RESTRICTED:
            # Restricted: User must be in the correct department AND have a required role
            has_role = any(role in chunk.allowed_roles for role in user_context.roles)
            dept_match = (
                chunk.department is not None and chunk.department == user_context.department
            )
            return bool(has_role and dept_match)

        # 4. Departmental Internal Access
        if (
            chunk.classification == Classification.DEPARTMENT_INTERNAL
            and chunk.department
            and chunk.department == user_context.department
        ):
            return True

        # 5. General Role/Department Access (for non-strict documents)
        if any(role in chunk.allowed_roles for role in user_context.roles):
            return True

        return bool(
            user_context.department is not None
            and user_context.department in chunk.allowed_departments
        )

    @staticmethod
    def build_dense_filter(user_context: UserContext) -> ChromaFilter:
        """Translate UserContext into a ChromaDB-compatible 'where' filter.

        The filter is designed to capture the 'OR' of several authorization conditions.
        Note: Complex RBAC logic often requires multiple queries or post-filtering,
        but we aim to push as much as possible to the index.
        """
        # We build a filter that matches PUBLIC or a specific department/role if applicable.
        # Since ChromaDB 'where' filters can be complex, we use $or.

        conditions: list[ChromaCondition] = []

        # Public documents
        conditions.append({"classification": {"$eq": Classification.PUBLIC}})

        # User's own documents
        conditions.append({"owner_user_id": {"$eq": user_context.user_id}})

        # User's department (for DEPARTMENT_INTERNAL)
        if user_context.department:
            dept_and: list[ChromaCondition] = [
                {"classification": {"$eq": Classification.DEPARTMENT_INTERNAL}},
                {"department": {"$eq": user_context.department}},
            ]
            conditions.append({"$and": dept_and})

        # Roles - using $in for allowed_roles is tricky because allowed_roles is a
        # tuple in the metadata. ChromaDB metadata filtering works best on scalars.
        # If roles are stored as a comma-separated string or individual keys, it's
        # easier. However, for this implementation, we will rely on index-level
        # filtering for basic classification/department and use post-filtering for
        # complex RBAC to avoid ChromaDB metadata complexity.

        return {"$or": conditions}
