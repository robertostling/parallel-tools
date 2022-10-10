# parallel-tools

This is a collection of scripts for making it simple to search for (possible)
translation equivalents of morphemes, words or phrases using multiparallel
corpora, for instance the Bible.

## Searching

Searches are split into two parts:
 1. identifying sentences/verses in the source language(s) matching some
    criteria, specified using one or more regular expressions.
 2. searching for words or character sequences in the target language(s) that
    correlate with the distribution of the sentences/verses found in step 1.

For instance, if we want to search for *not yet* in English
(ISO 639-3: `eng`), the `find_instances.py` script can be used like this:
```
python3 find_instances.py -e ' not yet ' eng
```

This will create a (long) list that looks like this:
```
01001001:0:6
01001002:0:6
01001003:0:6
01001004:0:6
[...]
60001008:1:32
[...]
62003002:23:32
[...]
```
The first column is the sentence identifier (in the Bible: verse
number), the second column is the number of occurrences of the search term in
that sentence, and the third column is the number of times the verse was found
in the language(s) used for the search (not all translations contain the same
sentences, the major split in the Bible corpus being between the New Testament
and the Old Testament).

Most verses contain zero instances of *not yet*, while e.g. verse 60001008
contains *not yet* in only 1 of 32 translations of that verse, and 62003002
contains *not yet* in 23 of 32 translations.

*Note the spaces*! What follows the `-e` argument is a regular expression, and
in this case we are interested in two full tokens, *not* and *yet*. It is also
possible to search for things like suffixes, including variants due to vowel
harmony (note that there is only a space _after_ the suffix):
```
python3 find_instances.py -e 'ss[aä] ' fin
```

The list can be passed to the `find_equivalents.py` script, which does the
heavy work of finding translation equivalents in other languages.

## Developing queries

You can use the `-v` option to `find_instances.py` to print out the instances
found in context. For instance:

```
python3 find_instances.py -v -e 'dzangbwe' dig
```

This is useful as a sanity check to make sure you do not get a lot of
unintended hits in the source/seed language.

## Example

The first part of this command, using `find_instance.py`, extracts the number
of instances of the pattern (in this case, the bigram *not yet*) in each
sentence of the English translations. The second part, using
`find_equivalents.py`, searches for words and bigrams in Indonesian,
German and Digo that match the distribution of *not yet*.

```
python3 find_instances.py -e ' not yet ' eng | \
    python3 find_equivalents.py --features=words,bigrams,subsequences ind deu dig
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

## Types of searches

The argument `--features` takes a comma-separated list which can combine the
following types:

* words
* bigrams
* prefixes
* suffixes
* subsequences

Note that `subsequences` also covers prefixes and suffixes, so there is no
point combining these. If you only want to look at the end or beginning of
words, specifying `suffixes` or `prefixes` can save time, however.

In the hits, underscore `_` is used to indicate a word boundary.


## Comparing expressions

You can also combine `-v` with `-a` to only display instances that also match
the previous query. For instance, if you want manually look for plural
markers in Swedish, you can start by selecting a suitable noun in English and
searching for its equivalent. In this case, we start with the forms "snake"
and "snakes" (regular expression: ` snakes? `):

```
python3 find_instances.py -e ' snakes? ' eng | python3 find_equivalents.py --features=subsequences swe-x-bible-1917
    83.07  _orm
    46.80  _orm_
    35.06  orm_
    5.27  _ormar_
    4.57  _ormar
```

The root is (correctly) identified as "orm", with possible suffixes. To look
at only the singular instances:

    python3 find_instances.py -e ' snake ' eng | python3 find_instances.py -a -v -e ' orm' swe-x-bible-1917

And for the plural ones:

    python3 find_instances.py -e ' snakes ' eng | python3 find_instances.py -a -v -e ' orm' swe-x-bible-1917

From which you could tentatively conclude that the suffix "-ar" is a plural
marker for this noun in Swedish.

## Performance

This benchmark consists of searching through 1698 Bible translations for
sequences corresponding to Finnish character sequence "hyvä".
The time depends crucially on what types of sequences we look for, and on the
number of processors of the machine, for the numbers below a 12-core Xeon CPU
with hyperthreading was used:

* Words only: 69 seconds
* Words and bigrams: 205 seconds


