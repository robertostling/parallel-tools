import sys
import argparse
import re
from collections import Counter
import glob
from configparser import ConfigParser
import os.path

from mpfile import MPFile

CONFIG = ConfigParser()
for config_filename in ['/etc/parallel-tools']:
    if os.path.exists(config_filename):
        CONFIG.read(config_filename)


RE_CONTEXT = re.compile('(\w+):(\d+):(\d+)$')

def parse_context(s):
    m = RE_CONTEXT.match(s)
    if m is None:
        raise ValueError('Invalid context description: "%s"' % s)
    return (m.group(1), int(m.group(2)), int(m.group(3)))


def find_files(names, corpus_path=None):
    if corpus_path is None:
        if 'default' in CONFIG and 'corpus_path' in CONFIG['default']:
            corpus_path = CONFIG['default']['corpus_path']
    filenames = []
    for name in names:
        if os.path.exists(name):
            filenames.append(name)
        elif corpus_path:
            found = glob.glob(os.path.join(corpus_path, name + '*.txt'))
            if found:
                filenames.extend(found)
            else:
                print('WARNING: %s not found' % name, file=sys.stderr)
        else:
            print('WARNING: %s not found' % name, file=sys.stderr)
    return filenames

def main():
    parser = argparse.ArgumentParser(description='Parallel corpus searching')
    parser.add_argument(
            '-e', '--expression', type=str, metavar='REGEX', action='append',
            help='Regular expression(s) to search for')
    parser.add_argument(
            '-v', '--verbose', action='store_true',
            help='Print matches for manual inspection')
    parser.add_argument(
            '-l', '--lowercase', action='store_true',
            help='Lower-case text before matching')
    parser.add_argument(
            '-a', '--append', action='store_true',
            help='Merge the mathches of this search with previous results')
    parser.add_argument(
            '-p', '--corpus-path', type=str, metavar='PATH',
            help='Path to parallel corpus')
    parser.add_argument(
            'files', nargs='+', metavar='FILE')

    args = parser.parse_args()

    if args.append:
        try:
            contexts = list(map(parse_context, sys.stdin.readlines()))
        except ValueError as e:
            print(e, file=sys.stderr)
            print('''
Note that find_instances.py expects a list of contexts on standard input.
This list may be empty. Check if you accidentally directed some other data to
this process.'''.strip(), file=sys.stderr)
            sys.exit(1)
    else:
        contexts = []

    contexts = {sent_id: (k, n) for sent_id, k, n in contexts}

    regexes = [re.compile(e) for e in args.expression]

    sent_id_count = Counter()
    sent_id_matches = Counter()
    examples = []

    for filename in find_files(args.files, args.corpus_path):
        mpf = MPFile(filename)
        sent_id_count.update(mpf.sentences.keys())
        for sent_id, sent in mpf.sentences.items():
            if args.lowercase:
                sent = sent.lower()
            for regex in regexes:
                if args.verbose:
                    m = regex.search(sent)
                    if m:
                        show = True
                        if args.append:
                            if sent_id in contexts:
                                k, n = contexts[sent_id]
                                if k*2 < n:
                                    show = False
                            else:
                                show = False
                        if show:
                            examples.append((sent, m))
                else:
                    if regex.search(sent):
                        sent_id_matches[sent_id] += 1

    if args.verbose:
        for sent, m in examples:
            i = m.start()
            j = m.end()
            print('%s\033[91m%s\033[0m%s' % (sent[:i], sent[i:j], sent[j:]))
    else:
        for sent_id, (k, n) in contexts.items():
            sent_id_count[sent_id] += n
        for sent_id, n in sorted(sent_id_count.items()):
            k = sent_id_matches[sent_id]
            if sent_id in contexts:
                ck, cn = contexts[sent_id]
                k += ck
            print('%s:%d:%d' % (sent_id, k, n))


if __name__ == '__main__': main()

