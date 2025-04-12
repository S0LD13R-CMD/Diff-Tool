package main.java.com.diffutil.model;

import java.util.List;
import java.util.Optional;

/**
 * Represents an addition in a diff.
 * Uses Java 16+ Record for conciseness, similar to Python dataclass.
 */
public record Addition(
    String content,
    Optional<List<Integer>> diffIndices,
    Optional<Integer> matchedIndex,
    Optional<Boolean> isMoved,
    Optional<Integer> originalIndex, // For potential moved additions
    Optional<Integer> newIndex // For potential moved additions
) implements DiffElement {

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
}
