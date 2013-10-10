import nltk
from nltk.corpus import stopwords
from nltk.tokenize import wordpunct_tokenize
import re
import string

_STOPWORDS = set(stopwords.words('english'))

_re_url = re.compile(r"""
    (https?|ftp)://((?P<subdomain>[^.]+)\.)?
    (?P<host>[^.]+)\.(?P<domain>[^/:]+)(?P<path>[^\.]*)
    """, re.VERBOSE | re.I)

def clean_url(url):
    """
    Return space-delimited string of valid host and path tokens.
    """
    m = _re_url.search(url)
    if m:
        is_valid = lambda x: x and x.isalnum() and not x.isdigit()
        path_tokens = filter(
            is_valid, re.split(r'[^a-z|0-9]', m.group('path'), flags=re.I))
        return '%s %s' % (m.group('host'), ' '.join(path_tokens))
    return ''

def clean_tweet_text(tweet):
    """
    Return tweet text without hyperlinks and appended url terms.
    """
    text = tweet['text']
    text = re.sub(r'http[^ ]+', '', text)
    for url in tweet['entities']['urls']:
        text += ' ' + clean_url(url['expanded_url'])    
    return text.strip().encode('utf-8')

def clean_text(text):
    return text.encode('utf-8')

def is_valid_bigram(bigram):
    """
    First and second words must be capitalized and not stop words.
    """
    return bigram[0][0].isupper() and \
        not is_stop_word(bigram[0]) and \
        bigram[1][0].isupper() and \
        not is_stop_word(bigram[1])

def is_valid_trigram(trigram):
    """
    First and third word must be capitalized and not stop words. The second
    word must be alpha, e.g. Bank of America.
    """
    return trigram[0][0].isupper() and \
        not is_stop_word(trigram[0]) and \
        trigram[1][0].isalpha() and \
        trigram[2][0].isupper() and \
        not is_stop_word(trigram[2])

def is_valid_unigram(word):
    l = len(word)
    return not is_stop_word(word) and \
        word.isalnum() and \
        not word.isdigit() and \
        l > 2 and \
        l < 12

def is_stop_word(word):
    return word.lower() in _STOPWORDS

def tokenize(text, include_ngrams=True, limit_ngrams=False):
    words = wordpunct_tokenize(text)

    unigrams = filter(is_valid_unigram, words)

    bigrams, trigrams = [], []
    if include_ngrams:
        bigrams = nltk.bigrams(words)
        trigrams = nltk.trigrams(words)
        if limit_ngrams:
            bigrams = filter(is_valid_bigram, bigrams)
            trigrams = filter(is_valid_trigram, trigrams)

    tokens = unigrams + map(lambda ngram: ' '.join(ngram), bigrams + trigrams)

    return map(string.lower, tokens)
