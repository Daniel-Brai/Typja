from typja.helpers import find_templates


class TestFindTemplates:

    def test_find_templates_basic(self, tmp_path):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        (templates_dir / "index.html").write_text("<html></html>")
        (templates_dir / "about.html").write_text("<html></html>")
        (templates_dir / "contact.jinja").write_text("<html></html>")

        found = find_templates(
            templates_dir, include_patterns=["*.html", "*.jinja"], exclude_patterns=[]
        )

        assert len(found) == 3
        assert any(f.name == "index.html" for f in found)
        assert any(f.name == "about.html" for f in found)
        assert any(f.name == "contact.jinja" for f in found)

    def test_find_templates_nested(self, tmp_path):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        (templates_dir / "base.html").write_text("<html></html>")
        subdir = templates_dir / "users"
        subdir.mkdir()
        (subdir / "list.html").write_text("<html></html>")
        (subdir / "detail.html").write_text("<html></html>")

        found = find_templates(
            templates_dir, include_patterns=["*.html"], exclude_patterns=[]
        )

        assert len(found) == 3
        assert any(f.name == "base.html" for f in found)
        assert any(f.name == "list.html" for f in found)
        assert any(f.name == "detail.html" for f in found)

    def test_find_templates_with_exclusions(self, tmp_path):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        (templates_dir / "index.html").write_text("<html></html>")

        node_modules = templates_dir / "node_modules"
        node_modules.mkdir()
        (node_modules / "excluded.html").write_text("<html></html>")

        found = find_templates(
            templates_dir,
            include_patterns=["*.html"],
            exclude_patterns=["**/node_modules/**"],
        )

        assert len(found) == 1
        assert found[0].name == "index.html"
        assert not any(f.name == "excluded.html" for f in found)

    def test_find_templates_multiple_exclusions(self, tmp_path):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        (templates_dir / "index.html").write_text("<html></html>")

        # Create multiple excluded directories
        (templates_dir / "node_modules").mkdir()
        (templates_dir / "node_modules" / "excluded1.html").write_text("<html></html>")

        (templates_dir / "dist").mkdir()
        (templates_dir / "dist" / "excluded2.html").write_text("<html></html>")

        found = find_templates(
            templates_dir,
            include_patterns=["*.html"],
            exclude_patterns=["**/node_modules/**", "**/dist/**"],
        )

        assert len(found) == 1
        assert found[0].name == "index.html"

    def test_find_templates_multiple_patterns(self, tmp_path):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        (templates_dir / "index.html").write_text("<html></html>")
        (templates_dir / "base.jinja").write_text("<html></html>")
        (templates_dir / "email.jinja2").write_text("<html></html>")
        (templates_dir / "macro.j2").write_text("<html></html>")
        (templates_dir / "style.css").write_text("/* css */")

        found = find_templates(
            templates_dir,
            include_patterns=["*.html", "*.jinja", "*.jinja2", "*.j2"],
            exclude_patterns=[],
        )

        assert len(found) == 4
        assert not any(f.name == "style.css" for f in found)

    def test_find_templates_empty_directory(self, tmp_path):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        found = find_templates(
            templates_dir, include_patterns=["*.html"], exclude_patterns=[]
        )

        assert len(found) == 0

    def test_find_templates_nonexistent_directory(self, tmp_path):
        nonexistent = tmp_path / "does_not_exist"

        found = find_templates(
            nonexistent, include_patterns=["*.html"], exclude_patterns=[]
        )

        assert len(found) == 0

    def test_find_templates_sorted_output(self, tmp_path):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        (templates_dir / "zebra.html").write_text("<html></html>")
        (templates_dir / "alpha.html").write_text("<html></html>")
        (templates_dir / "beta.html").write_text("<html></html>")

        found = find_templates(
            templates_dir, include_patterns=["*.html"], exclude_patterns=[]
        )

        assert len(found) == 3

        names = [f.name for f in found]
        assert names == sorted(names)

    def test_find_templates_no_duplicates(self, tmp_path):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        (templates_dir / "index.html").write_text("<html></html>")

        found = find_templates(
            templates_dir,
            include_patterns=["*.html", "index.html"],
            exclude_patterns=[],
        )

        assert len(found) == 1
        assert found[0].name == "index.html"

    def test_find_templates_case_sensitive(self, tmp_path):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        (templates_dir / "Index.HTML").write_text("<html></html>")
        (templates_dir / "about.html").write_text("<html></html>")

        found = find_templates(
            templates_dir, include_patterns=["*.html"], exclude_patterns=[]
        )

        assert len(found) == 1
        assert found[0].name == "about.html"

    def test_find_templates_deeply_nested(self, tmp_path):
        templates_dir = tmp_path / "templates"
        path = templates_dir / "a" / "b" / "c" / "d"
        path.mkdir(parents=True)

        (path / "deep.html").write_text("<html></html>")

        found = find_templates(
            templates_dir, include_patterns=["*.html"], exclude_patterns=[]
        )

        assert len(found) == 1
        assert found[0].name == "deep.html"

    def test_find_templates_with_pycache(self, tmp_path):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        (templates_dir / "index.html").write_text("<html></html>")

        pycache = templates_dir / "__pycache__"
        pycache.mkdir()
        (pycache / "excluded.html").write_text("<html></html>")

        found = find_templates(
            templates_dir,
            include_patterns=["*.html"],
            exclude_patterns=["**/__pycache__/**"],
        )

        assert len(found) == 1
        assert found[0].name == "index.html"

    def test_find_templates_only_files(self, tmp_path):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        (templates_dir / "index.html").write_text("<html></html>")
        (templates_dir / "subdir").mkdir()

        found = find_templates(
            templates_dir, include_patterns=["*"], exclude_patterns=[]
        )

        assert all(f.is_file() for f in found)

    def test_find_templates_relative_paths(self, tmp_path):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        (templates_dir / "index.html").write_text("<html></html>")

        found = find_templates(
            templates_dir, include_patterns=["*.html"], exclude_patterns=[]
        )

        assert all(f.is_absolute() for f in found)

    def test_find_templates_using_test_fixtures(self, valid_templates_dir):
        found = find_templates(
            valid_templates_dir,
            include_patterns=["*.html", "*.jinja"],
            exclude_patterns=[],
        )

        assert len(found) > 0
        assert any(f.name == "simple_vars.html" for f in found)
