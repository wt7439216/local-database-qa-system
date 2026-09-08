"""Deterministic conversation-aware query routing (Phase E / v3.4).

Single routing pipeline:

    raw question + normalized history + scope context
        -> follow-up / pronoun / ellipsis resolution (deterministic)
        -> minimal semantic rewrite (never invents facts)
        -> rule-first intent classification
        -> RouteDecision

Hard invariants (Phase E contract):

- The router only interprets semantics.  It NEVER changes the effective
  QueryScope; scope resolution stays in query_scope/library_store.
- original_question is always preserved next to normalized_question.
- A referent is only substituted when the structured history or a clear
  textual antecedent pins it down; otherwise resolution is "ambiguous" and
  the original question is kept untouched.
- v3.4 is fully deterministic: no LLM is consulted, so every decision is
  reproducible and fast (microseconds).
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from core.text_rules import (
    extract_terms,
    is_book_overview_query,
    is_book_toc_query,
    normalize_query,
    route_by_rules,
)

HISTORY_MAX_TURNS = 3

LOCATION_WORDS = ("哪页", "第几页", "哪里", "在哪里", "位置", "出处", "来源", "在哪", "找一下", "找到", "找找", "什么地方", "哪些地方")
CHAPTER_LOCATION_WORDS = ("在哪一章", "在哪个章节", "在哪章", "哪一章", "哪个章节", "哪章", "第几章", "哪几章")
COMPARE_WORDS = ("区别", "比较", "对比", "异同", "相比")
CHAPTER_OVERVIEW_WORDS = ("讲什么", "讲了什么", "介绍", "概括", "总结", "主要内容", "内容", "概要", "概览")

FOLLOW_UP_PREFIXES = (
    "那", "那么", "还有", "另外", "以及", "其次", "此外", "其中", "其他", "其它",
    "继续", "接着", "再说", "展开", "详细", "换句话说", "它的", "它们",
    "该", "此", "上述", "上面", "前面", "刚才",
    "介绍", "说明", "概括", "总结", "讲讲", "说说", "看看", "分析", "比较",
    "和前面", "跟前面", "与前面", "和之前", "跟之前", "与之前", "和刚才", "跟刚才",
)
# 追问中指向上一轮对象的结构标记（"其它/其他/其中/此外"不是代词指代）。
PRONOUN_WORDS = ("它", "它们", "这个", "那个", "其", "前者", "后者")
PRONOUN_COMPOUNDS = ("其它", "其他", "其中", "此外")
ORDINAL_UNITS = ("个", "层", "种", "条", "篇", "类", "节", "点")
# 追问中"只差一个主语"的方面词：remainder 完全由这些词+胶水词构成时才允许代入 referent。
ASPECT_WORDS = (
    "优缺点", "优点", "缺点", "优势", "劣势", "特点", "特性", "特征", "区别",
    "作用", "意义", "定义", "原理", "内容", "方法", "技术", "方案", "流程",
    "步骤", "分类", "组成", "结构", "应用", "场景", "原因", "影响", "带宽",
    "速率", "参数", "机制", "规则", "公式", "标准", "接口", "频段", "容量",
    "编码", "调制", "多址", "复用", "信道", "概念", "目标", "目的", "功能",
    "性能", "指标", "计算", "过程", "方式", "条件", "前提", "关系", "异同",
    "不足",
)
GLUE_WORDS = ("的", "有", "什么", "哪些", "是", "呢", "吗", "啊", "呀", "了", "一下", "说说", "讲讲", "说说看", "主要", "分别", "之间", "相互", "两者", "二者", "说", "说的", "说到", "讲到", "讲的", "提到", "提到的", "讲")
# "技术有什么缺点" -> "技术缺点"：载体名词 + 方面词才允许分解；
# "调制方式" 这类自含复合术语不得被拆成"调制+方式"。
CARRIER_NOUNS = ("技术", "内容", "方案", "方法", "概念", "问题", "方面", "部分", "知识", "东西")
# referent 提取时剥离的疑问/连接脚手架（用于"衰落是怎么产生的" -> "衰落"）。
REFERENT_SCAFFOLD = (
    "这本书", "这本教材", "本教材", "本书", "该教材", "该书",
    "为什么", "为何", "原因", "是什么", "是谁", "怎么", "怎样", "如何",
    "哪些", "哪个", "什么", "多少", "是否", "请问", "请", "介绍", "说明",
    "分析", "概括", "总结", "主要", "大概", "一下", "意义", "作用", "里面",
    "书中", "全书", "这个", "那个", "有关", "关于", "以及", "位置", "来源",
    "出处", "哪里", "哪一页", "哪页", "第几页", "页码", "找到", "信息",
    "和", "与", "在", "中", "里", "的", "了", "吗", "呢", "是", "叫",
    "有什么", "有哪些", "什么叫", "什么是", "咋回事", "产生", "引起", "导致",
    "区别", "不同", "分别是", "各自", "它们", "它",
)
REFERENT_TAILS = (
    "是什么", "有哪些", "怎么样", "如何", "为什么", "产生", "引起", "导致",
    "定义", "含义", "概念", "介绍", "概述", "总结", "概括", "原理", "特点",
    "特性", "特征", "优点", "缺点", "优势", "劣势", "区别", "作用", "意义",
    "分类", "流程", "过程", "结构", "组成", "模型", "技术", "方式", "方法",
    "应用", "场景", "问题", "内容", "机制", "规则", "公式", "参数", "标准",
    "接口", "频段", "速率", "容量", "编码", "调制", "解调", "多址", "复用",
    "信道", "性能", "指标", "目标", "功能", "条件", "前提", "关系", "计算",
)
LATIN_UNITS = {"db", "dbm", "dbi", "hz", "khz", "mhz", "ghz", "bit", "bits", "byte", "bytes", "kbps", "mbps", "gbps"}
# 单字噪声词：referent 提取时丢弃，但"帧""码"等真实术语单字保留。
_SINGLE_JUNK = set("讲说看问解请再与和及跟比最都就很它这那的了吗呢")

GREETINGS = {"你好", "您好", "哈喽", "嗨", "hello", "hi", "在吗", "谢谢", "感谢", "多谢", "再见", "拜拜", "bye", "goodbye"}

KNOWN_ROUTES = ("qa", "compare", "locate", "locate_chapter", "book_toc", "book_overview", "chapter_overview", "unsupported")

ROUTE_REASON = {
    "book_toc": "BOOK_TOC_PATTERN",
    "book_overview": "BOOK_OVERVIEW_PATTERN",
    "chapter_overview": "CHAPTER_REFERENCE",
    "locate_chapter": "LOCATE_CHAPTER_PATTERN",
    "locate": "LOCATE_PATTERN",
    "compare": "COMPARE_PATTERN",
    "qa": "DEFAULT_QA",
    "unsupported": "UNSUPPORTED_INPUT",
}


def normalize_history(history: list[Any] | None) -> list[dict[str, str]]:
    """Keep the last few valid turns; tolerate garbage items from clients."""
    if not history:
        return []
    turns: list[dict[str, str]] = []
    for item in history:
        if not isinstance(item, dict):
            continue
        question = item.get("question")
        answer = item.get("answer")
        if not isinstance(question, str) or not question.strip():
            continue
        turns.append(
            {
                "question": question.strip()[:2000],
                "answer": answer.strip()[:6000] if isinstance(answer, str) else "",
            }
        )
    return turns[-HISTORY_MAX_TURNS:]


@dataclass(frozen=True)
class HistoryTurn:
    """One conversation turn with optional structured metadata.

    The structured fields are additive: clients that only send
    ``{question, answer}`` still work, the resolver falls back to textual
    extraction.  Fields arrive from the engine's own ``history_entry`` of
    the previous turn, so referents for chained follow-ups survive.
    """

    question: str
    answer: str = ""
    route: str = ""
    chapter: int | None = None
    document_ids: tuple[str, ...] = ()
    compare_entities: tuple[str, ...] = ()
    referent: str = ""

    @classmethod
    def from_entry(cls, entry: Any) -> "HistoryTurn | None":
        if not isinstance(entry, dict):
            return None
        question = entry.get("question")
        answer = entry.get("answer")
        if not isinstance(question, str) or not question.strip():
            return None
        question = question.strip()[:2000]
        answer = answer.strip()[:6000] if isinstance(answer, str) else ""
        route = entry.get("route")
        if not isinstance(route, str) or route not in KNOWN_ROUTES:
            route = ""
        chapter = entry.get("chapter")
        if isinstance(chapter, bool) or not isinstance(chapter, int) or not 1 <= chapter <= 999:
            chapter = None
        document_ids = tuple(str(value)[:200] for value in entry.get("document_ids") or () if isinstance(value, str))[:50]
        compare_entities = tuple(str(value)[:200] for value in entry.get("compare_entities") or () if isinstance(value, str))[:20]
        referent = entry.get("referent")
        referent = referent.strip()[:200] if isinstance(referent, str) else ""
        return cls(question, answer, route, chapter, document_ids, compare_entities, referent)

    @property
    def effective_route(self) -> str:
        return self.route or classify_route(self.question)


@dataclass(frozen=True)
class Resolution:
    status: str  # none | resolved | ambiguous | topic_shift
    referent: str
    rewritten: str  # "" means keep the original question
    reason: str


@dataclass(frozen=True)
class RouteDecision:
    route: str
    confidence: str
    reason_code: str
    original_question: str
    normalized_question: str
    resolution_status: str
    referent: str
    follow_up: bool
    scope_conflict: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "route": self.route,
            "confidence": self.confidence,
            "reason_code": self.reason_code,
            "original_question": self.original_question,
            "normalized_question": self.normalized_question,
            "resolution_status": self.resolution_status,
            "referent": self.referent,
            "follow_up": self.follow_up,
            "scope_conflict": self.scope_conflict,
        }


def looks_like_follow_up(question: str) -> bool:
    """Heuristic for fragments that only make sense with the previous turn."""
    value = normalize_query(question)
    if not value:
        return False
    if any(value.startswith(prefix) for prefix in FOLLOW_UP_PREFIXES):
        return True
    if re.fullmatch(r"第[0-9一二三四五六七八九十]{1,3}章[呢吗]*", value):
        return True
    if re.search(r"第[0-9一二三四五六七八九十]+[层类个种条篇部]", value):
        # 裸序数指代（"第二层""第三个"）指向上一轮回答里的列举内容。
        return True
    compact = value
    for compound in PRONOUN_COMPOUNDS:
        compact = compact.replace(compound, "")
    if any(word in compact for word in PRONOUN_WORDS) and len(value) <= 14:
        return True
    if len(value) <= 8 and value.endswith(("呢", "吗")):
        return True
    return False


def classify_route(question: str) -> str:
    normalized = normalize_query(question)
    if is_book_toc_query(normalized) or "有哪些章节" in normalized:
        return "book_toc"
    if any(word in normalized for word in COMPARE_WORDS):
        # Compare must outrank chapter/book overview: "第一章和第二章内容有
        # 什么区别" contains both a chapter number and the overview word
        # "内容", but it is a comparison question.
        return "compare"
    if extract_chapter_number(normalized) is not None and any(word in normalized for word in CHAPTER_OVERVIEW_WORDS):
        return "chapter_overview"
    if is_book_overview_query(normalized):
        return "book_overview"
    if any(word in normalized for word in CHAPTER_LOCATION_WORDS):
        return "locate_chapter"
    if any(word in normalized for word in LOCATION_WORDS):
        return "locate"
    legacy = route_by_rules(normalized)
    return "book_overview" if legacy == "summary" else "qa"


def extract_chapter_number(question: str) -> int | None:
    # A follow-up merges the previous question in front of this one, so the
    # latest chapter number is the one the user is asking about now.
    numbers = [int(value) for value in re.findall(r"第\s*(\d{1,3})\s*章", question)]
    if numbers:
        return numbers[-1]
    numerals = re.findall(r"第\s*([一二三四五六七八九十]{1,3})\s*章", question)
    return chinese_numeral_to_int(numerals[-1]) if numerals else None


def chinese_numeral_to_int(text: str) -> int | None:
    """Parse chapter numerals like 十、十一、二十一、三十 (up to 99)."""
    digits = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
    if text == "十":
        return 10
    if "十" in text:
        left, _, right = text.partition("十")
        if (left and left not in digits) or (right and right not in digits):
            return None
        return (digits.get(left, 1) if left else 1) * 10 + (digits.get(right, 0) if right else 0)
    return digits.get(text)


def split_compare_entities(question: str) -> list[str]:
    """Extract the compared sides from a question like "GSM 和 WCDMA 有什么区别？"."""
    value = question
    for phrase in ("有什么区别", "有何区别", "有什么异同", "区别是什么", "区别", "异同", "比较", "对比", "相比"):
        value = value.replace(phrase, " ")
    entities: list[str] = []
    for part in re.split(r"[和与及跟、]", value):
        part = part.strip(" ？?。！!，,、的是哪有什怎么怎样如何请")
        if part and part not in entities:
            entities.append(part)
    return entities


def latin_tokens(text: str) -> list[str]:
    tokens: list[str] = []
    for token in re.findall(r"[A-Za-z][A-Za-z0-9./+-]{1,}", text):
        value = re.sub(r"[^A-Za-z0-9]", "", token).lower()
        if len(value) >= 2 and value not in LATIN_UNITS:
            tokens.append(value.upper())
    return tokens


def salient_topic(turn: HistoryTurn) -> str:
    """Best deterministic referent for a turn: structured fields first."""
    if turn.referent:
        return turn.referent
    if turn.compare_entities:
        return turn.compare_entities[0]
    value = normalize_query(turn.question)
    for token in latin_tokens(value):
        return token
    for phrase in sorted(REFERENT_SCAFFOLD, key=len, reverse=True):
        value = value.replace(phrase, " ")
    parts = [part for part in re.split(r"\s+", value.strip()) if part and part not in GREETINGS]
    cleaned: list[str] = []
    for part in parts:
        for tail in sorted(REFERENT_TAILS, key=len, reverse=True):
            if part.endswith(tail) and len(part) > len(tail):
                part = part[: -len(tail)]
                break
        if part and not (len(part) == 1 and part in _SINGLE_JUNK):
            cleaned.append(part)
    return max(cleaned, key=len) if cleaned else ""


def _strip_followup_markers(value: str) -> str:
    value = re.sub(r"^(那|那么|还有|另外|此外|其中|其他|其它|然后|接着|继续|再|该|此|上述|上面|前面|刚才|以及|其次|而且|然后呢|接着呢|继续呢|展开|详细|换句话说)+", "", value)
    value = value.rstrip("呢吗啊呀")
    return value.strip()


def _attach_referent(referent: str, remainder: str) -> str:
    """Join a resolved referent with the rest of the fragment.

    "的" is a possessive connector and must survive ("后者的带宽是多少" ->
    "CDMA的带宽是多少"), other openings join directly.
    """
    remainder = remainder.strip("呢吗啊呀")
    if not remainder:
        return referent
    if remainder.startswith(("有", "是", "的", "和", "与", "在", "为", "跟", "怎么", "如何")):
        return f"{referent}{remainder}"
    return f"{referent}的{remainder}"


def _aspect_of(remainder: str) -> str:
    """The single aspect word a fragment asks about, or "" when the fragment
    carries its own content (which would make referent substitution wrong)."""
    value = remainder
    for glue in sorted(GLUE_WORDS, key=len, reverse=True):
        value = value.replace(glue, "")
    if not value:
        return ""
    if value in ASPECT_WORDS:
        return value
    # "技术有什么缺点" -> glue strip leaves "技术缺点": a carrier noun
    # followed by an aspect word; "调制方式" has no carrier and stays
    # self-contained.
    for carrier in sorted(CARRIER_NOUNS, key=len, reverse=True):
        if value.startswith(carrier) and value[len(carrier):] in ASPECT_WORDS:
            return value[len(carrier):]
    return ""


def _ordinal_reference(value: str) -> tuple[int, str] | None:
    match = re.search(r"第([0-9一二三四五六七八九十]{1,3})([层类个种条篇节点])", value)
    if not match:
        return None
    number = match.group(1)
    parsed = int(number) if number.isdigit() else chinese_numeral_to_int(number)
    if parsed is None or not 1 <= parsed <= 200:
        return None
    return parsed, match.group(2)


def _ordinal_item(turn: HistoryTurn, ordinal: int) -> str:
    """Look up the ordinal target in the previous answer's list-like text."""
    answer = re.sub(r"\[\d+\]", "", turn.answer)
    numbered: dict[int, str] = {}
    for position, line in enumerate(re.split(r"[\n；;。]", answer), 1):
        match = re.match(r"\s*(\d+)\s*[.、）)]\s*(.+)$", line.strip())
        if match:
            numbered[int(match.group(1))] = match.group(2).strip()
        numbered.setdefault(position, line.strip())
    phrases: dict[int, str] = {}
    for match in re.finditer(r"第([0-9一二三四五六七八九十]{1,3})([层类个种条篇节点])\s*([^，。；;,\n]{1,40})?", answer):
        number = match.group(1)
        parsed = int(number) if number.isdigit() else chinese_numeral_to_int(number)
        if parsed is not None:
            phrases[parsed] = (match.group(3) or "").strip()
    item = phrases.get(ordinal) or numbered.get(ordinal)
    if item is None:
        return ""
    item = item.strip(" :：-—")
    item = re.split(r"[（(]", item)[0].strip()
    if 2 <= len(item) <= 80:
        return item
    return ""


def _chapter_from_item(item: str) -> int | None:
    match = re.search(r"第\s*([0-9一二三四五六七八九十]{1,3})\s*章", item)
    if not match:
        return None
    return chinese_numeral_to_int(match.group(1)) if not match.group(1).isdigit() else int(match.group(1))


def _previous_chapter(turn: HistoryTurn) -> int | None:
    if turn.chapter is not None:
        return turn.chapter
    if turn.effective_route == "chapter_overview":
        return extract_chapter_number(turn.question)
    return None


def is_unsupported(question: str) -> bool:
    value = normalize_query(question)
    if value in GREETINGS:
        return True
    if len(value) <= 2 and not extract_terms(value):
        return True
    return False


def detect_scope_conflict(
    question: str,
    document_titles: dict[str, str] | None,
    allowed_document_ids: set[str] | frozenset[str] | None,
) -> bool:
    """A known document title appears in the question but is outside scope.

    ``allowed_document_ids is None`` means the default scope still covers
    every document — nothing can conflict.  The router only REPORTS the
    conflict; it never widens the scope.
    """
    if not document_titles or allowed_document_ids is None:
        return False
    value = normalize_query(question)
    # 最长标题匹配优先：短标题常是长标题的子串（"移动通信" vs
    # "移动通信测试文档"），只有用户实际指到的那个标题才算数。
    best_title = ""
    best_document_id = ""
    for document_id, title in document_titles.items():
        normalized_title = normalize_query(title)
        if len(normalized_title) >= 2 and normalized_title in value and len(normalized_title) > len(best_title):
            best_title, best_document_id = normalized_title, document_id
    return bool(best_title) and best_document_id not in allowed_document_ids


class QueryRouter:
    """Deterministic rule-first router: no LLM, no side effects."""

    def route(
        self,
        question: str,
        history: list[Any] | None = None,
        document_titles: dict[str, str] | None = None,
        allowed_document_ids: set[str] | frozenset[str] | None = None,
    ) -> RouteDecision:
        question = str(question or "").strip()
        turns: list[HistoryTurn] = []
        for entry in (history or [])[-HISTORY_MAX_TURNS:]:
            turn = HistoryTurn.from_entry(entry)
            if turn is not None:
                turns.append(turn)
        follow_up = bool(turns) and looks_like_follow_up(question)
        resolution = self._resolve_followup(question, turns) if follow_up else Resolution("none", "", "", "DIRECT")

        normalized = resolution.rewritten or question
        if resolution.status == "ambiguous":
            route, confidence, reason_code = "qa", "low", "AMBIGUOUS_FOLLOWUP"
        elif is_unsupported(question):
            route, confidence, reason_code = "unsupported", "high", "UNSUPPORTED_INPUT"
        else:
            route = classify_route(normalized)
            reason_code = ROUTE_REASON.get(route, "DEFAULT_QA")
            if resolution.status == "resolved":
                reason_code = f"{reason_code}+{resolution.reason}"
                confidence = "medium"
            else:
                confidence = "high" if route in {"book_toc", "book_overview", "chapter_overview", "locate", "locate_chapter", "compare", "unsupported"} else "medium"
        return RouteDecision(
            route=route,
            confidence=confidence,
            reason_code=reason_code,
            original_question=question,
            normalized_question=normalized,
            resolution_status=resolution.status,
            referent=resolution.referent,
            follow_up=follow_up,
            scope_conflict=detect_scope_conflict(question, document_titles, allowed_document_ids),
        )

    def _resolve_followup(self, question: str, turns: list[HistoryTurn]) -> Resolution:
        prev = turns[-1]
        value = normalize_query(question)

        # (1) 裸章节追问："那第二章呢" -> "第二章主要讲了什么"
        chapter = extract_chapter_number(question)
        if chapter is not None:
            remainder = _strip_followup_markers(value)
            remainder = re.sub(r"第[0-9一二三四五六七八九十]+章", "", remainder)
            remainder = remainder.strip("呢吗啊呀")
            if not remainder:
                return Resolution("resolved", f"第{chapter}章", f"第{chapter}章主要讲了什么", "FOLLOWUP_CHAPTER")
            return Resolution("topic_shift", "", "", "SELF_CONTAINED_CHAPTER")

        # (2) "和前面的相比呢"：与更早一轮的话题对比
        if value.startswith(("和前面", "跟前面", "与前面", "和之前", "跟之前", "与之前", "和刚才", "跟刚才")):
            current = salient_topic(prev)
            earlier = salient_topic(turns[-2]) if len(turns) >= 2 else ""
            if current and earlier:
                return Resolution("resolved", f"{current}与{earlier}", f"{current}和{earlier}相比有什么区别", "FOLLOWUP_COMPARE_PREV")
            return Resolution("ambiguous", "", "", "NO_EARLIER_TOPIC")

        # (3) 前者 / 后者
        if "前者" in value or "后者" in value:
            entities = self._compare_entities_of(prev)
            if len(entities) >= 2:
                referent = entities[0] if "前者" in value else entities[1]
                remainder = value.replace("前者", "").replace("后者", "")
                return Resolution("resolved", referent, _attach_referent(referent, remainder), "FOLLOWUP_FORMER_LATTER")
            return Resolution("ambiguous", "", "", "NO_COMPARE_ENTITIES")

        # (4) "它们有什么区别"
        if "它们" in value:
            entities = self._compare_entities_of(prev)
            if len(entities) >= 2 and ("区别" in value or "异同" in value or "比较" in value or "对比" in value):
                return Resolution("resolved", f"{entities[0]}与{entities[1]}", f"{entities[0]}和{entities[1]}有什么区别", "FOLLOWUP_COMPARE_ENTITIES")
            return Resolution("ambiguous", "", "", "NO_COMPARE_ENTITIES")

        # (5) 序数指代："第二个""第三层"
        ordinal = _ordinal_reference(value)
        if ordinal is not None:
            number, unit = ordinal
            item = _ordinal_item(prev, number)
            if item:
                item_chapter = _chapter_from_item(item)
                if item_chapter is not None:
                    return Resolution("resolved", f"第{item_chapter}章", f"第{item_chapter}章主要讲了什么", "FOLLOWUP_ORDINAL")
                remainder = _strip_followup_markers(value)
                remainder = re.sub(r"第[0-9一二三四五六七八九十]+[层类个种条篇节点]", "", remainder)
                return Resolution("resolved", item, _attach_referent(item, remainder), "FOLLOWUP_ORDINAL")
            if unit == "个":
                # "第二个呢" 且上一轮没有可对应的列表项：不猜。
                return Resolution("ambiguous", "", "", "NO_ORDINAL_ITEM")
            # 冻结兼容：内容型序数（"第二层"）无法定位时沿用既有合并行为。
            return Resolution("resolved", salient_topic(prev), f"{prev.question}{question}", "FOLLOWUP_ORDINAL_MERGE")

        # (6) 代词："它有什么优点" / "那它呢" / "这个呢"
        compact = value
        for compound in PRONOUN_COMPOUNDS:
            compact = compact.replace(compound, "")
        pronoun = next((word for word in PRONOUN_WORDS if word in compact), None)
        if pronoun is not None:
            if prev.effective_route == "compare":
                # 对比话题里的"它"没有唯一所指。
                return Resolution("ambiguous", "", "", "PRONOUN_AFTER_COMPARE")
            if prev.effective_route in {"book_toc", "book_overview"}:
                referent = "本书"
            else:
                referent = salient_topic(prev)
            remainder = _strip_followup_markers(compact.replace(pronoun, ""))
            if not remainder:
                chapter = _previous_chapter(prev)
                if chapter is not None:
                    return Resolution("resolved", f"第{chapter}章", f"第{chapter}章主要讲了什么", "FOLLOWUP_PRONOUN_BARE")
                if prev.effective_route in {"book_toc", "book_overview"}:
                    return Resolution("resolved", "本书", "本书主要讲了什么", "FOLLOWUP_PRONOUN_BARE")
                if not referent:
                    return Resolution("ambiguous", "", "", "NO_REFERENT")
                return Resolution("resolved", referent, referent, "FOLLOWUP_PRONOUN_BARE")
            if not referent:
                return Resolution("ambiguous", "", "", "NO_REFERENT")
            rewritten = _attach_referent(referent, remainder)
            return Resolution("resolved", referent, rewritten, "FOLLOWUP_PRONOUN_CONTENT")

        # (7) 无主语的延续："然后呢""还有呢""继续"
        remainder = _strip_followup_markers(value)
        if not remainder:
            chapter = _previous_chapter(prev)
            if chapter is not None:
                return Resolution("resolved", f"第{chapter + 1}章", f"第{chapter + 1}章主要讲了什么", "FOLLOWUP_NEXT_CHAPTER")
            referent = salient_topic(prev)
            if referent:
                return Resolution("resolved", referent, referent, "FOLLOWUP_BARE_CONTINUATION")
            return Resolution("ambiguous", "", "", "NO_REFERENT")

        # (8) 只差主语的方面追问："那缺点呢" / "刚才说的技术有什么缺点"
        aspect = _aspect_of(remainder)
        if aspect:
            referent = salient_topic(prev)
            if not referent:
                return Resolution("ambiguous", "", "", "NO_REFERENT")
            return Resolution("resolved", referent, f"{referent}有什么{aspect}", "FOLLOWUP_ASPECT")

        # (9) 追问标记但自带内容（如"那TCP和UDP有什么区别"）：不继承旧话题。
        return Resolution("topic_shift", "", "", "SELF_CONTAINED")

    def _compare_entities_of(self, turn: HistoryTurn) -> list[str]:
        if turn.compare_entities:
            return list(turn.compare_entities)
        if turn.effective_route == "compare":
            return split_compare_entities(turn.question)
        return []


def build_history_entry(
    prepared: Any,
    answer: str,
    citations: list[dict[str, Any]],
) -> dict[str, Any]:
    """Additive per-turn metadata the client can round-trip into history.

    Old clients ignore this field entirely and keep sending plain
    {question, answer} history — the router then falls back to textual
    referent extraction.
    """
    decision = getattr(prepared, "decision", None)
    chapter = None
    if decision is not None and decision.route == "chapter_overview":
        chapter = extract_chapter_number(decision.normalized_question) or extract_chapter_number(decision.original_question)
    elif decision is not None and decision.route == "locate_chapter":
        primary = prepared.contexts[0].chapter if prepared.contexts else ""
        match = re.search(r"第([0-9一二三四五六七八九十]{1,3})章", primary or "")
        if match:
            chapter = chinese_numeral_to_int(match.group(1)) if not match.group(1).isdigit() else int(match.group(1))
    document_ids = sorted({str(citation.get("document_id")) for citation in citations if citation.get("document_id")})
    compare_entities = split_compare_entities(decision.normalized_question) if decision is not None and decision.route == "compare" else []
    return {
        "question": prepared.question,
        "answer": answer,
        "route": prepared.route,
        "chapter": chapter,
        "document_ids": document_ids,
        "compare_entities": compare_entities,
        "referent": decision.referent if decision is not None else "",
    }
