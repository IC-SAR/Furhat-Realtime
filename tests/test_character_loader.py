from __future__ import annotations

import contextlib
import json
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from Furhat.Character import loader as character_loader  # noqa: E402
from Furhat import settings_store  # noqa: E402


def _write_character(
    path: Path,
    *,
    char_id: str,
    with_links: bool = True,
    include_external_links: bool = True,
    external_links: list[str] | None = None,
) -> None:
    payload: dict[str, object] = {
        "id": char_id,
        "name": char_id,
        "openingLine": "Hello",
        "voiceId": "voice",
        "faceId": "face",
    }
    if include_external_links:
        links = external_links if external_links is not None else ["https://example.com/a.txt"]
        payload["externalLinks"] = [{"link": link} for link in links] if with_links else []
    path.write_text(json.dumps(payload), encoding="utf-8")


@contextlib.contextmanager
def _serve_test_http(
    responses: dict[str, tuple[int, dict[str, str], bytes]],
):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            status, headers, body = responses.get(
                self.path,
                (404, {"Content-Type": "text/plain; charset=utf-8"}, b"missing"),
            )
            self.send_response(status)
            for key, value in headers.items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()


class CharacterLoaderTests(unittest.TestCase):
    def test_convert_github_to_raw_preserves_blob_conversion(self) -> None:
        converted = character_loader._convert_github_to_raw(  # noqa: SLF001
            "https://github.com/example/repo/blob/main/docs/page.md"
        )
        self.assertEqual(
            converted,
            "https://raw.githubusercontent.com/example/repo/main/docs/page.md",
        )

    def test_list_character_files_only_returns_character_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_character(root / "valid.json", char_id="valid")
            _write_character(
                root / "nolinks.json",
                char_id="nolinks",
                include_external_links=False,
            )
            (root / "other.json").write_text('{"hello": "world"}', encoding="utf-8")

            files = character_loader.list_character_files(app_root=root)

            self.assertEqual([path.name for path in files], ["valid.json"])

    def test_resolve_startup_character_prefers_saved_character_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            saved = root / "saved.json"
            env_file = root / "env.json"
            preferred = root / "Pepper - Innovation Day.json"
            _write_character(saved, char_id="saved")
            _write_character(env_file, char_id="env")
            _write_character(preferred, char_id="preferred")

            resolved = character_loader.resolve_startup_character(
                settings_store.AppSettings(character_path=str(saved)),
                app_root=root,
                env={"FURHAT_CHARACTER_FILE": str(env_file)},
            )

            self.assertEqual(resolved, saved.resolve())

    def test_resolve_startup_character_uses_env_before_preferred(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            env_file = root / "env.json"
            preferred = root / "Pepper - Innovation Day.json"
            _write_character(env_file, char_id="env")
            _write_character(preferred, char_id="preferred")

            resolved = character_loader.resolve_startup_character(
                settings_store.AppSettings(),
                app_root=root,
                env={"FURHAT_CHARACTER_FILE": str(env_file)},
            )

            self.assertEqual(resolved, env_file.resolve())

    def test_resolve_startup_character_falls_back_to_preferred_then_first_character(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            preferred = root / "Pepper - Innovation Day.json"
            _write_character(preferred, char_id="preferred")
            _write_character(root / "zeta.json", char_id="zeta")

            resolved = character_loader.resolve_startup_character(
                settings_store.AppSettings(),
                app_root=root,
                env={},
            )
            self.assertEqual(resolved, preferred.resolve())

            preferred.unlink()
            resolved_without_preferred = character_loader.resolve_startup_character(
                settings_store.AppSettings(),
                app_root=root,
                env={},
            )
            self.assertEqual(resolved_without_preferred, (root / "zeta.json").resolve())

    def test_download_sources_cleans_html_chrome_and_preserves_plain_text(self) -> None:
        mojibake_dash = "\u00e2\u20ac\u201c"
        mojibake_spanish = "Espa\u00c3\u00b1ol"
        html_page = f"""
<!doctype html>
<html>
<head>
  <title>Innovation Center {mojibake_dash} St. Vrain Valley Schools</title>
  <style>.hidden {{ display:none; }}</style>
  <script>console.log('ignore me');</script>
</head>
<body>
  <div>View Alerts</div>
  <div>Dismiss</div>
  <div>English</div>
  <div>- {mojibake_spanish}</div>
  <div>- About</div>
  <div>- Programs</div>
  <div>- Schools</div>
  <div>- Departments</div>
  <div>- Quick Links</div>
  <main>
    <article>
      <h1>Innovation Center {mojibake_dash} St. Vrain Valley Schools</h1>
      <p>This is a static HTML page for the RAG pipeline.</p>
      <ul><li>First fact</li><li>Second fact</li></ul>
    </article>
  </main>
  <footer><p>Search for:</p></footer>
</body>
</html>
""".encode("utf-8")
        weak_html = b"""
<html>
<head><title>Weak Header Page</title></head>
<body><p>This page should still be treated as HTML.</p></body>
</html>
"""
        with _serve_test_http(
            {
                "/page.html": (200, {"Content-Type": "text/html; charset=utf-8"}, html_page),
                "/plain.txt": (
                    200,
                    {"Content-Type": "text/plain; charset=utf-8"},
                    b"Plain text source.\nSecond line.",
                ),
                "/weak": (200, {}, weak_html),
            }
        ) as base_url, tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir)
            notifications: list[str] = []

            character_loader._download_sources(  # noqa: SLF001
                [
                    f"{base_url}/page.html",
                    f"{base_url}/plain.txt",
                    f"{base_url}/weak",
                ],
                dest,
                notifications.append,
            )

            contents = [path.read_text(encoding="utf-8") for path in sorted(dest.glob("*.txt"))]

        self.assertEqual(len(contents), 3)
        html_content = next(text for text in contents if "Innovation Center" in text)
        self.assertIn("Innovation Center \u2013 St. Vrain Valley Schools", html_content)
        self.assertIn(f"{base_url}/page.html", html_content)
        self.assertIn("This is a static HTML page for the RAG pipeline.", html_content)
        self.assertIn("First fact", html_content)
        self.assertNotIn("console.log", html_content)
        self.assertNotIn("View Alerts", html_content)
        self.assertNotIn("Dismiss", html_content)
        self.assertNotIn("English", html_content)
        self.assertNotIn("Espa\u00f1ol", html_content)
        self.assertNotIn("- About", html_content)
        plain_content = next(text for text in contents if "Plain text source." in text)
        self.assertEqual(plain_content, "Plain text source.\nSecond line.")
        weak_content = next(text for text in contents if "Weak Header Page" in text)
        self.assertIn(f"{base_url}/weak", weak_content)
        self.assertEqual(notifications, [])

    def test_download_sources_skips_navigation_only_html(self) -> None:
        nav_heavy_html = b"""
<html>
<head><title>Navigation Heavy</title></head>
<body>
  <header><p>View Alerts</p></header>
  <div>- About</div>
  <div>- Programs</div>
  <div>- Schools</div>
  <div>- Departments</div>
  <div>- Quick Links</div>
  <div>English</div>
  <div>- Espa\xc3\xb1ol</div>
  <div>Dismiss</div>
</body>
</html>
"""
        with _serve_test_http(
            {
                "/nav-only.html": (200, {"Content-Type": "text/html; charset=utf-8"}, nav_heavy_html),
            }
        ) as base_url, tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir)
            notifications: list[str] = []

            character_loader._download_sources(  # noqa: SLF001
                [f"{base_url}/nav-only.html"],
                dest,
                notifications.append,
            )

            saved = list(dest.glob("*.txt"))

        self.assertEqual(saved, [])
        self.assertTrue(
            any("page contained only navigation or utility chrome" in message for message in notifications),
            notifications,
        )

    def test_download_sources_skips_binary_and_low_text_html(self) -> None:
        js_shell = b"""
<html>
<head><title>JS App</title><script>window.boot();</script></head>
<body><div id="app"></div></body>
</html>
"""
        with _serve_test_http(
            {
                "/binary.bin": (
                    200,
                    {"Content-Type": "application/octet-stream"},
                    b"\x00\x01\x02\x03binary",
                ),
                "/js-only.html": (200, {"Content-Type": "text/html"}, js_shell),
            }
        ) as base_url, tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir)
            notifications: list[str] = []

            character_loader._download_sources(  # noqa: SLF001
                [
                    f"{base_url}/binary.bin",
                    f"{base_url}/js-only.html",
                ],
                dest,
                notifications.append,
            )

            saved = list(dest.glob("*.txt"))

        self.assertEqual(saved, [])
        self.assertTrue(
            any("unsupported binary content" in message for message in notifications),
            notifications,
        )
        self.assertTrue(
            any("empty or JS-rendered HTML" in message for message in notifications),
            notifications,
        )

    def test_download_sources_uses_google_docs_export_when_available(self) -> None:
        doc_url = "https://docs.google.com/document/d/test-doc/edit?usp=sharing"
        export_url = "https://docs.google.com/document/d/test-doc/export?format=txt"
        notifications: list[str] = []

        def fake_fetch(url: str, timeout: int = character_loader.DEFAULT_TIMEOUT) -> character_loader.SourcePayload:
            self.assertEqual(url, export_url)
            return character_loader.SourcePayload(
                url=url,
                content_type="text/plain; charset=utf-8",
                charset="utf-8",
                raw=b"Stormy Specifics\n\nThe district serves many communities.",
            )

        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.object(
            character_loader,
            "_fetch_source",
            side_effect=fake_fetch,
        ):
            dest = Path(temp_dir)
            character_loader._download_sources([doc_url], dest, notifications.append)  # noqa: SLF001
            contents = [path.read_text(encoding="utf-8") for path in sorted(dest.glob("*.txt"))]

        self.assertEqual(len(contents), 1)
        self.assertTrue(contents[0].startswith("Stormy Specifics\n" + doc_url + "\n\n"))
        self.assertIn("The district serves many communities.", contents[0])
        self.assertEqual(notifications, [])

    def test_download_sources_skips_google_docs_when_export_is_unavailable(self) -> None:
        doc_url = "https://docs.google.com/document/d/test-doc/edit?usp=sharing"
        export_url = "https://docs.google.com/document/d/test-doc/export?format=txt"
        notifications: list[str] = []

        def fake_fetch(url: str, timeout: int = character_loader.DEFAULT_TIMEOUT) -> character_loader.SourcePayload:
            self.assertEqual(url, export_url)
            return character_loader.SourcePayload(
                url=url,
                content_type="text/html; charset=utf-8",
                charset="utf-8",
                raw=b"<html><body>Sign in to continue</body></html>",
            )

        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.object(
            character_loader,
            "_fetch_source",
            side_effect=fake_fetch,
        ):
            dest = Path(temp_dir)
            character_loader._download_sources([doc_url], dest, notifications.append)  # noqa: SLF001
            contents = list(dest.glob("*.txt"))

        self.assertEqual(contents, [])
        self.assertTrue(
            any("google docs export unavailable" in message for message in notifications),
            notifications,
        )

    def test_prepare_character_rag_builds_index_from_mixed_supported_sources(self) -> None:
        html_page = b"""
<html>
<head><title>Support Page</title></head>
<body>
  <section>
    <h1>Support Page</h1>
    <p>This HTML page contains enough readable text for chunking and retrieval.</p>
    <p>It should be preserved as cleaned text before embeddings are built.</p>
  </section>
</body>
</html>
"""
        with _serve_test_http(
            {
                "/page.html": (200, {"Content-Type": "text/html; charset=utf-8"}, html_page),
                "/plain.txt": (
                    200,
                    {"Content-Type": "text/plain; charset=utf-8"},
                    b"Supplemental plain text source for the character.",
                ),
                "/binary.bin": (
                    200,
                    {"Content-Type": "application/octet-stream"},
                    b"\x00\x01\x02",
                ),
            }
        ) as base_url, tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            character_path = root / "character.json"
            _write_character(
                character_path,
                char_id="html-character",
                external_links=[
                    f"{base_url}/page.html",
                    f"{base_url}/plain.txt",
                    f"{base_url}/binary.bin",
                ],
            )
            notifications: list[str] = []
            original_index_path = character_loader.retriever.INDEX_PATH

            def fake_embed_texts(texts: list[str], model: str) -> list[list[float]]:
                return [[float(index + 1), float(len(text))] for index, text in enumerate(texts)]

            try:
                with (
                    mock.patch.object(character_loader, "DEFAULT_CHAR_DIR", root / "characters"),
                    mock.patch.object(character_loader.builder, "embed_texts", side_effect=fake_embed_texts),
                ):
                    character_loader._prepare_character_rag_sync(  # noqa: SLF001
                        character_path,
                        notifications.append,
                        force=True,
                    )

                    status = character_loader.get_character_rag_status(character_path)
                    sources_dir = character_loader.get_character_sources_dir(character_path)
                    source_files = sorted(path.name for path in sources_dir.glob("*.txt"))
                    saved_texts = [
                        path.read_text(encoding="utf-8")
                        for path in sorted(sources_dir.glob("*.txt"))
                    ]
            finally:
                character_loader.retriever.set_index_path(original_index_path)
                character_loader.retriever.reload_index()

        self.assertEqual(status.state, "ready")
        self.assertGreater(status.entries, 0)
        self.assertEqual(len(source_files), 2)
        self.assertTrue(any("Support Page" in text for text in saved_texts))
        self.assertTrue(any("Supplemental plain text source" in text for text in saved_texts))
        self.assertTrue(
            any("unsupported binary content" in message for message in notifications),
            notifications,
        )
        self.assertTrue(
            any("RAG index ready" in message for message in notifications),
            notifications,
        )


if __name__ == "__main__":
    unittest.main()
