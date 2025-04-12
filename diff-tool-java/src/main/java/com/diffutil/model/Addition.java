package com.diffutil.model;

import java.util.List;
import java.util.Optional;

/**
 * Represents an addition in a diff.
 * Compatible with Java 11 (no record keyword).
 */
public final class Addition implements DiffElement {
    private final String content;
    private final Optional<List<Integer>> diffIndices;
    private final Optional<Integer> matchedIndex;
    private final Optional<Boolean> isMoved;
    private final Optional<Integer> originalIndex;
    private final Optional<Integer> newIndex;

    // Private constructor to enforce use of factory methods or specific constructors
    private Addition(String content, Optional<List<Integer>> diffIndices, Optional<Integer> matchedIndex, Optional<Boolean> isMoved, Optional<Integer> originalIndex, Optional<Integer> newIndex) {
        this.content = content;
        this.diffIndices = diffIndices != null ? diffIndices : Optional.empty();
        this.matchedIndex = matchedIndex != null ? matchedIndex : Optional.empty();
        this.isMoved = isMoved != null ? isMoved : Optional.empty();
        this.originalIndex = originalIndex != null ? originalIndex : Optional.empty();
        this.newIndex = newIndex != null ? newIndex : Optional.empty();
    }

    // Constructor for simple addition
    public Addition(String content) {
        this(content, Optional.empty(), Optional.empty(), Optional.empty(), Optional.empty(), Optional.empty());
    }

    // Constructor with diff indices
    public Addition(String content, List<Integer> diffIndices) {
        this(content, Optional.ofNullable(diffIndices), Optional.empty(), Optional.empty(), Optional.empty(), Optional.empty());
    }

     // Constructor with diff indices and match index (for modification pairs)
    public Addition(String content, List<Integer> diffIndices, Integer matchedIndex) {
        this(content, Optional.ofNullable(diffIndices), Optional.ofNullable(matchedIndex), Optional.empty(), Optional.empty(), Optional.empty());
    }

    @Override
    public String getContent() {
        return content;
    }

    @Override
    public ElementType getType() {
        return ElementType.ADDITION;
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
        return isMoved.or(() -> Optional.of(false)); // Default to false if not set
    }

    // Not applicable to Addition
    @Override
    public Optional<Boolean> isCombinedModification() {
        return Optional.of(false);
    }

    @Override
    public Optional<Integer> getCombinedNewIndex() {
        return Optional.empty();
    }

    @Override
    public Optional<Integer> getOriginalIndex() {
        return originalIndex;
    }

    @Override
    public Optional<Integer> getNewIndex() {
        return newIndex;
    }

    // Optional: Add equals(), hashCode(), and toString() if needed for collections etc.
    // For this specific use case, they might not be strictly necessary.
}
