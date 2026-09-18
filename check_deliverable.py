#!/usr/bin/env python3
"""
Pre-delivery check for Cobalt IMA deliverables.

Catches the three failure modes that survive line-editing, because all of them
live in slots that are not body text:

  1. Stale terminology  — "Roadmap" in a title slot.
  2. Unfilled placeholder — [bracketed] template text shipped to a client. This
     is the failure mode a neutral template creates, and the one that embarrasses.
  3. Prior-client residue — a name carried over from another client's file.

    python3 check_deliverable.py Client_Impact_Measurement_Assessment_Sept2026.docx
    python3 check_deliverable.py index.html

If the product name differs from the company name, name it so it is not read as
residue from another client:

    python3 check_deliverable.py index.html --mine SELweb
"""
import sys, os, re, zipfile

# "Roadmap" is legitimate for the follow-on engagement, so it is only an error
# in a title/metadata slot. These patterns target those slots specifically.
TITLE_SLOT_PATTERNS = [
    (r'IMPACT MEASUREMENT ROADMAP',            'cover title'),
    (r'Impact Measurement Roadmap',            'title / running header / cover label'),
    (r'<title>[^<]*Roadmap',                   'HTML <title>'),
    (r'cover-label"[^>]*>[^<]*Roadmap',        'HTML cover label'),
    (r"PDF_NAME\s*=\s*'[^']*Roadmap",          'PDF_NAME constant'),
    (r'_Impact_Measurement_Roadmap_',          'filename convention'),
]

PRIOR_CLIENTS = ['Breathe for Change', 'BFC', 'Snorkl', 'Journify', 'Doorman',
                 'Innovamat', 'Derivita', 'M.S.Ed', 'William Jewell',
                 'Human Intelligence', 'Yoga Ed', 'xSEL', 'SELweb']

# Unfilled template placeholders. The template marks every client slot with
# [bracketed prose] saying what belongs there; any that survives into a client
# file is a hard fail. The pattern must NOT match code — JS array literals,
# attribute selectors and CSS pseudo-classes are all bracketed too. Requiring
# interior whitespace plus two real words excludes ['behavior'], [href="#x"],
# [onclick] and [entry.target.id], which is what an earlier, looser version of
# this check wrongly flagged.
PLACEHOLDER_PATTERN = r'\[(?=[^\]\n]*\s)(?=(?:[^\]\n]*[A-Za-z]{3,}){2})[^\]\n]{10,200}\]'

# Files that ARE the template are expected to be full of placeholders.
TEMPLATE_FILENAMES = {'cobalt-ima-template', 'COBALT_IMA_TEMPLATE'}

DOCX_PARTS = ['word/document.xml', 'word/header1.xml', 'word/footer1.xml',
              'word/header2.xml', 'word/footer2.xml', 'docProps/core.xml',
              'docProps/app.xml']


def harvest(path):
    """Return {slot_name: text}. For .docx this includes headers/footers and
    document properties, which is where stale titles actually hide."""
    out = {}
    if path.lower().endswith('.docx'):
        z = zipfile.ZipFile(path)
        names = set(z.namelist())
        for part in DOCX_PARTS:
            if part in names:
                raw = z.read(part).decode('utf-8', 'replace')
                body = ' '.join(re.findall(r'<w:t(?:\s[^>]*)?>(.*?)</w:t>', raw, re.S))
                out[part] = body + ' ' + raw  # raw too, for docProps title fields
    else:
        out[os.path.basename(path)] = open(path, encoding='utf-8', errors='replace').read()
    out['<filename>'] = os.path.basename(path)
    return out


def own_client(slots, extra):
    """Names that belong to THIS document.

    Deliberately NARROW: the <title>, the cover client line, and the filename.
    An earlier version searched the whole document, which let contamination
    exempt itself — a stray 'Breathe for Change' pasted into an xSEL paragraph
    landed inside the identity region and silenced its own warning.

    A product name that differs from the company name (SELweb vs xSEL Labs)
    will not appear in those three slots, so pass it with --mine.
    """
    blob = slots.get('<filename>', '')
    for text in slots.values():
        for pat in [r'<title>([^<]*)</title>', r'cover-client"[^>]*>([^<]*)<']:
            for m in re.finditer(pat, text):
                blob += ' | ' + m.group(1)
    return blob + ' | ' + ' | '.join(extra)


def main(paths, mine_extra=()):
    failures = 0
    for path in paths:
        base = os.path.basename(path)
        parent = os.path.basename(os.path.dirname(os.path.abspath(path)))
        is_template = parent in TEMPLATE_FILENAMES or os.path.splitext(base)[0] in TEMPLATE_FILENAMES
        print(f'\n=== {base} ==={"  (template — placeholder check skipped)" if is_template else ""}')
        slots = harvest(path)
        mine = own_client(slots, mine_extra)
        hits = []
        for slot, text in slots.items():
            for pat, label in TITLE_SLOT_PATTERNS:
                for m in re.finditer(pat, text):
                    hits.append(f'  STALE TERM  [{slot}] {label}: {m.group(0)[:70]!r}')
            if not is_template:
                for m in re.finditer(PLACEHOLDER_PATTERN, text):
                    hits.append(f'  PLACEHOLDER [{slot}] unfilled: {m.group(0)[:80]!r}')
            for client in PRIOR_CLIENTS:
                # Case-insensitive: filenames lowercase the client name.
                if re.search(r'\b' + re.escape(client), mine, re.I):
                    continue          # this document's own client, not residue
                n = len(re.findall(r'\b' + re.escape(client), text))
                if n:
                    hits.append(f'  RESIDUE     [{slot}] prior client {client!r} x{n}')
        # de-duplicate: the raw XML is searched alongside extracted text
        hits = sorted(set(hits))
        if hits:
            failures += 1
            print('\n'.join(hits))
        else:
            print('  clean — no stale terminology, no unfilled placeholders, no residue')
    print()
    if failures:
        print(f'FAIL: {failures} file(s) need attention before delivery.')
        return 1
    print('PASS: safe to deliver.')
    return 0


if __name__ == '__main__':
    args = sys.argv[1:]
    mine_extra = []
    while '--mine' in args:
        i = args.index('--mine')
        mine_extra.append(args[i + 1])
        del args[i:i + 2]
    if not args:
        print(__doc__); sys.exit(2)
    sys.exit(main(args, mine_extra))
