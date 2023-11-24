import sys
import math
import argparse
import re

from collections import Counter, defaultdict
from operator import itemgetter
import os.path

from mpfile import MPFile
from find_instances import parse_context, find_files


def main():
    parser = argparse.ArgumentParser(
            description='Displaying parallel verses')
    parser.add_argument(
            '-n', '--first-n', type=int, default=0, metavar='N',
            help='print the top N matches only')
    parser.add_argument(
            '-v', '--verbose', action='store_true',
            help='more verbose output')
    parser.add_argument(
            '-s', '--shortest-first', action='store_true',
            help='sort verses by length')
    parser.add_argument(
            '-c', '--contexts', type=str, metavar='FILE',
            help='file containing contexts (from find_instances.py), default:'
                 ' stdin')
    parser.add_argument(
            '--corpus-path', type=str, metavar='FILE',
            help='directory of corpus files (overrides value in config file)')
    parser.add_argument(
            'files', nargs='+', metavar='FILE')

    args = parser.parse_args()

    if args.contexts:
        with open(args.contexts) as f:
            contexts = f.readlines()
    else:
        contexts = [s for s in sys.stdin.read().split('\n') if s.strip()]

    try:
        contexts = list(map(parse_context, contexts))
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    filenames = find_files(args.files, corpus_path=args.corpus_path)

    mpfs = [MPFile(filename) for filename in filenames]

    verses = [sent_id for sent_id, k, n in contexts
              if k*2 >= n and all(sent_id in mpf.sentences for mpf in mpfs)]

    verse_texts = [(sent_id, [mpf.sentences[sent_id] for mpf in mpfs])
                   for sent_id in verses]

    if args.shortest_first:
        verse_texts.sort(
                key=lambda t: sum(len(' '.join(text)) for text in t[1]))

    if args.first_n:
        verse_texts = verse_texts[:args.first_n]

    for sent_id, texts in verse_texts:
        print(sent_id)
        for text in texts:
            print(text)
        print()


if __name__ == '__main__': main()

