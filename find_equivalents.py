import sys
import math
import argparse
import re

from multiprocessing import Pool
from collections import Counter, defaultdict
from operator import itemgetter
import os.path

from scipy.special import gammaln

from mpfile import MPFile
from find_instances import parse_context, find_files

def bigrams(tokens):
    return [w_t+'_'+w_tp1 for w_t, w_tp1 in zip(tokens, tokens[1:])]

def prefixes(tokens, n=6):
    return ['_'+w[:i] for w in tokens
                      for i in range(1, min(n+1, len(w)-2))]

def suffixes(tokens, n=6):
    return [w[-i:]+'_' for w in tokens
                       for i in range(1, min(n+1, len(w)-2))]

def subsequences(tokens, n=10):
    return ['#'+w[i:j]+'#'
            for w in tokens
            for i in range(0, len(w)-1)
            for j in range(i+1, len(w)+1)]

def logll_dirichlet_multinomial(alpha, n, x):
    assert len(alpha) == len(x)
    assert n == sum(x)
    z = gammaln(sum(alpha)) - gammaln(n + sum(alpha))
    return z + sum(gammaln(x[k] + alpha[k]) - gammaln(alpha[k])
                   for k in range(len(x)))

def find_translations(t):
    filename, contexts, options = t

    mpf = MPFile(filename)

    contexts = [t for t in contexts if t[0] in mpf.sentences]
    all_context_sents = {sent_id for sent_id, k, n in contexts}
    context_vector = {sent_id: k/n for sent_id, k, n in contexts if k}
    item_context_counts = defaultdict(Counter)

    vocabulary = {token for sentence in mpf.sentences.values()
                        for token in sentence}

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
    if 'subsequences' in features:
        extractors.append(subsequences)

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
        if options['score'] == 'bayes':
            u = set(counts.keys())
            v = {k for k, v in context_vector.items() if v >= 0.5}
            n = len(all_context_sents)
            assert n >= len(u|v)
            log_p_independent = logll_dirichlet_multinomial(
                    [1.0, 1.0], n, [len(u), n-len(u)])
            log_p_independent += logll_dirichlet_multinomial(
                    [1.0, 1.0], n, [len(v), n-len(v)])
            log_p_joint =  logll_dirichlet_multinomial(
                    [1.0, 1.0, 1.0, 1.0],  n,
                    [len(u-v), len(v-u), len(v&u), n-len(v|u)])
            log_p_prior = -math.log(len(vocabulary))
            return log_p_prior + log_p_joint - log_p_independent
        elif options['score'] == 'cosine':
            z = sum(x*contexts_vector[sent_id] for sent_id, x in counts.items())
            counts_norm = math.sqrt(sum(x*x for x in counts.values()))
            return z / (counts_norm * contexts_norm)
        else:
            assert False

    scores = sorted([
            (item, similarity(context_counts))
            for item, context_counts in candidates],
            key=lambda t: (-t[1], -len(t[0])))

    if 'subsequences' in features:
        raw_scores = scores
        scores = []
        seen = set()
        for item, x in raw_scores:
            if item[0] == '#' and item[-1] == '#':
                w = item[1:-1]
                if w in seen: continue
                for i in range(0, len(w)-1):
                    for j in range(i+1, len(w)+1):
                        seen.add(w[i:j])
            elif item[0] != '_' and item[-1] != '_':
                seen.add(item)
            scores.append((item, x))

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
            '-s', '--score', type=str, metavar='NAME',
            default='bayes',
            help='scoring method: bayes (Dirichlet-multinomial model), cosine')
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
               'max_ratio': args.max_ratio,
               'score': args.score}

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

