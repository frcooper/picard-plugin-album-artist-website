import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
README_PATH = REPO_ROOT / "README.md"
MANIFEST_PATH = REPO_ROOT / "MANIFEST.toml"


_MANIFEST_VERSION_RE = re.compile(r'^version\s*=\s*"(?P<version>[^"]+)"\s*$', re.MULTILINE)
_README_VERSION_RE = re.compile(r'^-\s+Plugin version:\s*(?P<version>\S+)\s*$', re.MULTILINE)


class VersionSyncTests(unittest.TestCase):
    def test_manifest_version_matches_readme(self) -> None:
        manifest_text = MANIFEST_PATH.read_text(encoding="utf-8")
        readme_text = README_PATH.read_text(encoding="utf-8")

        m2 = _README_VERSION_RE.search(readme_text)
        self.assertIsNotNone(m2, "Could not find '- Plugin version:' in README.md")
        assert m2 is not None
        readme_version = m2.group("version")

        m1 = _MANIFEST_VERSION_RE.search(manifest_text)
        self.assertIsNotNone(m1, "Could not find version in MANIFEST.toml")
        assert m1 is not None
        manifest_version = m1.group("version")
        self.assertEqual(manifest_version, readme_version)


if __name__ == "__main__":
    unittest.main()
