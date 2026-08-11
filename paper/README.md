# Paper source

`main.tex` is the LaTeX source of *Ten new terms for five bishop-graph
sequences, via a bishop-to-rook coordinate reduction*. It is a single
self-contained file: no `.bib`, no figures, standard packages only
(`geometry`, `amsmath`, `amssymb`, `amsthm`, `booktabs`, `microtype`,
`hyperref`).

## Building

Any mainstream TeX distribution works:

```sh
tectonic main.tex        # or: pdflatex main.tex (twice, for references)
```

Last verified with tectonic: exit 0, 9 pages, no overfull boxes and no
undefined references.

## Provenance of the numbers

Every term value in the paper is taken from the staged b-files in
`../OEIS-upload/`, not retyped from prose. The published reach each new term is
measured against comes from `../tools/probe_upstream_bfiles.py`, which reads the
b-file rather than the DATA line — see the correction section of the paper for
why that distinction matters.

Reproduce every claim with `python ../verify_all.py` from the repository root.
