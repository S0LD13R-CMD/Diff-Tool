package com.diffutil.model;

import java.util.List;
import java.util.Optional;

/**
 * Represents a removal in a diff.
 * Compatible with Java 11.
 */
public final class Removal implements DiffElement {
    private final String content;
    private final Optional<List<Integer>> diffIndices;
    private final Optional<Integer> matchedIndex;
    private final Optional<Boolean> isMoved;
    private final Optional<Boolean> isCombinedMod;
    private final Optional<Integer> combinedNewIndex;
    private final Optional<Integer> originalIndex;
    private final Optional<Integer> newIndex;

    // Private base constructor
    private Removal(String content, Optional<List<Integer>> diffIndices, Optional<Integer> matchedIndex,
                    Optional<Boolean> isMoved, Optional<Boolean> isCombinedMod, Optional<Integer> combinedNewIndex,
                    Optional<Integer> originalIndex, Optional<Integer> newIndex) {
        this.content = content;
        this.diffIndices = diffIndices != null ? diffIndices : Optional.empty();
        this.matchedIndex = matchedIndex != null ? matchedIndex : Optional.empty();
        this.isMoved = isMoved != null ? isMoved : Optional.empty();
        this.isCombinedMod = isCombinedMod != null ? isCombinedMod : Optional.empty();
        this.combinedNewIndex = combinedNewIndex != null ? combinedNewIndex : Optional.empty();
        this.originalIndex = originalIndex != null ? originalIndex : Optional.empty();
        this.newIndex = newIndex != null ? newIndex : Optional.empty();
    }

    // Constructor for simple removal
    public Removal(String content) {
        this(content, Optional.empty(), Optional.empty(), Optional.empty(), Optional.empty(), Optional.empty(), Optional.empty(), Optional.empty());
    }

    // Constructor with diff indices and match index (for modification pairs)
    public Removal(String content, List<Integer> diffIndices, Integer matchedIndex) {
         this(content, Optional.ofNullable(diffIndices), Optional.ofNullable(matchedIndex), Optional.empty(), Optional.empty(), Optional.empty(), Optional.empty(), Optional.empty());
    }

    // Constructor for combined modifications (for console view)
    public Removal(String content, List<Integer> diffIndices, Integer matchedIndex, boolean isCombinedMod, Integer combinedNewIndex) {
        this(content, Optional.ofNullable(diffIndices), Optional.ofNullable(matchedIndex), Optional.empty(), Optional.of(isCombinedMod), Optional.ofNullable(combinedNewIndex), Optional.empty(), Optional.empty());
    }

    @Override
    public String getContent() {
        return content;
    }

    @Override
    public ElementType getType() {
        return ElementType.REMOVAL;
    }

    @Override
    public Optional<List<Integer>> getDiffIndices() {
        return diffIndices;
    }

    @Override
    public Optional<Integer> getMatchedIndex() {
        return matchedIndex;
    }

    @Override
    public Optional<Boolean> isMoved() {
        return isMoved.or(() -> Optional.of(false)); // Default to false
    }

    @Override
    public Optional<Boolean> isCombinedModification() {
        return isCombinedMod.or(() -> Optional.of(false)); // Default to false
    }

    @Override
    public Optional<Integer> getCombinedNewIndex() {
        return combinedNewIndex;
    }

    @Override
    public Optional<Integer> getOriginalIndex() {
        return originalIndex;
    }

    @Override
    public Optional<Integer> getNewIndex() {
        return newIndex;
    }

     // Optional: Add equals(), hashCode(), and toString()
}
