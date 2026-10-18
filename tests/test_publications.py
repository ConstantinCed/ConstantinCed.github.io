import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import update_publications as u


def feed(author=u.AUTHOR, paper_id='2610.19251v1', title='A &amp; B'):
    return f'''<feed xmlns="http://www.w3.org/2005/Atom"><entry>
    <id>http://arxiv.org/abs/{paper_id}</id><title>{title}</title>
    <published>2026-10-13T22:11:50Z</published><author><name>{author}</name></author>
    </entry></feed>'''


class PublicationsTests(unittest.TestCase):
    def test_new_paper_preserves_manual_annotations_and_surrounding_page(self):
        old = u.render('2607.27342', {'title':'Existing', 'authors':[u.AUTHOR+'*', 'Ishaan Kannan*'], 'date':'July 2026 · *Equal contribution'})
        html = 'before\n' + u.START + old + u.END + '\nafter'
        updated, added = u.update_html(html, u.parse_feed(feed()))
        self.assertEqual(added, ['2610.19251'])
        self.assertIn(old, updated)
        self.assertTrue(updated.startswith('before\n'))
        self.assertTrue(updated.endswith('\nafter'))
        self.assertLess(updated.index('2610.19251'), updated.index('2607.27342'))
        self.assertEqual(u.update_html(updated, u.parse_feed(feed(paper_id='2610.19251v2'))), (updated, []))

    def test_excludes_other_authors_and_fails_closed(self):
        for data in [feed(author='Someone Cedillo'), '<feed/>', feed(paper_id='error')]:
            with self.assertRaises(ValueError):
                u.parse_feed(data)

    def test_escapes_external_text(self):
        papers = u.parse_feed(feed(title='&lt;script&gt; &amp; math'))
        block = u.render('2610.19251', papers['2610.19251'])
        self.assertIn('&lt;script&gt; &amp; math', block)
        self.assertNotIn('<script>', block)
        self.assertIn('<strong>'+u.AUTHOR+'</strong>', block)

    def test_missing_markers_do_not_replace_page(self):
        with self.assertRaises(ValueError):
            u.update_html('<html>untouched</html>', u.parse_feed(feed()))


if __name__ == '__main__':
    unittest.main()
