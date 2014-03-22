from patternreplacer import PatternReplacer

samplepattern_no = 'this-is-my-/test/-t.png'
samplepattern_begin = '/-this-is-my-/test/-t.png'
samplepattern_end = '/-this-is-my-/test/-t.png/'
samplepattern_both = '///this-ismy-/test/-t.png/'


def test_no_delimiter():
    pr = PatternReplacer("replaceme", '-/')
    assert pr.get_n_delimiters() == 0
    assert pr.get_n_tokens() == 1, pr.get_n_tokens()
    assert pr.replace(['onetoken']) == 'onetoken'


def test_finds_proper_number_of_delimiters():
    pr = PatternReplacer(samplepattern_no, '-/')
    assert pr.get_n_delimiters() == 4

    pr = PatternReplacer(samplepattern_both, '-/')
    assert pr.get_n_delimiters() == 5


def test_verify():
    pr = PatternReplacer(samplepattern_no, '-/')
    assert pr.verify('i-want-to-/a/-g') is True
    assert pr.verify('i-wan-tto-/a/-g') is True
    assert pr.verify('i-wan-tto-/ag/-') is False
    assert pr.verify('-iwan-tto-/a/-g') is False
    assert pr.verify('i-wan-t-to-/a-g') is False
    assert pr.verify('/i-want-to-/ag') is False
    assert pr.verify('/i-wantto-/ag/') is False


def test_number_of_tokens():
    pats = [(samplepattern_no, 5), (samplepattern_begin, 5), (samplepattern_end, 5), (samplepattern_both, 4)]

    for pat, expect in pats:
        pr = PatternReplacer(pat, '-/')
        assert pr.get_n_tokens() == expect, pat


def test_replace():
    tokens = ['first', 'second', 'third', 'fourth', 'fifth']
    pr = PatternReplacer(samplepattern_no, '-/')
    assert pr.replace(tokens) == 'first-second-third-/fourth/-fifth', pr.replace(tokens)

    pr = PatternReplacer(samplepattern_begin, '-/')
    assert pr.replace(tokens) == '/-first-second-third-/fourth/-fifth', pr.replace(tokens)

    pr = PatternReplacer(samplepattern_end, '-/')
    assert pr.replace(tokens) == '/-first-second-third-/fourth/-fifth/', pr.replace(tokens)

    pr = PatternReplacer(samplepattern_both, '-/')
    assert pr.replace(tokens[0:4]) == '///first-second-/third/-fourth/', pr.replace(tokens[0:4])


def test_other_delimiter():
    pr = PatternReplacer(r'abd#k\hj#$', '#$')
    assert pr.get_n_delimiters() == 2
    assert pr.replace(['first', 'second']) == r'first#second#$'


