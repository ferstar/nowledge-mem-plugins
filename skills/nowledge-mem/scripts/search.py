"""Deep memory search with progressive disclosure (from deep-mem)"""

from dataclasses import dataclass, field
from typing import Any

from scripts.api import APIClient


@dataclass
class MemoryItem:
    """A single memory from search results"""

    memory_id: str
    title: str | None
    content: str
    similarity_score: float
    importance: float
    labels: list[str]
    source_thread_id: str | None = None


@dataclass
class ThreadRef:
    """Reference to a related thread"""

    thread_id: str
    title: str | None
    summary: str | None
    message_count: int


@dataclass
class DeepSearchResult:
    """Result of a deep memory search"""

    query: str
    memories: list[MemoryItem] = field(default_factory=list)
    related_threads: list[ThreadRef] = field(default_factory=list)
    total_memories_found: int = 0
    total_threads_found: int = 0


class DeepMemorySearcher:
    """Progressive disclosure search for memories and threads"""

    def __init__(self, client: APIClient):
        self.client = client

    def search(
        self,
        query: str,
        memory_limit: int = 10,
        thread_limit: int = 5,
        expand_threads: bool = True,
    ) -> DeepSearchResult:
        """Search memories with progressive thread discovery

        Phase 1: Search memories
        Phase 2: Discover related threads (if expand_threads=True)
        """
        result = DeepSearchResult(query=query)

        # Phase 1: Search memories
        mem_response = self.client.search_memories(query, limit=memory_limit)

        # Handle various response formats:
        # 1. List of {memory: {...}, similarity_score: ...}
        # 2. Dict with {memories: [...], total: ...}
        # 3. Direct list of memory objects
        if isinstance(mem_response, list):
            memories_data = mem_response
            result.total_memories_found = len(memories_data)
        else:
            memories_data = mem_response.get("memories", [])
            result.total_memories_found = mem_response.get("total", len(memories_data))

        for item in memories_data:
            # Handle {memory: {...}, similarity_score: ...} format
            if "memory" in item:
                m = item["memory"]
                score = item.get("similarity_score", 0.0)
            else:
                m = item
                score = m.get("similarity_score", 0.0)

            result.memories.append(
                MemoryItem(
                    memory_id=m.get("id", ""),
                    title=m.get("title"),
                    content=m.get("content", ""),
                    similarity_score=score,
                    importance=m.get("importance", 0.5),
                    labels=m.get("labels", []),
                    source_thread_id=m.get("source_thread_id"),
                )
            )

        # Phase 2: Thread discovery
        if expand_threads and thread_limit > 0:
            # Strategy 1: Use source_thread_id from memories (direct reference)
            thread_ids_from_memories: set[str] = set()
            for mem in result.memories:
                if mem.source_thread_id:
                    thread_ids_from_memories.add(mem.source_thread_id)

            # Fetch threads by ID if we have references
            for tid in list(thread_ids_from_memories)[:thread_limit]:
                try:
                    thread_data = self.client.get_thread(tid)
                    # get_thread returns {"thread": {...}, "messages": [...]}
                    thread_obj = thread_data.get("thread", thread_data)
                    result.related_threads.append(
                        ThreadRef(
                            thread_id=thread_obj.get("thread_id", thread_obj.get("id", "")),
                            title=thread_obj.get("title"),
                            summary=thread_obj.get("summary"),
                            message_count=thread_obj.get("message_count", 0),
                        )
                    )
                except Exception:
                    pass  # Thread may have been deleted

            # Strategy 2: If no thread references found, search by query
            if not result.related_threads:
                thread_response = self.client.search_threads(query, limit=thread_limit)

                # Handle both list and dict responses
                if isinstance(thread_response, list):
                    threads_data = thread_response
                    result.total_threads_found = len(threads_data)
                else:
                    threads_data = thread_response.get("threads", [])
                    result.total_threads_found = thread_response.get("total", len(threads_data))

                for t in threads_data:
                    result.related_threads.append(
                        ThreadRef(
                            thread_id=t.get("thread_id", t.get("id", "")),
                            title=t.get("title"),
                            summary=t.get("summary"),
                            message_count=t.get("message_count", 0),
                        )
                    )
            else:
                result.total_threads_found = len(result.related_threads)

        return result
