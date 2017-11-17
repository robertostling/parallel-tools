# The MPFile class handles files in the format of the paralleltext repository.
# 
# Metadata is stored in the 'metadata' attribute as a dict, while the actual
# parallel sentences are stored in 'sentences' as an identifier: sentence
# mapping.

import re

class MPFile:
    def __init__(self, filename=None):
        self.metadata = {}
        self.sentences = {}
        if filename is not None:
            self.read(filename)

    def read(self, filename):
        re_metadata = re.compile(r'#\s*([^:]+):\s*(.*)$')
        with open(filename, 'r', encoding='utf-8') as f:
            for i,line in enumerate(f):
                line = line.strip()
                if line.startswith('#'):
                    m = re_metadata.match(line)
                    if m:
                        self.metadata[m.group(1)] = m.group(2)
                else:
                    fields = line.split('\t')
                    if len(fields) == 2:
                        sent_id, sent = fields
                        self.sentences[sent_id] = sent.strip()
                    elif len(fields) < 2:
                        pass
                    else:
                        raise ValueError(
                        'Expected comment or two-column line at %s:%d' % (
                            filename, i+1))
        if 'Closest ISO 639-3' in self.metadata:
            self.metadata['closest ISO 639-3'] = \
                    self.metadata['Closest ISO 639-3']
            del self.metadata['Closest ISO 639-3']

    def make_bitext(self, that):
        common = sorted(
                {k for k,v in self.sentences.items() if v} &
                {k for k,v in that.sentences.items() if v})
        return ([self.sentences[k] for k in common],
                [that.sentences[k] for k in common],
                common)


if __name__ == '__main__':
    import sys
    from pprint import pprint
    mpf = MPFile(sys.argv[1])
    pprint(mpf.metadata)
    print(len(mpf.sentences))

