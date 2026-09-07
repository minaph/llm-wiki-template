"""Regression tests for document completion checks. Run with unittest."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from validate import validate


TASK = """---
id: CHECK-ONE
type: verification
status: active
priority: P2
trigger: on-demand
required_capabilities: [code-read, test]
---

# Check
"""


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="llm-wiki-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "llm_wiki"
        for folder in ("tasks", "wiki", "runs", "scripts"):
            (self.root / folder).mkdir(parents=True)
        self.task = self.root / "tasks/check.md"
        self.task.write_text(TASK, encoding="utf-8")

    def check_errors(self, expected):
        errors, _ = validate(self.root)
        self.assertTrue(any(expected in error for error in errors), errors)

    def test_starter_and_templates(self):
        for folder in ("tasks", "wiki", "runs"):
            (self.root / folder / "_TEMPLATE.md").write_text(TASK, encoding="utf-8")
        errors, counts = validate(self.root)
        self.assertEqual(errors, [])
        self.assertEqual(counts, {"tasks": 1, "runs": 0, "ids": 1})

    def test_missing_and_empty_required_values_fail(self):
        for key in ("id", "type", "status", "priority", "trigger", "required_capabilities"):
            line = next(line for line in TASK.splitlines() if line.startswith(key + ":"))
            for replacement in (None, "", "null", "~", "''", '""', "[]", "{}"):
                with self.subTest(key=key, value=replacement):
                    new_line = "" if replacement is None else f"{key}: {replacement}"
                    self.task.write_text(TASK.replace(line, new_line), encoding="utf-8")
                    errors, _ = validate(self.root)
                    self.assertTrue(errors)

    def test_malformed_metadata_and_old_types_fail(self):
        for old, new in (
            ("trigger: on-demand", "trigger: # not filled"),
            ("priority: P2", "priority: P9"),
            ("type: verification", "type: standing"),
            ("type: verification", "type: conditional"),
            ("status: active", "status: active\nstatus: paused"),
            ("trigger: on-demand", "trigger: |\n  multiline"),
            ("[code-read, test]", "code-read"),
            ("[code-read, test]", "[code-read,]"),
        ):
            with self.subTest(value=new):
                self.task.write_text(TASK.replace(old, new), encoding="utf-8")
                self.assertTrue(validate(self.root)[0])

    def test_individual_status_and_work_type_are_allowed(self):
        self.task.write_text(TASK.replace("status: active", "status: awaiting-data").replace(
            "type: verification", "type: migration"), encoding="utf-8")
        self.assertEqual(validate(self.root)[0], [])

    def test_reserved_direct_request_task_id_fails(self):
        self.task.write_text(TASK.replace("id: CHECK-ONE", "id: direct-request"), encoding="utf-8")
        self.check_errors("reserved Task ID: direct-request")

    def test_duplicate_actual_ids_fail(self):
        (self.root / "wiki/duplicate.md").write_text("---\nid: CHECK-ONE\n---\n", encoding="utf-8")
        self.check_errors("duplicate id")

    def test_missing_wiki_and_project_sources_fail(self):
        for target in ("../wiki/missing.md", "../../missing.py"):
            with self.subTest(target=target):
                self.task.write_text(TASK + f"\n[Source]({target})\n", encoding="utf-8")
                self.check_errors("broken link")

    def test_existing_project_sources_and_link_syntax(self):
        (self.base / "source (v1).py").write_text("", encoding="utf-8")
        self.task.write_text(TASK + '''
[Source](<../../source (v1).py> "Title")
[Encoded](../../source%20(v1).py#L1)
[Reference][source]
[source][]
[source]
[source]: <../../source (v1).py>
[Web](https://example.invalid/page)
[Anchor](#heading)
''', encoding="utf-8")
        self.assertEqual(validate(self.root)[0], [])

    def test_broken_reference_links_fail(self):
        for link in ("[Source][missing]", "[source][]", "[source]\n\n[source]: ../../missing.py"):
            with self.subTest(link=link):
                self.task.write_text(TASK + link, encoding="utf-8")
                self.assertTrue(validate(self.root)[0])

    def test_code_formatted_link_label_is_checked(self):
        self.task.write_text(TASK + "[`source.py`](../../missing.py)", encoding="utf-8")
        self.check_errors("broken link")

    def test_examples_are_not_live_links_but_template_links_are(self):
        self.task.write_text(TASK + '''
`[Example](missing.md)`
```md
[Example](missing.md)
```
<!-- [Example](missing.md) -->
''', encoding="utf-8")
        self.assertEqual(validate(self.root)[0], [])
        (self.root / "wiki/_TEMPLATE.md").write_text("[Source](missing.md)", encoding="utf-8")
        self.check_errors("broken link")

    def test_run_metadata_and_task_reference(self):
        run = self.root / "runs/one.md"
        editorial = self.root / "tasks/editorial.md"
        editorial.write_text(
            TASK.replace("id: CHECK-ONE", "id: WIKI-EDITORIAL-QUALITY").replace(
                "type: verification", "type: editorial"),
            encoding="utf-8",
        )

        run.write_text("---\nrun_id: RUN-ONE\ntask: CHECK-ONE\nexecutor: local\n---\n", encoding="utf-8")
        self.assertEqual(validate(self.root)[0], [])

        run.write_text("---\nrun_id: RUN-ONE\ntask: direct-request\nexecutor: local\n---\n", encoding="utf-8")
        self.assertEqual(validate(self.root)[0], [])

        run.write_text(
            "---\nrun_id: RUN-ONE\ntask: direct-request, CHECK-ONE, WIKI-EDITORIAL-QUALITY\nexecutor: local\n---\n",
            encoding="utf-8",
        )
        self.assertEqual(validate(self.root)[0], [])

        run.write_text(
            "---\nrun_id: RUN-ONE\ntask: CHECK-ONE, CHECK-ONE, WIKI-EDITORIAL-QUALITY\nexecutor: local\n---\n",
            encoding="utf-8",
        )
        self.assertEqual(validate(self.root)[0], [])

        run.write_text(
            "---\nrun_id: RUN-ONE\ntask: CHECK-ONE, MISSING, WIKI-EDITORIAL-QUALITY\nexecutor: local\n---\n",
            encoding="utf-8",
        )
        self.check_errors("unknown task ID: MISSING")

        for malformed in ("CHECK-ONE,", "CHECK-ONE, , WIKI-EDITORIAL-QUALITY", ",CHECK-ONE"):
            with self.subTest(task=malformed):
                run.write_text(
                    f"---\nrun_id: RUN-ONE\ntask: {malformed}\nexecutor: local\n---\n",
                    encoding="utf-8",
                )
                self.check_errors("non-empty comma-separated Task IDs")

        run.write_text("---\nrun_id: RUN-ONE\ntask: CHECK-ONE\n---\n", encoding="utf-8")
        self.check_errors("required metadata missing: executor")

    def test_missing_required_directory_fails(self):
        (self.root / "runs").rmdir()
        self.check_errors("missing directory: runs")


if __name__ == "__main__":
    unittest.main()
