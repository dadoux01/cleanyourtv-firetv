"""firetv.py: language, list choice, output translation, download URLs and archive safety (no TV needed)."""
import io
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import firetv  # noqa: E402


class LanguageTest(unittest.TestCase):
    def test_forced_language_wins(self):
        self.assertEqual(firetv.detect_lang({"FIRETV_LANG": "en", "LANG": "fr_FR.UTF-8"}), "en")
        self.assertEqual(firetv.detect_lang({"FIRETV_LANG": "fr", "LANG": "en_US.UTF-8"}), "fr")

    def test_system_language(self):
        self.assertEqual(firetv.detect_lang({"LANG": "fr_FR.UTF-8"}), "fr")
        self.assertEqual(firetv.detect_lang({"LC_ALL": "de_DE.UTF-8", "LANG": "fr_FR"}), "en")

    def test_every_message_has_both_languages_and_same_placeholders(self):
        import re
        for key, (fr, en) in firetv.MESSAGES.items():
            self.assertTrue(fr and en, key)
            self.assertEqual(sorted(re.findall(r"{(\w+)}", fr)), sorted(re.findall(r"{(\w+)}", en)), key)


class ListsTest(unittest.TestCase):
    def test_model_codes_point_to_existing_lists(self):
        for code in firetv.LISTS:
            self.assertTrue(firetv.model_list(code).exists(), code)

    def test_unknown_model(self):
        self.assertIsNone(firetv.model_list("AFTXYZ"))

    def test_aliases_name_real_commands(self):
        for alias, command in firetv.ALIASES.items():
            self.assertIn(command, firetv.COMMANDS, alias)


class TranslationTest(unittest.TestCase):
    def test_french_translates_known_lines(self):
        out = firetv.translate_line("nothing drifted: 56 listed packages are still disabled and Home is com.amazon.tv.launcher/.X\n", "fr")
        self.assertTrue(out.startswith("aucun écart : les 56 paquets"))
        self.assertEqual(firetv.translate_line("drift: 1 of 57; re-apply the list with --fix, or run x", "fr"),
                         "écart : 1 sur 57 ; réappliquez la liste avec « corriger » (--fix)")

    def test_unknown_lines_and_english_are_unchanged(self):
        self.assertEqual(firetv.translate_line("package:com.amazon.firebat", "fr"), "package:com.amazon.firebat")
        self.assertEqual(firetv.translate_line("nothing drifted: 1 listed packages", "en"), "nothing drifted: 1 listed packages")


class ToolchainTest(unittest.TestCase):
    def test_download_urls_per_platform(self):
        for system, key in (("Windows", "win"), ("Darwin", "mac"), ("Linux", "linux")):
            with mock.patch("platform.system", return_value=system):
                url, k = firetv.cmdline_tools_url()
                self.assertEqual(k, key)
                self.assertIn("commandlinetools-%s-" % key, url)
                self.assertIn(firetv.CMDLINE_SHA256[key][:8], firetv.CMDLINE_SHA256[key])
                self.assertIn({"Windows": "windows", "Darwin": "mac", "Linux": "linux"}[system], firetv.jdk_url())

    def test_arch(self):
        with mock.patch("platform.machine", return_value="arm64"):
            self.assertEqual(firetv.host_arch(), "aarch64")
        with mock.patch("platform.machine", return_value="AMD64"):
            self.assertEqual(firetv.host_arch(), "x64")

    def test_archive_path_traversal_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.zip"
            with zipfile.ZipFile(bad, "w") as z:
                z.writestr("../escape.txt", "x")
            with self.assertRaises(RuntimeError):
                firetv.extract(bad, Path(tmp) / "out")
            self.assertFalse((Path(tmp) / "escape.txt").exists())

    def test_checksum_mismatch_deletes_the_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "a.bin"
            f.write_bytes(b"abc")
            with mock.patch("sys.stderr", new_callable=io.StringIO), self.assertRaises(SystemExit):
                firetv.verify(f, "0" * 64)
            self.assertFalse(f.exists())

    def test_checksum_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "a.bin"
            f.write_bytes(b"abc")
            firetv.verify(f, firetv.sha256_of(f))
            self.assertTrue(f.exists())


class CommandLineTest(unittest.TestCase):
    def test_missing_host_is_refused_before_anything_runs(self):
        with mock.patch.dict(os.environ, {"TV_HOST": ""}), mock.patch("sys.stderr", new_callable=io.StringIO):
            self.assertEqual(firetv.main(["probe"]), 1)

    def test_unknown_command(self):
        with mock.patch("sys.stderr", new_callable=io.StringIO):
            self.assertEqual(firetv.main(["nope"]), 2)

    def test_no_command_prints_help(self):
        with mock.patch("sys.stdout", new_callable=io.StringIO):
            self.assertEqual(firetv.main([]), 2)


if __name__ == "__main__":
    unittest.main()
