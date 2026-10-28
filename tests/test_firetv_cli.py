"""firetv.py: command line, paths, unreachable TV, translations, downloads and archives (no TV needed)."""
import io
import os
import re
import sys
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import firetv  # noqa: E402


def run_main(argv):
    """main(argv) with stdout and stderr captured; returns (status, stdout, stderr)."""
    out, errs = io.StringIO(), io.StringIO()
    with mock.patch("sys.stdout", out), mock.patch("sys.stderr", errs):
        status = firetv.main(argv)
    return status, out.getvalue(), errs.getvalue()


class NoTV:
    """Patches that make any attempt to reach a TV fail the test."""
    def __enter__(self):
        self.patches = [mock.patch.object(firetv, "ensure_venv", return_value=None),
                        mock.patch.object(firetv, "tv_shell", side_effect=AssertionError("the TV was contacted"))]
        for p in self.patches:
            p.start()
        return self

    def __exit__(self, *exc):
        for p in self.patches:
            p.stop()


class LanguageTest(unittest.TestCase):
    def test_forced_language_wins(self):
        self.assertEqual(firetv.detect_lang({"FIRETV_LANG": "en", "LANG": "fr_FR.UTF-8"}), "en")
        self.assertEqual(firetv.detect_lang({"FIRETV_LANG": "fr", "LANG": "en_US.UTF-8"}), "fr")

    def test_system_language(self):
        self.assertEqual(firetv.detect_lang({"LANG": "fr_FR.UTF-8"}), "fr")
        self.assertEqual(firetv.detect_lang({"LC_ALL": "de_DE.UTF-8", "LANG": "fr_FR"}), "en")
        self.assertEqual(firetv.detect_lang({}), "en")

    def test_every_message_has_both_languages_and_same_placeholders(self):
        for key, (fr, en) in firetv.MESSAGES.items():
            self.assertTrue(fr and en, key)
            self.assertEqual(sorted(re.findall(r"{(\w+)}", fr)), sorted(re.findall(r"{(\w+)}", en)), key)


class ListsTest(unittest.TestCase):
    def test_model_codes_point_to_existing_lists(self):
        for code in firetv.LISTS:
            self.assertTrue(firetv.model_list(code).exists(), code)

    def test_unknown_model(self):
        self.assertIsNone(firetv.model_list("AFTXYZ"))
        with self.assertRaises(firetv.Refused):
            firetv.chosen_list("AFTXYZ", None)

    def test_aliases_name_real_commands(self):
        for alias, command in firetv.ALIASES.items():
            self.assertIn(command, firetv.COMMANDS, alias)


class TranslationTest(unittest.TestCase):
    # Real lines printed by the upstream tools, and the start of their French rendering.
    CASES = {
        "nothing drifted: 56 listed packages are still disabled and Home is com.amazon.tv.launcher/.X":
            "aucun écart : les 56 paquets",
        "drift: 1 of 57; re-apply the list with --fix, or run tools/disable.sh and the install script by hand":
            "écart : 1 sur 57 ; réappliquez la liste avec « corriger » (fix), ou lancez tools/disable.sh",
        "  back on (2): com.a, com.b": "  réactivés (2) : com.a, com.b",
        "  not installed any more (1): com.a": "  plus installés (1) : com.a",
        "still enabled after --fix: com.a (the firmware may pin them; re-run the list by hand after the next reboot)":
            "toujours activés après la correction : com.a",
        "192.168.1.50:5555 is closed: the TV refused the connection.": "192.168.1.50:5555 est fermé",
        "192.168.1.50:5555 is still open: network ADB is on. On the TV, turn USB debugging,": "192.168.1.50:5555 est toujours ouvert",
        "restoring the state recorded on 2026-10-28T15:00:00: re-enabling 28, leaving 28 as they were.":
            "restauration de l'état enregistré le 2026-10-28T15:00:00 : 28 réactivés, 28 laissés",
        "  leaving com.a alone (disabled when the record was taken)": "  com.a laissé tel quel (disabled",
        "recorded 56 packages on 192.168.1.50 (28 already disabled, left alone by undo) -> /x.json": "56 paquets enregistrés",
    }

    def test_known_lines(self):
        for line, start in self.CASES.items():
            self.assertTrue(firetv.translate_line(line, "fr").startswith(start), line)

    def test_core_refusal_keeps_the_package_names(self):
        line = ("refusing /x/l.txt: it disables core Android or TV middleware packages, and without them the TV may not "
                "boot again (#884): android, com.android.shell. Take these lines out of the list and run it again. "
                "Nothing was checked or changed.")
        out = firetv.translate_line(line, "fr")
        self.assertIn("android, com.android.shell", out)
        self.assertIn("Rien n'a été vérifié ni modifié", out)

    def test_unknown_lines_and_english_are_unchanged(self):
        self.assertEqual(firetv.translate_line("package:com.amazon.firebat\n", "fr"), "package:com.amazon.firebat")
        self.assertEqual(firetv.translate_line("nothing drifted: 1 listed packages\n", "en"), "nothing drifted: 1 listed packages")

    def test_patterns_compile_and_are_anchored(self):
        for pattern, _ in firetv.FR_LINES:
            self.assertTrue(pattern.startswith("^") and pattern.endswith("$"), pattern)


class DownloadTest(unittest.TestCase):
    def test_pinned_checksums_are_sha256(self):
        for key, value in firetv.CMDLINE_SHA256.items():
            self.assertRegex(value, r"^[0-9a-f]{64}$", key)

    def test_download_urls_per_platform(self):
        for system, key, jdk_os in (("Windows", "win", "windows"), ("Darwin", "mac", "mac"), ("Linux", "linux", "linux")):
            with mock.patch("platform.system", return_value=system):
                url, k = firetv.cmdline_tools_url()
                self.assertEqual(k, key)
                self.assertEqual(url, "https://dl.google.com/android/repository/commandlinetools-%s-%s_latest.zip"
                                 % (key, firetv.CMDLINE_TOOLS))
                self.assertIn("/17/ga/%s/" % jdk_os, firetv.jdk_url())

    def test_arch(self):
        with mock.patch("platform.machine", return_value="arm64"):
            self.assertEqual(firetv.host_arch(), "aarch64")
        with mock.patch("platform.machine", return_value="AMD64"):
            self.assertEqual(firetv.host_arch(), "x64")

    def test_only_https_on_known_hosts(self):
        self.assertTrue(firetv.trusted("https://github.com/adoptium/x.tar.gz"))
        self.assertTrue(firetv.trusted("https://dl.google.com/android/repository/x.zip"))
        self.assertFalse(firetv.trusted("http://github.com/adoptium/x.tar.gz"))
        self.assertFalse(firetv.trusted("https://github.com.evil.example/x"))
        self.assertFalse(firetv.trusted("ftp://dl.google.com/x"))
        with self.assertRaises(firetv.Refused):
            firetv.require_trusted("https://example.com/x.apk")

    def test_published_releases(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "RELEASES.txt"
            f.write_text("# tag sha256\nv1.0.0 " + "a" * 64 + "\nbroken line\nv1.1.0 " + "B" * 64 + "  # note\n")
            self.assertEqual(firetv.published_releases(f), [("v1.0.0", "a" * 64), ("v1.1.0", "b" * 64)])
            self.assertEqual(firetv.published_releases(Path(tmp) / "missing.txt"), [])

    def test_repository_release_file_is_well_formed(self):
        if firetv.RELEASES_FILE.exists():
            text = [l for l in firetv.RELEASES_FILE.read_text().splitlines() if l.strip() and not l.startswith("#")]
            self.assertEqual(len(firetv.published_releases()), len(text))


class ChecksumTest(unittest.TestCase):
    def test_mismatch_deletes_the_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "a.bin"
            f.write_bytes(b"abc")
            with mock.patch("sys.stderr", new_callable=io.StringIO), self.assertRaises(SystemExit):
                firetv.verify(f, "0" * 64)
            self.assertFalse(f.exists())

    def test_malformed_expected_sum_is_a_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "a.bin"
            f.write_bytes(b"abc")
            with mock.patch("sys.stderr", new_callable=io.StringIO), self.assertRaises(SystemExit):
                firetv.verify(f, "")
            self.assertFalse(f.exists())

    def test_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "a.bin"
            f.write_bytes(b"abc")
            firetv.verify(f, firetv.sha256_of(f))
            self.assertTrue(f.exists())


class ArchiveTest(unittest.TestCase):
    def test_zip_path_traversal_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.zip"
            with zipfile.ZipFile(bad, "w") as z:
                z.writestr("../escape.txt", "x")
            with self.assertRaises(RuntimeError):
                firetv.extract(bad, Path(tmp) / "out")
            self.assertFalse((Path(tmp) / "escape.txt").exists())

    @unittest.skipIf(os.name == "nt", "POSIX modes")
    def test_zip_modes_drop_setuid(self):
        with tempfile.TemporaryDirectory() as tmp:
            arc = Path(tmp) / "m.zip"
            with zipfile.ZipFile(arc, "w") as z:
                info = zipfile.ZipInfo("tool")
                info.external_attr = (0o4755 << 16)
                z.writestr(info, "x")
            firetv.extract(arc, Path(tmp) / "out")
            self.assertEqual(os.stat(Path(tmp) / "out" / "tool").st_mode & 0o7777, 0o755)

    def _tar(self, tmp, members):
        arc = Path(tmp) / "a.tar.gz"
        with tarfile.open(arc, "w:gz") as tf:
            for name, kind, value in members:
                info = tarfile.TarInfo(name)
                if kind == "sym":
                    info.type, info.linkname = tarfile.SYMTYPE, value
                    tf.addfile(info)
                else:
                    data = value.encode()
                    info.size = len(data)
                    tf.addfile(info, io.BytesIO(data))
        return arc

    def test_tar_symlink_out_of_the_folder_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            outside = Path(tmp) / "outside"
            outside.mkdir()
            arc = self._tar(tmp, [("lnk", "sym", str(outside)), ("lnk/pwn.txt", "file", "x")])
            with self.assertRaises(RuntimeError):
                firetv.extract(arc, Path(tmp) / "out")
            self.assertFalse((outside / "pwn.txt").exists())

    def test_tar_relative_symlink_escaping_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            arc = self._tar(tmp, [("jdk/up", "sym", "../../.."), ("jdk/up/x.txt", "file", "x")])
            with self.assertRaises(RuntimeError):
                firetv.extract(arc, Path(tmp) / "out")

    def test_tar_ordinary_archive_with_inner_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            arc = self._tar(tmp, [("jdk/bin/java", "file", "j"), ("jdk/legal", "sym", "bin")])
            firetv.extract(arc, Path(tmp) / "out")
            self.assertEqual((Path(tmp) / "out" / "jdk" / "bin" / "java").read_text(), "j")


class JdkTest(unittest.TestCase):
    def _jdk(self, base, rel):
        exe = "java.exe" if os.name == "nt" else "java"
        javac = "javac.exe" if os.name == "nt" else "javac"
        b = base / rel / "bin"
        b.mkdir(parents=True)
        (b / exe).write_text("")
        (b / javac).write_text("")
        return base / rel

    def test_linux_and_windows_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = self._jdk(Path(tmp), "jdk-17.0.21+9")
            self.assertEqual(firetv.find_java_home(Path(tmp)), home)

    def test_macos_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = self._jdk(Path(tmp), "jdk-17.0.21+9/Contents/Home")
            self.assertEqual(firetv.find_java_home(Path(tmp)), home)

    def test_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(firetv.find_java_home(Path(tmp) / "nothing"))
            self.assertEqual(firetv.jdk_major(Path(tmp)), 0)


class AccessibilityTest(unittest.TestCase):
    SVC = firetv.HOME_SERVICE

    def test_empty_or_null(self):
        self.assertEqual(firetv.merge_services("null", self.SVC), self.SVC)
        self.assertEqual(firetv.merge_services("", self.SVC), self.SVC)

    def test_other_services_are_kept(self):
        talkback = "com.google.android.marvin.talkback/com.google.android.marvin.talkback.TalkBackService"
        self.assertEqual(firetv.merge_services(talkback, self.SVC), talkback + ":" + self.SVC)

    def test_already_there_in_either_form(self):
        self.assertEqual(firetv.merge_services(self.SVC, self.SVC), self.SVC)
        full = "com.gathin.tvhome/com.gathin.tvhome.HomeKeyService"
        self.assertEqual(firetv.merge_services(full, self.SVC), full)

    def test_unexpected_value_is_left_alone(self):
        self.assertIsNone(firetv.merge_services("a/b; reboot", self.SVC))


class CommandLineTest(unittest.TestCase):
    def test_missing_host_is_refused_before_anything_runs(self):
        with NoTV(), mock.patch.dict(os.environ, {"TV_HOST": ""}):
            status, _, errs = run_main(["probe"])
        self.assertEqual(status, 2)
        self.assertIn("--host", errs)

    def test_unknown_command(self):
        with NoTV():
            self.assertEqual(run_main(["nope"])[0], 2)

    def test_unknown_option_is_refused(self):
        with NoTV():
            self.assertEqual(run_main(["--host", "1.2.3.4", "apply", "--dry-run"])[0], 2)

    def test_extra_argument_is_refused(self):
        with NoTV():
            self.assertEqual(run_main(["--host", "1.2.3.4", "check", "a.txt", "extra"])[0], 2)
            self.assertEqual(run_main(["--host", "1.2.3.4", "probe", "a.txt"])[0], 2)

    def test_theme_reset_with_a_folder_is_refused(self):
        with NoTV():
            self.assertEqual(run_main(["--host", "1.2.3.4", "theme", "themes/aurora", "--reset"])[0], 2)
            self.assertEqual(run_main(["--host", "1.2.3.4", "theme", "--reset", "themes/aurora"])[0], 2)

    def test_no_command_prints_help(self):
        with NoTV():
            status, out, _ = run_main([])
        self.assertEqual(status, 2)
        self.assertIn("firetv.py", out)

    def test_unreachable_tv_is_exit_2_with_a_connection_message(self):
        with mock.patch.object(firetv, "ensure_venv", return_value=None), \
                mock.patch.object(firetv, "tv_shell", side_effect=firetv.TVError("refused the connection")):
            for command in ("check", "probe", "apply", "fix", "restore"):
                status, _, errs = run_main(["--host", "1.2.3.4", command])
                self.assertEqual(status, 2, command)
                self.assertNotIn("Amazon", errs, command)
                self.assertIn("1.2.3.4", errs, command)

    def test_not_amazon_is_exit_1(self):
        with mock.patch.object(firetv, "ensure_venv", return_value=None), \
                mock.patch.object(firetv, "tv_shell", return_value="Xiaomi"):
            self.assertEqual(run_main(["--host", "1.2.3.4", "probe"])[0], 1)

    def test_relative_list_is_read_from_the_current_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "ma-liste.txt").write_text("com.example.app\n")
            cwd = os.getcwd()
            os.chdir(tmp)
            try:
                with mock.patch.object(firetv, "ensure_venv", return_value=None), \
                        mock.patch.object(firetv, "require_fire_tv", return_value="AFTKM"), \
                        mock.patch.object(firetv, "do_backup"), \
                        mock.patch.object(firetv, "run_script", return_value=0) as script:
                    status, _, _ = run_main(["--host", "1.2.3.4", "apply", "ma-liste.txt"])
            finally:
                os.chdir(cwd)
            self.assertEqual(status, 0)
            self.assertEqual(Path(script.call_args[0][2][0]), (Path(tmp) / "ma-liste.txt").resolve())

    def test_missing_list_is_refused_before_the_backup(self):
        with mock.patch.object(firetv, "ensure_venv", return_value=None), \
                mock.patch.object(firetv, "require_fire_tv", return_value="AFTKM"), \
                mock.patch.object(firetv, "do_backup") as backup:
            self.assertEqual(run_main(["--host", "1.2.3.4", "apply", "/nonexistent/list.txt"])[0], 2)
        backup.assert_not_called()

    def test_check_passes_the_status_through(self):
        for code in (0, 1, 2):
            with mock.patch.object(firetv, "ensure_venv", return_value=None), \
                    mock.patch.object(firetv, "require_fire_tv", return_value="AFTKM"), \
                    mock.patch.object(firetv, "run_streamed", return_value=code):
                self.assertEqual(run_main(["--host", "1.2.3.4", "check"])[0], code)


class WrapperTest(unittest.TestCase):
    def test_bat_reads_the_exit_code_after_python_ran(self):
        raw = (ROOT / "firetv.bat").read_bytes()
        self.assertIn(b"\r\n", raw)
        text = raw.decode("ascii")
        # %errorlevel% inside a ( … ) block is expanded before the block runs.
        self.assertNotRegex(text, r"\([^)]*%errorlevel%")
        self.assertIn('"%HERE%firetv.py" %*', text)

    def test_sh_wrapper_keeps_the_callers_folder(self):
        lines = (ROOT / "firetv.sh").read_text().splitlines()
        self.assertFalse(any(l.startswith("cd ") for l in lines))
        self.assertTrue(any('"$here/firetv.py" "$@"' in l for l in lines))


if __name__ == "__main__":
    unittest.main()
