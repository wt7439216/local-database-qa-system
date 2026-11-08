"""Capture / verify the versioned prompt contract (P4).

The prompt is the single most sensitive generation input.  This tool freezes
its exact text and a deterministic rendered sample so any later change must be
an explicit, reviewable baseline update.

    python -X utf8 scripts/capture_prompt_contract.py --update   # write baseline
    python -X utf8 scripts/capture_prompt_contract.py            # verify
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import config  # noqa: E402
from core.domain.prompts import (  # noqa: E402
    PROMPT_VERSION,
    SYSTEM_PROMPT,
    TASK_HINTS,
    build_messages,
)

BASELINE = ROOT / "eval" / "prompt_contract_baseline.json"


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def snapshot() -> dict:
    contexts = [
        SimpleNamespace(location="第4章 · GSM 空中接口（PDF 第51页）",
                        text="Um 接口是移动台与基站之间的空中接口，采用 GMSK 调制。"),
        SimpleNamespace(location="第5章 · 多径传播（PDF 第78页）",
                        text="多径传播会造成衰落，接收端通常使用均衡技术补偿信道失真。"),
    ]
    history = [{"question": "什么是 Um 接口？", "answer": "它是空中接口[1]。"}]
    messages, sent = build_messages("Um 接口采用什么调制？", contexts, "qa", history)
    return {
        "prompt_version": PROMPT_VERSION,
        "system_prompt": SYSTEM_PROMPT,
        "system_prompt_sha256": _sha(SYSTEM_PROMPT),
        "task_hints": dict(TASK_HINTS),
        "prompt_budget": config.RETRIEVAL.prompt_budget(
            config.ANSWER_CONTEXT_WINDOW, config.ANSWER_NUM_PREDICT
        ),
        "sample_sent_materials": len(sent),
        "sample_messages": messages,
        "sample_messages_sha256": _sha(json.dumps(messages, ensure_ascii=False, sort_keys=True)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--update", action="store_true")
    parser.add_argument("--out", type=Path, default=BASELINE)
    args = parser.parse_args()
    current = snapshot()
    if args.update:
        args.out.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
        print(f"prompt contract baseline written: {args.out}")
        return 0
    if not args.out.is_file():
        print("prompt contract baseline missing; run with --update")
        return 1
    baseline = json.loads(args.out.read_text(encoding="utf-8"))
    differences = [key for key in current if baseline.get(key) != current[key]]
    print("prompt_contract_identical", not differences, "differences", differences)
    return 0 if not differences else 1


if __name__ == "__main__":
    raise SystemExit(main())
