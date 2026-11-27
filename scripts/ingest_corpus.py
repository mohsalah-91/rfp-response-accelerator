from pathlib import Path
import os
import requests
import frontmatter

corpus_path = Path(__file__).resolve().parent.parent / "corpus"
ingest_url = os.environ.get("INGEST_URL", "http://127.0.0.1:8000") + "/documents/ingest"
failures = []
ingested_files = []
chunks_ingested = 0


for path in corpus_path.rglob("*.md"):
    try:
        post = frontmatter.load(path)
        content = post.content
        relative_title = path.relative_to(corpus_path).as_posix()
        print(f"Processing {relative_title}...")
        response = requests.post(
            ingest_url,
            json={"title": relative_title,"content": content},
            timeout = 120
            )
        response.raise_for_status()
        payload = response.json()
        chunks_ingested += payload["chunks_processed"]
        ingested_files.append(relative_title)
        print(f"Successfully ingested {relative_title} ({payload['chunks_processed']} chunks).")

    except Exception as e:
        print(f"Error processing {path}: {e}")
        failures.append((path, str(e)))


if failures:
    for path, error in failures:
        print(f"  {path}: {error}")
else:
    print("All files processed successfully without errors.")
    
    
print("Ingestion completed.")
print(f"Total documents processed: {len(ingested_files) + len(failures)}")
print(f"Successfully ingested documents: {len(ingested_files)}")
print(f"Successfully ingested chunks: {chunks_ingested}")
print(f"Failed files: {len(failures)}")
print("Ingested files:")
for file in ingested_files:
    print(f"  {file}")
