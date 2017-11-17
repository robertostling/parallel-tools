# parallel-tools

This is a collection of scripts for making it simple to search for (possible)
translation equivalents of morphemes, words or phrases using multiparallel
corpora, for instance the Bible.

## Example

The first part of this command, using `find_instance.py`, extracts the number
of instances of the pattern (in this case, the bigram *not yet*) in each
sentence of the English translations. The second part, using
`find_equivalents.py`, searches for words and bigrams in Indonesian and
German that match the distribution of *not yet*.

```python3 find_instances.py -e ' not yet ' eng | \
    python3 find_equivalents.py --features=words,bigrams ind deu```

Use of ISO codes assumes that `/etc/parallel-tools` contains the corpus path,
for instance:

```[default]

corpus_path=/data/paralleltext/bibles/corpus```

It is also possible to specify filenames directly, instead of ISO codes.

## Performance

This benchmark consists of searching through 1698 Bible translations for
sequences corresponding to Finnish character sequence "hyvä".
The time depends crucially on what types of sequences we look for.

* Words only: 69 seconds
* Words and bigrams: 205 seconds

