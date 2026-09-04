import argparse
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import fitz


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core import config

DEFAULT_PDF_DIR = config.PDF_DIR
DEFAULT_RAW_DIR = config.RAW_DIR
DEFAULT_OUTPUT = config.BOOK_TEXT_PATH


@dataclass
class OcrLine:
    text: str
    score: float
    left: float
    top: float
    right: float
    bottom: float


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract text from PDFs under data/pdf and save as data/raw/book.txt."
    )
    parser.add_argument("--pdf-dir", type=Path, default=DEFAULT_PDF_DIR)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--ocr",
        choices=["auto", "always", "never"],
        default="auto",
        help="auto uses embedded text when available and OCR otherwise.",
    )
    parser.add_argument(
        "--zoom",
        type=float,
        default=2.5,
        help="OCR render scale. 2.5 is a good balance for scanned books.",
    )
    parser.add_argument("--min-text-chars", type=int, default=80)
    parser.add_argument("--min-ocr-score", type=float, default=0.45)
    parser.add_argument("--start-page", type=int, default=1)
    parser.add_argument("--end-page", type=int)
    parser.add_argument("--max-pages", type=int)
    parser.add_argument(
        "--no-rotate",
        action="store_true",
        help="Write output directly without shifting book.txt/book2.txt names.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only show the files and rotation plan.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    pdf_dir = args.pdf_dir.resolve()
    raw_dir = args.raw_dir.resolve()
    output = args.output.resolve()

    pdf_files = sorted(pdf_dir.glob("*.pdf"), key=lambda p: p.name.lower())
    if not pdf_files:
        raise SystemExit(f"No PDF files found in {pdf_dir}")

    print("PDF files:")
    for pdf in pdf_files:
        print(f"  - {pdf.name} ({pdf.stat().st_size / 1024 / 1024:.1f} MB)")

    rotate = not args.no_rotate and output == (raw_dir / "book.txt").resolve()
    if rotate:
        print("\nRotation plan:")
        for src, dst in build_rotation_plan(raw_dir):
            print(f"  {src.name} -> {dst.name}")
        print("  new extraction -> book.txt")
    else:
        print(f"\nOutput: {output}")
        print("Rotation disabled.")

    if args.dry_run:
        return

    raw_dir.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)

    temp_output = output.with_name(f".{output.name}.tmp")
    if temp_output.exists():
        temp_output.unlink()

    ocr_engine = None
    if args.ocr != "never":
        ocr_engine = load_ocr_engine()

    started = time.time()
    total_pages = 0
    ocr_pages = 0
    text_pages = 0
    empty_pages = 0

    try:
        with temp_output.open("w", encoding="utf-8", newline="\n") as out:
            write_header(out, pdf_files, args)

            for pdf_index, pdf_path in enumerate(pdf_files, 1):
                with fitz.open(pdf_path) as doc:
                    page_numbers = select_pages(
                        doc.page_count,
                        start_page=args.start_page,
                        end_page=args.end_page,
                        max_pages=args.max_pages,
                    )
                    out.write(f"\n\n# PDF {pdf_index}: {pdf_path.name}\n")
                    out.write(f"# Total pages: {doc.page_count}\n\n")

                    for seq, page_no in enumerate(page_numbers, 1):
                        page = doc.load_page(page_no - 1)
                        total_pages += 1

                        text, method = extract_page_text(page, args, ocr_engine)
                        text = normalize_text(text)

                        if method == "ocr":
                            ocr_pages += 1
                        elif method == "text":
                            text_pages += 1
                        else:
                            empty_pages += 1

                        out.write(f"\n[page_{page_no:04d} method={method}]\n")
                        if text:
                            out.write(text)
                            out.write("\n")
                        else:
                            out.write("[empty_page]\n")

                        if seq == 1 or seq % 10 == 0 or seq == len(page_numbers):
                            print(
                                f"{pdf_path.name}: page {page_no}/{doc.page_count} "
                                f"({seq}/{len(page_numbers)} selected), method={method}"
                            )

        if rotate:
            rotate_book_files(raw_dir)
        elif output.exists():
            output.unlink()

        temp_output.replace(output)
    except Exception:
        if temp_output.exists():
            print(f"Temporary output kept for inspection: {temp_output}")
        raise

    elapsed = time.time() - started
    print("\nDone.")
    print(f"Output: {output}")
    print(f"Pages processed: {total_pages}")
    print(f"Text-layer pages: {text_pages}")
    print(f"OCR pages: {ocr_pages}")
    print(f"Empty pages: {empty_pages}")
    print(f"Elapsed: {elapsed / 60:.1f} minutes")


def load_ocr_engine():
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError as exc:
        raise SystemExit(
            "OCR dependency is missing. Install it with:\n"
            "python -m pip install rapidocr-onnxruntime\n"
        ) from exc

    return RapidOCR()


def extract_page_text(page, args, ocr_engine):
    embedded = ""
    if args.ocr != "always":
        embedded = page.get_text("text", sort=True).strip()

    if args.ocr == "never":
        return embedded, "text" if embedded else "empty"

    if args.ocr == "auto" and len(embedded) >= args.min_text_chars:
        return embedded, "text"

    if ocr_engine is None:
        return embedded, "text" if embedded else "empty"

    lines = ocr_page(page, ocr_engine, zoom=args.zoom, min_score=args.min_ocr_score)
    text = format_ocr_lines(lines)
    if text:
        return text, "ocr"

    return embedded, "text" if embedded else "empty"


def ocr_page(page, ocr_engine, zoom, min_score):
    matrix = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=matrix, alpha=False)
    image_bytes = pix.tobytes("png")
    result, _ = ocr_engine(image_bytes)

    if not result:
        return []

    lines = []
    for box, text, score in result:
        text = clean_ocr_line(text)
        if not text or float(score) < min_score:
            continue

        xs = [point[0] for point in box]
        ys = [point[1] for point in box]
        lines.append(
            OcrLine(
                text=text,
                score=float(score),
                left=min(xs),
                top=min(ys),
                right=max(xs),
                bottom=max(ys),
            )
        )

    return sort_ocr_lines(lines)


def sort_ocr_lines(lines):
    if not lines:
        return []

    heights = sorted(max(1.0, line.bottom - line.top) for line in lines)
    median_height = heights[len(heights) // 2]
    row_tolerance = max(8.0, median_height * 0.6)

    rows = []
    for line in sorted(lines, key=lambda item: (item.top, item.left)):
        center = (line.top + line.bottom) / 2
        placed = False
        for row in rows:
            if abs(row["center"] - center) <= row_tolerance:
                row["items"].append(line)
                row["center"] = (row["center"] * (len(row["items"]) - 1) + center) / len(
                    row["items"]
                )
                placed = True
                break
        if not placed:
            rows.append({"center": center, "items": [line]})

    ordered = []
    for row in sorted(rows, key=lambda item: item["center"]):
        ordered.extend(sorted(row["items"], key=lambda item: item.left))

    return ordered


def format_ocr_lines(lines):
    if not lines:
        return ""

    heights = [max(1.0, line.bottom - line.top) for line in lines]
    median_height = sorted(heights)[len(heights) // 2]
    paragraph_gap = median_height * 1.8

    paragraphs = []
    current = ""
    previous = None

    for line in lines:
        if previous is not None and line.top - previous.bottom > paragraph_gap:
            if current:
                paragraphs.append(current)
                current = ""

        if not current:
            current = line.text
        elif should_join_without_space(current, line.text):
            current += line.text
        else:
            current += " " + line.text

        if ends_paragraph(line.text):
            paragraphs.append(current)
            current = ""

        previous = line

    if current:
        paragraphs.append(current)

    return "\n".join(paragraphs)


def should_join_without_space(left, right):
    if not left or not right:
        return True
    if right[0] in "，。；：、？！)]}）】":
        return True
    if left[-1] in "([{（【":
        return True
    return has_cjk(left[-1]) and has_cjk(right[0])


def ends_paragraph(text):
    if not text:
        return False
    if re.search(r"[。！？；:]$", text):
        return True
    if re.match(r"^(第[一二三四五六七八九十百千0-9]+[章节]|[0-9]+(\.[0-9]+)*\s+)", text):
        return True
    return False


def has_cjk(char):
    return "\u4e00" <= char <= "\u9fff"


def clean_ocr_line(text):
    text = str(text).replace("\u3000", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_text(text):
    text = text.replace("\ufeff", "")
    text = text.replace("\x00", "")
    text = text.replace("\u3000", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()


def select_pages(page_count, start_page=1, end_page=None, max_pages=None):
    start_page = max(1, start_page)
    end_page = page_count if end_page is None else min(page_count, end_page)
    if end_page < start_page:
        return []

    pages = list(range(start_page, end_page + 1))
    if max_pages is not None:
        pages = pages[: max(0, max_pages)]
    return pages


def write_header(out, pdf_files, args):
    out.write("# Extracted book text\n")
    out.write("# Generated by scripts/pdf_to_book_txt.py\n")
    out.write(f"# OCR mode: {args.ocr}\n")
    out.write(f"# OCR zoom: {args.zoom}\n")
    out.write("# Source PDFs:\n")
    for pdf in pdf_files:
        out.write(f"# - {pdf.name}\n")


def build_rotation_plan(raw_dir):
    files = []
    for path in raw_dir.glob("book*.txt"):
        index = book_index(path.name)
        if index is not None:
            files.append((index, path))

    plan = []
    for index, src in sorted(files, reverse=True):
        dst = raw_dir / f"book{index + 1}.txt"
        plan.append((src, dst))
    return plan


def rotate_book_files(raw_dir):
    for src, dst in build_rotation_plan(raw_dir):
        if dst.exists():
            dst.unlink()
        src.replace(dst)


def book_index(name):
    if name == "book.txt":
        return 1
    match = re.fullmatch(r"book(\d+)\.txt", name)
    if not match:
        return None
    index = int(match.group(1))
    return index if index >= 2 else None


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(130)
