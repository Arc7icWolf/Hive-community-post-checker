import unittest
from community_post_checker import text_language, convert_and_count_words, clean_markdown


class TestFuncs(unittest.TestCase):

    def test_text_language(self):
        # Test language detection
        result_ita = text_language("Questo è un testo in italiano.")
        self.assertTrue(result_ita[0])
        self.assertEqual(result_ita[1], 1)
        result_eng_ita = text_language("This is an Eglish text. Questo invece è un testo in italiano.")
        self.assertTrue(result_eng_ita[0])
        self.assertEqual(result_eng_ita[1], 2)

    def test_clean_markdown(self):
        # Test cleaning markdown
        markdown_text = "This is a ![alt text](image.jpg) [link](http://example.com)"
        result = clean_markdown(markdown_text)
        self.assertNotIn("![alt text]", result)
        self.assertNotIn("[link](http://example.com)", result)
        self.assertNotIn("alt text", result)
        self.assertIn("link", result)

    def test_convert_and_count_words(self):
        # Test word count function
        md_text_eng = "This is a **bold** text with a [link](http://example.com) and an ![image](image.jpg)"
        result_eng = convert_and_count_words(md_text_eng)
        self.assertEqual(result_eng, 10)
        md_text_ita = "L'apostrofo ed i numeri 123; 1, 2 e 3 con un tag @name."
        result_ita = convert_and_count_words(md_text_ita)
        self.assertEqual(result_ita, 14)


if __name__ == "__main__":
    unittest.main()
