This project is part of an ongoing AI-assisted research workflow for formal mathematics: Lean checks each proof term against its stated assumptions, so a result either holds or it does not.

# De Bruijn–Erdős compactness for graph coloring

This Lean 4 project formalizes the de Bruijn–Erdős compactness theorem for graph coloring and
several stronger consequences. Lean checks the complete proofs against Mathlib. The project has
no proof gaps or custom axioms.

## Verified theorem

For any simple graph `G` and natural number `n`, if every finite induced subgraph of `G` admits an
`n`-coloring, then `G` admits an `n`-coloring:

```lean
theorem SimpleGraph.colorable_of_finite_induced_colorable
    (hfinite : ∀ s : Finset V, (G.induce (↑s : Set V)).Colorable n) :
    G.Colorable n
```

The project also proves compactness for homomorphisms into finite target graphs, arbitrary finite
color palettes, and coloring from finite vertex lists. Its obstruction theorem states that failure
of `n`-colorability has a finite induced witness. If an infinite graph has a positive finite
chromatic number, one of its finite induced subgraphs has the same chromatic number. The final
theorems characterize infinite chromatic number by unbounded finite induced chromatic numbers.

## Claim boundary

The proofs do not construct a non-5-colorable finite unit-distance graph. They do not improve the
known Hadwiger–Nelson bounds or solve Erdős Problem 508. They prove that a finite obstruction must
exist if the plane needs at least six colors.

## Source

N. G. de Bruijn and P. Erdős, “A colour problem for infinite graphs and a problem in the theory
of relations,” *Indagationes Mathematicae* 13 (1951), 369–373.

- [Publisher PDF](https://pure.tue.nl/ws/files/4237754/597497.pdf)

## Build and verify

The repository pins Lean and Mathlib. From the repository root:

```sh
lake exe cache get
lake build
python3 scripts/audit.py
```

The audit rebuilds the project, rejects proof-gap and soundness escape tokens in the library
sources, rejects compiler warnings, and checks 21 public declarations for axiom dependencies. The
only permitted dependencies are `Classical.choice`, `propext`, and `Quot.sound`.

## Proof provenance

AI produced the Lean proofs under Egor Lyfar’s direction. Lean’s kernel checks the resulting proof
terms. The source article anchors the mathematical claim.

## Lean Pool

[Lean Pool PR #275](https://github.com/Vilin97/lean-pool/pull/275) carries the same complete theory
for upstream build, quality, and significance review.

## License

Apache-2.0. See [LICENSE](LICENSE).
