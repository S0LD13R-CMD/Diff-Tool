package main.java.com.diffutil.model;

import java.util.List;
import java.util.Optional;

/**
 * Represents an unchanged line in a diff.
 * Uses Java 16+ Record.
 */
public record Unchanged(
    String content,
    Optional<Boolean> isMoved,
    Optional<Integer> originalIndex,
    Optional<Integer> newIndex
) implements DiffElement {

    // Constructor for simple unchanged line
    public Unchanged(String content) {
        this(content, Optional.empty(), Optional.empty(), Optional.empty());
    }

     // Constructor for moved unchanged line
    public Unchanged(String content, boolean isMoved, Integer originalIndex, Integer newIndex) {
        this(content, Optional.of(isMoved), Optional.ofNullable(originalIndex), Optional.ofNullable(newIndex));
    }

    @Override
    public String getContent() {
        return content;
    }

    @Override
    public ElementType getType() {
        return ElementType.UNCHANGED;
    }

    @Override
    public Optional<List<Integer>> getDiffIndices() {
        return Optional.empty(); // Not applicable
    }

    @Override
    public Optional<Integer> getMatchedIndex() {
        return Optional.empty(); // Not applicable
    }

    @Override
    public Optional<Boolean> isMoved() {
        return isMoved.or(() -> Optional.of(false)); // Default to false
    }

    // Not applicable
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
