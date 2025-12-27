"""Unified API client for Nowledge Mem server"""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

SUCCESS_CODES = frozenset({200, 201, 202, 204})


class APIError(Exception):
    """Raised when API request fails

    Attributes:
        status_code: HTTP status code (if available)
        response_text: Response body (if available)
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_text: str | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


class APIClient:
    """Unified HTTP client for Nowledge Mem API

    Combines functionality from all mem-* skills:
    - Memory CRUD (add, search, update, delete)
    - Thread operations (save, search, get, expand)
    - Labels management
    """

    def __init__(
        self,
        base_url: str,
        auth_token: str,
        timeout: float = 30.0,
        timeout_health: float = 5.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token
        self.timeout = timeout
        self.timeout_health = timeout_health
        self._client: httpx.Client | None = None

    def _get_client(self) -> httpx.Client:
        """Get or create HTTP client with connection pooling"""
        if self._client is None:
            headers = {"Content-Type": "application/json"}
            # Only add Authorization header if auth_token is provided
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            self._client = httpx.Client(
                headers=headers,
                timeout=self.timeout,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            )
        return self._client

    def close(self) -> None:
        """Close the HTTP client and release connections"""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "APIClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.close()
        return False

    # ========== Health & Auth ==========

    def health_check(self) -> tuple[bool, str | None]:
        """Check API health endpoint

        Returns:
            Tuple of (is_healthy, error_message)
        """
        client = self._get_client()
        try:
            response = client.get(
                f"{self.base_url}/health",
                timeout=self.timeout_health,
            )
            if response.status_code == 200:
                return True, None
            return False, f"Health check returned {response.status_code}"

        except httpx.TimeoutException:
            return False, f"Health check timeout after {self.timeout_health}s"
        except httpx.ConnectError as e:
            return False, f"Connection failed: {e}"
        except httpx.RequestError as e:
            return False, f"Request error: {type(e).__name__}: {e}"

    def auth_check(self) -> tuple[bool, str | None]:
        """Verify authentication by attempting a minimal authenticated request"""
        client = self._get_client()
        try:
            response = client.get(
                f"{self.base_url}/threads",
                params={"limit": 1},
                timeout=self.timeout_health,
            )

            if response.status_code == 401:
                return False, "Authentication failed: invalid or expired token"
            if response.status_code == 403:
                return False, "Authorization failed: insufficient permissions"
            if response.status_code in SUCCESS_CODES:
                return True, None

            return True, f"Auth check returned {response.status_code} (may be OK)"

        except httpx.TimeoutException:
            return False, f"Auth check timeout after {self.timeout_health}s"
        except httpx.RequestError as e:
            return False, f"Auth check failed: {type(e).__name__}: {e}"

    # ========== Memory Operations (mem-add, mem-manage) ==========

    def add_memory(
        self,
        content: str,
        title: str | None = None,
        importance: float = 0.5,
        labels: str | None = None,
        event_start: str | None = None,
        event_end: str | None = None,
        temporal_context: str | None = None,
    ) -> dict[str, Any]:
        """Add a new memory"""
        client = self._get_client()
        payload: dict[str, Any] = {"content": content, "importance": importance}

        if title:
            payload["title"] = title
        if labels:
            payload["labels"] = [l.strip() for l in labels.split(",") if l.strip()]
        if event_start:
            payload["event_start"] = event_start
        if event_end:
            payload["event_end"] = event_end
        if temporal_context:
            payload["temporal_context"] = temporal_context

        response = client.post(f"{self.base_url}/memories", json=payload)

        if response.status_code not in SUCCESS_CODES:
            raise APIError(
                f"Add memory failed: {response.status_code} - {response.text[:200]}",
                status_code=response.status_code,
                response_text=response.text,
            )
        return response.json()

    def update_memory(
        self,
        memory_id: str,
        content: str | None = None,
        title: str | None = None,
        importance: float | None = None,
        labels: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing memory"""
        client = self._get_client()
        payload: dict[str, Any] = {}

        if content is not None:
            payload["content"] = content
        if title is not None:
            payload["title"] = title
        if importance is not None:
            payload["importance"] = importance
        if labels is not None:
            payload["labels"] = labels

        response = client.patch(f"{self.base_url}/memories/{memory_id}", json=payload)

        if response.status_code not in SUCCESS_CODES:
            raise APIError(
                f"Update memory failed: {response.status_code} - {response.text[:200]}",
                status_code=response.status_code,
                response_text=response.text,
            )
        return response.json()

    def delete_memory(self, memory_id: str) -> dict[str, Any]:
        """Delete a memory"""
        client = self._get_client()
        response = client.delete(f"{self.base_url}/memories/{memory_id}")

        if response.status_code not in SUCCESS_CODES:
            raise APIError(
                f"Delete memory failed: {response.status_code} - {response.text[:200]}",
                status_code=response.status_code,
                response_text=response.text,
            )
        return {"status": "deleted", "memory_id": memory_id}

    def get_memory(self, memory_id: str) -> dict[str, Any]:
        """Get a specific memory by ID"""
        client = self._get_client()
        response = client.get(f"{self.base_url}/memories/{memory_id}")

        if response.status_code not in SUCCESS_CODES:
            raise APIError(
                f"Get memory failed: {response.status_code}",
                status_code=response.status_code,
            )
        return response.json()

    def search_memories(
        self,
        query: str,
        limit: int = 10,
        mode: str = "deep",
        filter_labels: str | None = None,
    ) -> dict[str, Any]:
        """Search memories with semantic search"""
        client = self._get_client()
        payload: dict[str, Any] = {
            "query": query,
            "limit": limit,
            "mode": mode,
        }
        if filter_labels:
            payload["filter_labels"] = filter_labels

        response = client.post(f"{self.base_url}/memories/search", json=payload)

        if response.status_code not in SUCCESS_CODES:
            raise APIError(
                f"Memory search failed: {response.status_code} - {response.text[:200]}",
                status_code=response.status_code,
            )
        return response.json()

    # ========== Labels (mem-manage) ==========

    def list_labels(self) -> dict[str, Any]:
        """List all memory labels"""
        client = self._get_client()
        response = client.get(f"{self.base_url}/labels")

        if response.status_code not in SUCCESS_CODES:
            raise APIError(
                f"List labels failed: {response.status_code} - {response.text[:200]}",
                status_code=response.status_code,
            )
        return response.json()

    # ========== Thread Operations (mem-persist, deep-mem) ==========

    def save_thread(
        self,
        payload: dict[str, Any],
        retry_count: int = 1,
    ) -> dict[str, Any]:
        """Save thread to Nowledge Mem"""
        client = self._get_client()
        last_error: APIError | None = None

        for attempt in range(retry_count + 1):
            try:
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt}/{retry_count}")

                response = client.post(
                    f"{self.base_url}/threads",
                    json=payload,
                    timeout=self.timeout,
                )

                if response.status_code in SUCCESS_CODES:
                    if response.status_code == 204:
                        return {"status": "success", "thread": payload}
                    return response.json()

                # Non-retryable errors
                if response.status_code in (400, 401, 403, 404, 422):
                    raise APIError(
                        f"API error {response.status_code}: {response.text[:500]}",
                        status_code=response.status_code,
                        response_text=response.text,
                    )

                # Retryable server errors (5xx)
                last_error = APIError(
                    f"Server error {response.status_code}: {response.text[:200]}",
                    status_code=response.status_code,
                    response_text=response.text,
                )

            except httpx.TimeoutException as e:
                last_error = APIError(f"Request timeout after {self.timeout}s: {e}")
            except httpx.ConnectError as e:
                last_error = APIError(f"Connection failed: {e}")
            except httpx.RequestError as e:
                last_error = APIError(f"Request failed: {type(e).__name__}: {e}")

        raise last_error or APIError("Unknown error after retries")

    def search_threads(
        self,
        query: str,
        limit: int = 20,
        mode: str = "full",
    ) -> dict[str, Any]:
        """Search threads with message matching"""
        client = self._get_client()
        params = {
            "query": query,
            "limit": limit,
            "mode": mode,
        }

        response = client.get(f"{self.base_url}/threads/search", params=params)

        if response.status_code not in SUCCESS_CODES:
            raise APIError(
                f"Thread search failed: {response.status_code} - {response.text[:200]}",
                status_code=response.status_code,
            )
        return response.json()

    def get_thread(self, thread_id: str) -> dict[str, Any]:
        """Get a specific thread with all messages"""
        client = self._get_client()
        response = client.get(f"{self.base_url}/threads/{thread_id}")

        if response.status_code not in SUCCESS_CODES:
            raise APIError(
                f"Get thread failed: {response.status_code}",
                status_code=response.status_code,
            )
        return response.json()

    def get_thread_summaries(self, limit: int = 50) -> dict[str, Any]:
        """Get thread summaries/titles"""
        client = self._get_client()
        response = client.get(
            f"{self.base_url}/threads/summaries",
            params={"limit": limit},
        )

        if response.status_code not in SUCCESS_CODES:
            raise APIError(
                f"Get summaries failed: {response.status_code}",
                status_code=response.status_code,
            )
        return response.json()
