import sys
import math
import argparse
import re
from multiprocessing import Pool
from collections import Counter, defaultdict
from operator import itemgetter
import os.path

from mpfile import MPFile
from find_instances import parse_context, find_files

def bigrams(tokens):
    return [w_t+'_'+w_tp1 for w_t, w_tp1 in zip(tokens, tokens[1:])]

def prefixes(tokens, n=6):
    return ['_'+w[:i] for w in tokens
                      for i in range(1, min(n+1, len(tokens)-2))]

def suffixes(tokens, n=6):
    return [w[-i:]+'_' for w in tokens
                       for i in range(1, min(n+1, len(tokens)-2))]


def find_translations(t):
    filename, contexts, options = t

    mpf = MPFile(filename)

    contexts = [t for t in contexts if t[0] in mpf.sentences]
    all_context_sents = {sent_id for sent_id, k, n in contexts}
    context_vector = {sent_id: k/n for sent_id, k, n in contexts if k}
    item_context_counts = defaultdict(Counter)

    # Maximum length ratio allowed between candidates and the contexts
    # That is, items that are this many times more (or less) common than the
    # thing we are searching for should be ignored.
    max_ratio = options.get('max_ratio', 4)

    n_best = options.get('n_best')

    extractors = []
    features = options.get('features', ['words'])
    if 'words' in features:
        extractors.append(lambda x: x)
    if 'bigrams' in features:
        extractors.append(bigrams)
    if 'prefixes' in features:
        extractors.append(prefixes)
    if 'suffixes' in features:
        extractors.append(suffixes)

    for extractor in extractors:
        for sent_id, sent in mpf.sentences.items():
            if sent_id not in all_context_sents: continue
            for item in extractor(sent.split()):
                item_context_counts[item][sent_id] += 1

    context_count = sum(int(x >= 0.5) for x in context_vector.values())
    min_count = context_count / max_ratio
    max_count = context_count * max_ratio
    candidates = [(item, context_counts)
                  for item, context_counts in item_context_counts.items()
                  if len(context_counts) >= min_count and
                     len(context_counts) <= max_count]

    contexts_vector = {sent_id: k/n for sent_id, k, n in contexts}
    contexts_norm = math.sqrt(sum(x*x for x in contexts_vector.values()))

    def similarity(counts):
        z = sum(x*contexts_vector[sent_id] for sent_id, x in counts.items())
        counts_norm = math.sqrt(sum(x*x for x in counts.values()))
        return z / (counts_norm * contexts_norm)

    scores = sorted([
            (item, similarity(context_counts))
            for item, context_counts in candidates],
            key=itemgetter(1), reverse=True)

    return scores[:n_best] if n_best else scores


def main():
    parser = argparse.ArgumentParser(
            description='Finding translation equivalents')
    parser.add_argument(
            '-f', '--features', type=str, metavar='FEATURES',
            default='words',
            help='comma-separated list of features: words, bigrams, '
                 'prefixes, suffixes')
    parser.add_argument(
            '-m', '--max-ratio', type=int, default=4, metavar='N',
            help='higher values widens the search space')
    parser.add_argument(
            '-n', '--n-best', type=int, default=5, metavar='N',
            help='print the N best matches only')
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

    options = {'n_best': args.n_best,
               'features': args.features.split(','),
               'max_ratio': args.max_ratio}

    filenames = find_files(args.files, corpus_path=args.corpus_path)
    tasks = [(filename, contexts, options) for filename in filenames]

    with Pool() as p:
        result = list(p.map(find_translations, tasks))

    for scores, filename in zip(result, filenames):
        print(os.path.basename(filename))
        for item, score in scores:
            print('    %.2f  %s' % (score, item))
        print()


if __name__ == '__main__': main()

