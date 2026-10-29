# collada test data

Notes about the data files used in pycollada's unit tests.

- [Assimp BSD-compatible example files](https://github.com/assimp/assimp/blob/b0987f4513eb8c55d3c1d5a5754ec3a6abe094c1/LICENSE) used to test an edge case were retrieved 11/30/2022
  - earthCylindrical.DAE
  - cube_tristrips.dae

- `bumpmap.dae` is a hand-authored, complete COLLADA 1.4.1 scene with one
  UV-mapped triangle, a diffuse texture and an FCOLLADA `NORMALMAP` extension.
  It is independent of pycollada's serializer. The two accompanying 1x1 RGB
  PNGs contain a brown diffuse color and a flat normal, respectively. These
  fixtures were created for pycollada under the repository's BSD license with
  AI assistance. They were not exported by, or verified in, a separate editor.
