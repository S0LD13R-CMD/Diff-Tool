# Diffing Tool

Diffing tools show you what changed between two versions of a file.
For example, given these two input files.

## Algorithm

This tool is an *optimal* diffing implementation, meaning it always shows the smallest 
possible number of removal and addition markers.

This is done by computing the *longest common subsequence* for the unchanged parts, i.e.
we maximize the length of the unchanged parts. We implement that using dynamic programming,
with a quadratic complexity. In that recursion, we then also keep track of what is added and
removed.

## Potential improvements

There's some things left that could be improved:

- Packaging this into a tool that could be easily installed
- Char-based diffing as opposed to line-based diffing. The algorithm would stay
  exactly the same. The only thing that would need to be updated is the visualization
- Faster line-based diffing. One could first hash all lines to make comparisons faster
