# parallel-tools

This is a collection of scripts for making it simple to search for (possible)
translation equivalents of morphemes, words or phrases using multiparallel
corpora, for instance the Bible.

## Example

The first part of this command, using `find_instance.py`, extracts the number
of instances of the pattern (in this case, the bigram *not yet*) in each
sentence of the English translations. The second part, using
`find_equivalents.py`, searches for words and bigrams in Indonesian,
German and Digo that match the distribution of *not yet*.

```
    python3 find_instances.py -e ' not yet ' eng | \
    python3 find_equivalents.py --features=words,bigrams,sequences ind deu dig
```

You can also do the inverse, that is, search for something in English which
corresponds to the average distribution of the word *belum* in Indonesian,
the bigram *noch nicht* in German, and the morpheme *dzangbwe* in Digo:

```
    python3 find_instances.py -e ' belum ' ind | \
    python3 find_instances.py -a -e ' noch nicht ' deu | \
    python3 find_instances.py -a -e 'dzangbwe' dig | \
    python3 find_equivalents.py --features=words,bigrams,subsequences eng
```

Note the flag `-a` in the last two calls to `find_instances.py`. This tells
the program to combine the the German contexts with the ones from Indonesian,
and then combine the Digo contexts with the combined Indonesian/German ones.
We can of course also search for these individually:

```
    python3 find_instances.py -e 'dzangbwe' dig | \
    python3 find_equivalents.py --features=words,bigrams,subsequences eng
```

Use of ISO codes assumes that `/etc/parallel-tools` contains the corpus path,
for instance:

```
[default]

corpus_path=/data/paralleltext/bibles/corpus
```

It is also possible to specify filenames directly, instead of ISO codes.

## Performance

This benchmark consists of searching through 1698 Bible translations for
sequences corresponding to Finnish character sequence "hyvä".
The time depends crucially on what types of sequences we look for, and on the
number of processors of the machine, for the numbers below a 12-core Xeon CPU
with hyperthreading was used:

* Words only: 69 seconds
* Words and bigrams: 205 seconds

## Developing queries

You can use the `-v` option to `find_instances.py` to print out the instances
found in context. For instance:

```
python3 find_instances.py -v -e 'dzangbwe' dig
```

This is useful as a sanity check to make sure you do not get a lot of
unintended hits in the source/seed language.

