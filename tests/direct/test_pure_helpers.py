import unittest
import json
import hashlib

CHUNK_SIZE = 5000
MAX_DOC_CHARS = 40000

def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def _norm(text):
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [" ".join(ln.split()) for ln in t.split("\n")]
    out, blank = [], 0
    for ln in lines:
        if ln == "":
            blank += 1
            if blank > 1:
                continue
        else:
            blank = 0
        out.append(ln)
    return "\n".join(out).strip()

def _chunks(doc, size=CHUNK_SIZE):
    out, cur = [], ""
    for p in doc.split("\n\n"):
        while len(p) > size:
            if cur:
                out.append(cur)
                cur = ""
            out.append(p[:size])
            p = p[size:]
        if cur and len(cur) + len(p) + 2 > size:
            out.append(cur)
            cur = p
        else:
            cur = p if not cur else cur + "\n\n" + p
    if cur:
        out.append(cur)
    return out

def _flat(s):
    return " ".join(str(s).split()).lower()

def _grounded(quote, chunk):
    q = _flat(quote).strip("\"' .")
    return len(q) >= 12 and q in _flat(chunk)

def _parse(raw):
    if isinstance(raw, dict):
        return raw
    s = str(raw).strip()
    if s.startswith("```"):
        s = s.strip("`").strip()
        if s[:4].lower() == "json":
            s = s[4:]
    try:
        v = json.loads(s.strip())
        return v if isinstance(v, dict) else {}
    except Exception:
        return {}

def _clean_chunk(items, parsed, chunk):
    src = parsed.get("results", parsed) if isinstance(parsed, dict) else {}
    out = {}
    for it in items:
        r = src.get(it["id"]) if isinstance(src, dict) else None
        st, q = "UNCLEAR", ""
        if isinstance(r, dict):
            s = str(r.get("status", "")).upper()
            if s in ("PRESENT", "ABSENT", "UNCLEAR"):
                st = s
            q = str(r.get("quote", ""))[:200]
        g = (st == "PRESENT") and _grounded(q, chunk)
        out[it["id"]] = {"status": st, "quote": q if g else "", "grounded": g}
    return out

def _reduce(items, chunk_results, full):
    status, quotes = {}, {}
    for it in items:
        hit, unclear = "", False
        for cr in chunk_results:
            r = cr[it["id"]]
            if r["status"] == "PRESENT" and r["grounded"]:
                hit = hit or r["quote"]
            elif r["status"] == "UNCLEAR" or r["status"] == "PRESENT":
                unclear = True
        must = it["polarity"] == "MUST_HAVE"
        if hit:
            st = "SATISFIED" if must else "VIOLATED"
        elif unclear or not full:
            st = "UNRESOLVED"
        else:
            st = "MISSING" if must else "CLEAR"
        status[it["id"]], quotes[it["id"]] = st, hit
    bad = [i for i in items if i["severity"] == "BLOCKER"
           and status[i["id"]] in ("MISSING", "VIOLATED")]
    good = all(status[i["id"]] in ("SATISFIED", "CLEAR")
               for i in items if i["severity"] in ("BLOCKER", "MAJOR"))
    outcome = "FAIL" if bad else ("PASS" if (full and good) else "REVIEW")
    return outcome, status, quotes

def _same_decision(a, b):
    keys = ("outcome", "coverage_bp", "doc_sha256", "chunk_hashes", "status_by_item")
    return all(a.get(k) == b.get(k) for k in keys)

def _strip_tags(html_text):
    out = []
    in_tag = False
    for ch in html_text:
        if ch == "<":
            in_tag = True
        elif ch == ">":
            in_tag = False
        elif not in_tag:
            out.append(ch)
    return "".join(out)


class TestPureHelpers(unittest.TestCase):
    def test_chunking_deterministic_and_covers_all_text(self):
        paragraphs = ["Paragraph " + str(i) + " " + ("content " * 50) for i in range(20)]
        doc = "\n\n".join(paragraphs)
        chunks1 = _chunks(doc, size=500)
        chunks2 = _chunks(doc, size=500)
        self.assertEqual(chunks1, chunks2)
        # Verify text preservation
        recombined = " ".join(" ".join(c.split()) for c in chunks1)
        original_words = " ".join(doc.split())
        self.assertEqual(recombined, original_words)

    def test_hash_sensitivity_one_char_change(self):
        base = "This is a clean document body text."
        alt = "This is a clean document body text!"
        self.assertNotEqual(_sha(base), _sha(alt))

    def test_normalization_whitespace_crlf(self):
        raw = "Line 1   with spaces\r\n\r\n\r\n\r\nLine 2 \t more  spaces\r\n"
        norm = _norm(raw)
        self.assertEqual(norm, "Line 1 with spaces\n\nLine 2 more spaces")

    def test_strip_html_tags(self):
        raw = "<html><body><h1>Title</h1><p>Content &amp; clause.</p></body></html>"
        stripped = _strip_tags(raw)
        self.assertEqual(stripped, "TitleContent &amp; clause.")

    def test_grounded_verifies_substring_len_12(self):
        chunk = "All subscriptions auto-renew annually unless cancelled 30 days prior."
        self.assertTrue(_grounded("auto-renew annually unless", chunk))
        # Case and whitespace tolerance
        self.assertTrue(_grounded("AUTO-RENEW   annually", chunk))
        # Short quote < 12 characters must fail
        self.assertFalse(_grounded("auto-renew", chunk))
        # Hallucinated / invented quote must fail
        self.assertFalse(_grounded("users will receive full refunds anytime", chunk))

    def test_parse_json_markdown_and_raw(self):
        raw_json = '{"results": {"refund": {"status": "PRESENT", "quote": "full refund policy"}}}'
        self.assertEqual(_parse(raw_json)["results"]["refund"]["status"], "PRESENT")

        fenced_json = '```json\n{"results": {"refund": {"status": "PRESENT", "quote": "full refund policy"}}}\n```'
        self.assertEqual(_parse(fenced_json)["results"]["refund"]["status"], "PRESENT")

        malformed = 'Random LLM text that failed json generation'
        self.assertEqual(_parse(malformed), {})

    def test_clean_chunk_ungrounded_quote_downgraded(self):
        items = [
            {"id": "refund", "question": "Refund policy exists", "severity": "BLOCKER", "polarity": "MUST_HAVE"}
        ]
        chunk = "We do not offer any cash refunds under any circumstances."
        # LLM claimed present with hallucinated quote
        fake_parsed = {
            "results": {
                "refund": {"status": "PRESENT", "quote": "We offer 100% money back guarantee"}
            }
        }
        cleaned = _clean_chunk(items, fake_parsed, chunk)
        self.assertFalse(cleaned["refund"]["grounded"])
        self.assertEqual(cleaned["refund"]["quote"], "")

    def test_reduce_must_have_and_must_not_have(self):
        items = [
            {"id": "refund", "question": "Refund policy", "severity": "BLOCKER", "polarity": "MUST_HAVE"},
            {"id": "auto_renew", "question": "No auto renew", "severity": "BLOCKER", "polarity": "MUST_NOT_HAVE"}
        ]
        chunk = "All sales include 30 day refund policy. Accounts auto-renew automatically every month."
        chunk_results = [
            {
                "refund": {"status": "PRESENT", "quote": "30 day refund policy", "grounded": True},
                "auto_renew": {"status": "PRESENT", "quote": "auto-renew automatically", "grounded": True}
            }
        ]
        outcome, status, quotes = _reduce(items, chunk_results, full=True)
        # refund MUST_HAVE hit -> SATISFIED
        self.assertEqual(status["refund"], "SATISFIED")
        # auto_renew MUST_NOT_HAVE hit -> VIOLATED
        self.assertEqual(status["auto_renew"], "VIOLATED")
        # auto_renew is BLOCKER and VIOLATED -> outcome FAIL
        self.assertEqual(outcome, "FAIL")

    def test_reduce_pass_when_good_and_full(self):
        items = [
            {"id": "refund", "question": "Refund policy", "severity": "BLOCKER", "polarity": "MUST_HAVE"},
            {"id": "no_hidden_fees", "question": "No hidden fees", "severity": "MAJOR", "polarity": "MUST_NOT_HAVE"}
        ]
        chunk_results = [
            {
                "refund": {"status": "PRESENT", "quote": "full refund guarantee within 14 days", "grounded": True},
                "no_hidden_fees": {"status": "ABSENT", "quote": "", "grounded": False}
            }
        ]
        outcome, status, _ = _reduce(items, chunk_results, full=True)
        self.assertEqual(status["refund"], "SATISFIED")
        self.assertEqual(status["no_hidden_fees"], "CLEAR")
        self.assertEqual(outcome, "PASS")

    def test_reduce_not_full_caps_at_review(self):
        items = [
            {"id": "refund", "question": "Refund policy", "severity": "BLOCKER", "polarity": "MUST_HAVE"}
        ]
        chunk_results = [
            {
                "refund": {"status": "PRESENT", "quote": "full refund guarantee within 14 days", "grounded": True}
            }
        ]
        # full=False because max_chunks truncated document
        outcome, _, _ = _reduce(items, chunk_results, full=False)
        self.assertEqual(outcome, "REVIEW")

    def test_same_decision_logic(self):
        dec1 = {
            "outcome": "PASS",
            "coverage_bp": 10000,
            "doc_sha256": "abc123",
            "chunk_hashes": ["c1", "c2"],
            "status_by_item": {"item1": "SATISFIED"},
            "quotes": {"item1": "exact quote wording A"},
            "ungrounded_count": 0
        }
        dec2 = {
            "outcome": "PASS",
            "coverage_bp": 10000,
            "doc_sha256": "abc123",
            "chunk_hashes": ["c1", "c2"],
            "status_by_item": {"item1": "SATISFIED"},
            "quotes": {"item1": "slightly different quote wording B"},
            "ungrounded_count": 1
        }
        # Different quote wording or ungrounded_count MUST pass
        self.assertTrue(_same_decision(dec1, dec2))

        # Different outcome must fail
        dec3 = dict(dec1, outcome="FAIL")
        self.assertFalse(_same_decision(dec1, dec3))

        # Different doc hash must fail
        dec4 = dict(dec1, doc_sha256="xyz789")
        self.assertFalse(_same_decision(dec1, dec4))


if __name__ == "__main__":
    unittest.main()
