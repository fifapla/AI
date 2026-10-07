# Dynamic Semantic Chunker

A context-aware text chunking utility designed for RAG pipelines to dynamically group sentences based on semantic boundaries rather than fixed token limits.


**Note:** despite the name, this groups a fixed number of sentences per chunk - it does not detect actual semantic/topic boundaries. A real semantic chunker would need sentence embeddings to measure topic shifts.
