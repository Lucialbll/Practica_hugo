
from pathlib import Path
import sqlite3
import json
import re

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
BUILD = ROOT / "build"
DB = BUILD / "site.db"
SEARCH_JSON = ROOT / "static" / "search.json"
TAGS_JSON = ROOT / "data" / "tags.json"


def read_front_matter(text):
    """Lee el front matter YAML sencillo."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)

    if not match:
        return {}, text

    metadata = {}

    for line in match.group(1).splitlines():
        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        if key == "tags":
            tags = re.match(r"\[(.*?)\]", value)
            metadata["tags"] = (
                [t.strip().strip("'\"") for t in tags.group(1).split(",")]
                if tags else []
            )
        else:
            metadata[key] = value.strip("'\"")

    return metadata, match.group(2)


def extract_posts():
    """Extrae los artículos Markdown publicados."""
    posts = []

    for path in CONTENT.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        metadata, body = read_front_matter(text)

        if metadata.get("draft", "false").lower() == "true":
            continue

        title = metadata.get("title", path.stem)
        tags = metadata.get("tags", [])
        relative_path = path.relative_to(CONTENT).with_suffix("").as_posix()
        url = "/" if relative_path == "_index" else "/" + relative_path + "/"

        posts.append({
    "title": title,
    "url": url,
    "tags": tags,
    "text": body.strip(),
    "words": len(re.findall(r"\b\w+\b", body))
})

    return posts


def create_database(posts):
    """Crea SQLite e inserta los artículos."""
    BUILD.mkdir(exist_ok=True)

    with sqlite3.connect(DB) as connection:
        connection.execute("DROP TABLE IF EXISTS posts")

        connection.execute("""
    CREATE TABLE posts (
        url TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        text TEXT NOT NULL,
        tags TEXT NOT NULL,
        words INTEGER NOT NULL
    )
""")

        connection.executemany(
           "INSERT INTO posts VALUES (?, ?, ?, ?, ?)",
            [
                (
                    p["url"],
                    p["title"],
                    p["text"],
                    json.dumps(p["tags"], ensure_ascii=False),
                    p["words"]
                )
                for p in posts
            ]
        )



def export_json():
    """Exporta los datos de SQLite a JSON."""
    SEARCH_JSON.parent.mkdir(exist_ok=True)
    TAGS_JSON.parent.mkdir(exist_ok=True)

    STATS_JSON = ROOT / "data" / "stats.json"

    with sqlite3.connect(DB) as connection:
        rows = connection.execute("""
            SELECT url, title, text, tags
            FROM posts
            ORDER BY title
        """).fetchall()

        search_data = [
            {
                "url": url,
                "title": title,
                "text": text,
                "tags": json.loads(tags)
            }
            for url, title, text, tags in rows
        ]

        tag_counts = {}

        for (tags_json,) in connection.execute("SELECT tags FROM posts"):
            for tag in json.loads(tags_json):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        total_words = connection.execute(
            "SELECT SUM(words) FROM posts"
        ).fetchone()[0]

    SEARCH_JSON.write_text(
        json.dumps(search_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    TAGS_JSON.write_text(
        json.dumps(tag_counts, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    STATS_JSON.write_text(
        json.dumps({"total_words": total_words}, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
def main():
    posts = extract_posts()
    create_database(posts)
    export_json()

    print(f"Artículos indexados: {len(posts)}")
    print(f"Base de datos: {DB}")
    print(f"JSON de búsqueda: {SEARCH_JSON}")
    print(f"Etiquetas: {TAGS_JSON}")


if __name__ == "__main__":
    main()
