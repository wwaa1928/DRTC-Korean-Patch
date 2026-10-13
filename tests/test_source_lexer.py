import unittest

from tools.source_lexer import classify_literal,lex_literals


class LiteralClassificationTests(unittest.TestCase):
    def classify(self,tail):
        code=b'"Foo" '+tail
        literals,issues=lex_literals(code)
        self.assertEqual(issues,[])
        literal=literals[0]
        return classify_literal(literal,code[literal['end']+1:])

    def test_technical_tokens_followed_by_whitespace_or_end(self):
        for token in (b'$=',b'str>',b'>str',b'evaluate',b'$load',b'load',b'parse'):
            for suffix in (b'',b' if',b'\r\nnext',b'\tnext'):
                with self.subTest(token=token,suffix=suffix):
                    self.assertEqual(self.classify(token+suffix),'review-code-or-identifier')

    def test_longer_words_are_not_technical_tokens(self):
        for token in (b'$=other',b'str>other',b'>string',b'evaluate-other',b'loader',b'parse-extra'):
            with self.subTest(token=token):self.assertEqual(self.classify(token),'text-candidate')

    def test_display_literal_remains_translatable(self):
        self.assertEqual(self.classify(b'print'),'text-candidate')


if __name__=='__main__':unittest.main()
