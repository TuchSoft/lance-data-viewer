#!/usr/bin/env python3
"""Create a small Lance dataset for trying out the viewer.

It writes one table, ``demo``, holding scalars, an 8-dimensional vector column
and four blob columns: a PNG, a JPEG larger than the inline limit, a WAV and an
MP4. That is enough to exercise the media preview, the vector sparkline and the
server-side filtering at the same time.

    python scripts/make-demo-dataset.py ./demo-data
    docker run --rm -p 8080:8080 -v "$(pwd)/demo-data:/data:ro" lance-data-viewer:dev
"""
import argparse
import base64
import os
import struct

import lancedb

# 1x1 red pixel.
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def wav_header():
    """A minimal but signature-valid RIFF/WAVE header."""
    return b"RIFF" + struct.pack("<I", 36) + b"WAVEfmt " + b"\x00" * 20


def mp4_header():
    """A 24-byte ISO base media header with a valid ftyp box."""
    return struct.pack(">I", 24) + b"ftypisom" + b"\x00" * 12


def big_jpeg(size=100 * 1024):
    """A JPEG signature followed by random bytes, over the 64 KiB inline cap."""
    return b"\xff\xd8\xff" + os.urandom(size)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path", nargs="?", default="./demo-data", help="directory to write into"
    )
    parser.add_argument("--rows", type=int, default=25, help="number of rows")
    args = parser.parse_args()

    os.makedirs(args.path, exist_ok=True)

    rows = []
    for i in range(args.rows):
        rows.append(
            {
                "id": i,
                "label": f"row-{i:03d}",
                "score": round(i * 1.5, 3),
                "img": PNG,
                "photo": big_jpeg(),
                "audio": wav_header(),
                "video": mp4_header(),
                "bytes": f"plain text stored as bytes {i}".encode(),
                "empty": None,
                "vec": [round((i % 10) / 10 + j / 100, 4) for j in range(8)],
            }
        )

    db = lancedb.connect(args.path)
    db.create_table("demo", data=rows, mode="overwrite")

    print(f"wrote {len(rows)} rows to {os.path.join(args.path, 'demo.lance')}")
    print("columns: id, label, score, img, photo, audio, video, bytes, empty, vec")


if __name__ == "__main__":
    main()
