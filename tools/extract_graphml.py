import struct
import zlib
import sys
import os


# ---------------------------------------------------------------------------
# PNG extraction
# ---------------------------------------------------------------------------

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _extract_from_png(data: bytes) -> str | None:
    #Return the GraphML string embedded in a PNG file, or None
    if data[:8] != _PNG_SIGNATURE:
        return None

    pos = 8
    while pos + 12 <= len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        chunk_type = data[pos + 4 : pos + 8]
        chunk_data = data[pos + 8 : pos + 8 + length]

        if chunk_type == b"tEXt":
            try:
                null_pos = chunk_data.index(b"\x00")
            except ValueError:
                pos += 12 + length
                continue
            keyword = chunk_data[:null_pos].decode("latin-1")
            if keyword.lower() == "graphml":
                text = chunk_data[null_pos + 1 :].decode("latin-1")
                return text

        elif chunk_type == b"zTXt":
            try:
                null_pos = chunk_data.index(b"\x00")
            except ValueError:
                pos += 12 + length
                continue
            keyword = chunk_data[:null_pos].decode("latin-1")
            if keyword.lower() == "graphml":
                # compression method byte follows null, then deflate data
                compressed = chunk_data[null_pos + 2 :]
                try:
                    text = zlib.decompress(compressed).decode("utf-8")
                    return text
                except Exception:
                    pass

        elif chunk_type == b"iTXt":
            # Keyword, null, compression flag, compression method, lang,
            # translated keyword, null, text (may be compressed)
            try:
                null_pos = chunk_data.index(b"\x00")
                keyword = chunk_data[:null_pos].decode("latin-1")
                if keyword.lower() == "graphml":
                    rest = chunk_data[null_pos + 1 :]
                    comp_flag = rest[0]
                    comp_method = rest[1]
                    rest = rest[2:]
                    # skip language tag
                    second_null = rest.index(b"\x00")
                    rest = rest[second_null + 1 :]
                    # skip translated keyword
                    third_null = rest.index(b"\x00")
                    text_bytes = rest[third_null + 1 :]
                    if comp_flag == 1:
                        text_bytes = zlib.decompress(text_bytes)
                    return text_bytes.decode("utf-8")
            except Exception:
                pass

        elif chunk_type == b"IEND":
            break

        pos += 12 + length

    return None


# ---------------------------------------------------------------------------
# JPEG extraction
# ---------------------------------------------------------------------------

_JPEG_SOI = b"\xff\xd8"


def _extract_from_jpeg(data: bytes) -> str | None:
    #Return the GraphML string embedded in a JPEG file, or None.
    if data[:2] != _JPEG_SOI:
        return None

    # Strategy 1: look for raw <?xml ... </graphml> span anywhere in the file.
    xml_start = data.find(b"<?xml")
    if xml_start == -1:
        # Also try without XML declaration
        xml_start = data.find(b"<graphml")
        if xml_start == -1:
            return None

    graphml_end = data.find(b"</graphml>", xml_start)
    if graphml_end == -1:
        return None

    xml_bytes = data[xml_start : graphml_end + len(b"</graphml>")]
    try:
        return xml_bytes.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return xml_bytes.decode("latin-1")
        except Exception:
            return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract_graphml(image_path: str) -> str | None:
    try:
        with open(image_path, "rb") as fh:
            data = fh.read()
    except OSError as exc:
        print(f"[extract_graphml] Cannot open '{image_path}': {exc}", file=sys.stderr)
        return None

    # Detect by magic bytes
    if data[:8] == _PNG_SIGNATURE:
        return _extract_from_png(data)

    if data[:2] == _JPEG_SOI:
        return _extract_from_jpeg(data)

    print(
        f"[extract_graphml] '{image_path}' is neither PNG nor JPEG.",
        file=sys.stderr,
    )
    return None


def extract_graphml_to_file(image_path: str, output_path: str | None = None) -> str | None:
    graphml = extract_graphml(image_path)
    if graphml is None:
        print(
            f"[extract_graphml] No embedded GraphML found in '{image_path}'.",
            file=sys.stderr,
        )
        return None

    if output_path is None:
        base, _ = os.path.splitext(image_path)
        # Handle double-extension names like "foo.graphml.png" -> "foo.graphml"
        if base.endswith(".graphml"):
            output_path = base
        else:
            output_path = base + ".graphml"

    try:
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(graphml)
        print(f"[extract_graphml] Extracted GraphML written to '{output_path}'.")
        return output_path
    except OSError as exc:
        print(
            f"[extract_graphml] Cannot write to '{output_path}': {exc}",
            file=sys.stderr,
        )
        return None


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_graphml.py <image.png|jpg> [output.graphml]")
        sys.exit(1)

    in_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) >= 3 else None

    result = extract_graphml_to_file(in_path, out_path)
    if result is None:
        sys.exit(1)