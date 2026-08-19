"""
Vector Database Service
Stores and retrieves embeddings from Supabase pgvector
"""

import os
from supabase import create_client, Client
from typing import List, Dict
import math
import json


class VectorDB:

    def __init__(self):
        """Initialize Supabase client"""

        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            raise Exception(
                "❌ Missing SUPABASE_URL or SUPABASE_KEY in .env"
            )

        self.client: Client = create_client(
            supabase_url,
            supabase_key
        )

        print("✅ Connected to Supabase pgvector")


    # ============================================================
    # STORE CHUNKS
    # ============================================================

    def store_chunks(
        self,
        user_id: str,
        doc_id: str,
        filename: str,
        chunks: List[str],
        embeddings: List[List[float]]
    ) -> int:

        """
        Store document chunks and embeddings in Supabase.

        Each chunk is associated with a user_id so that
        different users/clients cannot retrieve each other's
        documents.
        """

        stored_count = 0

        for i, (chunk, embedding) in enumerate(
            zip(chunks, embeddings)
        ):

            try:

                # DEBUG
                print(
                    f"User ID: {user_id}"
                )

                print(
                    f"Embedding type: {type(embedding)}"
                )

                print(
                    f"Embedding preview: "
                    f"{str(embedding)[:100]}"
                )

                self.client.table("documents").insert({

                    "user_id": user_id,

                    "doc_id": doc_id,

                    "filename": filename,

                    "chunk_index": i,

                    "chunk_text": chunk,

                    "embedding": embedding

                }).execute()

                stored_count += 1

            except Exception as e:

                print(
                    f"❌ Error storing chunk {i}: "
                    f"{str(e)}"
                )


        print(
            f"✅ Stored "
            f"{stored_count}/{len(chunks)} "
            f"chunks for user {user_id}"
        )

        return stored_count


    # ============================================================
    # SEARCH SIMILAR CHUNKS
    # ============================================================

    def search_similar(
        self,
        user_id: str,
        query_embedding: List[float],
        limit: int = 5
    ) -> List[Dict]:

        """
        Search for similar chunks belonging ONLY to the
        specified user_id.
        """

        try:

            # ----------------------------------------------------
            # IMPORTANT:
            # Only retrieve documents belonging to this user.
            # ----------------------------------------------------

            response = (
                self.client
                .table("documents")
                .select(
                    "id, user_id, doc_id, filename, "
                    "chunk_index, chunk_text, embedding"
                )
                .eq("user_id", user_id)
                .execute()
            )


            if not response.data:

                print(
                    f"⚠️ No documents found "
                    f"for user {user_id}"
                )

                return []


            print(
                f"🔎 Searching "
                f"{len(response.data)} chunks "
                f"for user {user_id}"
            )


            # ----------------------------------------------------
            # COSINE SIMILARITY
            # ----------------------------------------------------

            def cosine_similarity(
                vec_a: list,
                vec_b: list
            ) -> float:

                """Calculate cosine similarity."""

                dot_product = sum(
                    x * y
                    for x, y in zip(
                        vec_a,
                        vec_b
                    )
                )

                norm_a = math.sqrt(
                    sum(
                        x * x
                        for x in vec_a
                    )
                )

                norm_b = math.sqrt(
                    sum(
                        x * x
                        for x in vec_b
                    )
                )

                if norm_a == 0 or norm_b == 0:
                    return 0.0

                return (
                    dot_product /
                    (norm_a * norm_b)
                )


            # ----------------------------------------------------
            # SCORE USER'S CHUNKS
            # ----------------------------------------------------

            scored_chunks = []

            for chunk in response.data:

                retrieved_embedding = (
                    chunk["embedding"]
                )


                # Supabase may return vector as string

                if isinstance(
                    retrieved_embedding,
                    str
                ):

                    try:

                        retrieved_embedding = (
                            json.loads(
                                retrieved_embedding
                            )
                        )

                    except json.JSONDecodeError:

                        # Handle PostgreSQL vector format:
                        # "[0.1,0.2,0.3]"

                        retrieved_embedding = (
                            retrieved_embedding
                            .strip("[]")
                            .split(",")
                        )


                # Convert everything to float

                retrieved_embedding = [
                    float(x)
                    for x in retrieved_embedding
                ]


                similarity_score = cosine_similarity(
                    query_embedding,
                    retrieved_embedding
                )


                scored_chunks.append({

                    "user_id": chunk["user_id"],

                    "doc_id": chunk["doc_id"],

                    "filename": chunk["filename"],

                    "chunk_index": chunk["chunk_index"],

                    "chunk_text": chunk["chunk_text"],

                    "similarity": similarity_score

                })


            # ----------------------------------------------------
            # SORT BY SIMILARITY
            # ----------------------------------------------------

            top_results = sorted(
                scored_chunks,
                key=lambda x: x["similarity"],
                reverse=True
            )[:limit]


            print(
                "🔎 Top results:"
            )

            for result in top_results:

                print(
                    f"   📄 "
                    f"{result['filename']} "
                    f"| Chunk "
                    f"{result['chunk_index']} "
                    f"| Similarity "
                    f"{result['similarity']:.4f}"
                )


            return top_results


        except Exception as e:

            print(
                "❌ Error searching similar "
                f"chunks: {str(e)}"
            )

            return []


    # ============================================================
    # DELETE DOCUMENT
    # ============================================================

    def delete_document(
        self,
        user_id: str,
        doc_id: str
    ) -> bool:

        """
        Delete a document ONLY if it belongs to
        the specified user.
        """

        try:

            self.client.table(
                "documents"
            ).delete().eq(
                "doc_id",
                doc_id
            ).eq(
                "user_id",
                user_id
            ).execute()


            print(
                f"✅ Deleted document "
                f"{doc_id} for user {user_id}"
            )

            return True


        except Exception as e:

            print(
                f"❌ Error deleting document: "
                f"{str(e)}"
            )

            return False


    # ============================================================
    # GET DOCUMENT COUNT
    # ============================================================

    def get_document_count(
        self,
        user_id: str = None
    ) -> int:

        """
        Get document chunk count.

        If user_id is provided, only count that user's
        chunks.
        """

        try:

            query = (
                self.client
                .table("documents")
                .select(
                    "id",
                    count="exact"
                )
            )


            if user_id:

                query = query.eq(
                    "user_id",
                    user_id
                )


            response = query.execute()


            return (
                response.count
                if response.count
                else 0
            )


        except Exception as e:

            print(
                f"❌ Error getting "
                f"document count: {str(e)}"
            )

            return 0


# ============================================================
# GLOBAL INSTANCE
# ============================================================

vector_db = VectorDB()