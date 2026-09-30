import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/study-shared/scripts"))
FIX = Path(__file__).parent / "fixtures"

SITEMAP = """<?xml version="1.0"?><urlset>
<url><loc>https://platzi.com/cursos/storage-aws/</loc></url>
<url><loc>https://platzi.com/cursos/aws-iam/</loc></url>
<url><loc>https://platzi.com/blog/something/</loc></url>
</urlset>"""


class Parsers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import platzi
        cls.p = platzi
        cls.course = platzi.parse_course(FIX.joinpath("platzi-course.html").read_text(encoding="utf-8"), "curso-demo")

    def test_catalog_keeps_only_course_urls(self):
        rows = self.p.parse_catalog(SITEMAP)
        self.assertEqual([r["slug"] for r in rows], ["storage-aws", "aws-iam"])
        self.assertEqual(rows[0]["url"], "https://platzi.com/cursos/storage-aws/")

    def test_course_metadata(self):
        c = self.course
        self.assertEqual(c["title"], "Curso de Demostración")
        self.assertTrue(c["description"].startswith("Fixture sintética"))
        self.assertEqual(c["level"], "Básico")

    def test_course_classes(self):
        cls = self.course["classes"]
        self.assertEqual(len(cls), 4)
        three = [x for x in cls if x["n"] == 3][0]
        self.assertEqual(three["title"], "Versionar sin miedo: control y recuperación")
        self.assertEqual(three["duration"], "08:30")
        self.assertEqual(three["minutes"], 8.5)
        self.assertEqual(three["url"], "https://platzi.com/cursos/curso-demo/versionar-sin-miedo/")
        self.assertEqual([x["n"] for x in cls], [1, 2, 3, 4])

    def test_course_total_minutes(self):
        self.assertAlmostEqual(self.course["total_minutes"], sum(x["minutes"] for x in self.course["classes"]), places=1)

    def test_summary_is_the_class_text_only(self):
        s = self.p.parse_summary(FIX.joinpath("platzi-class.html").read_text(encoding="utf-8"))
        self.assertIn("encriptación del lado del servidor", s)
        self.assertIn("Primer punto & detalle.", s)
        self.assertNotIn("<", s)
        self.assertNotIn("Inglés Básico", s)
        self.assertNotIn("texto de script", s)

    def test_summary_missing_returns_empty(self):
        self.assertEqual(self.p.parse_summary("<html><body><p>nothing here</p></body></html>"), "")


if __name__ == "__main__":
    unittest.main()
