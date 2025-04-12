package main.java.com.diffutil.model;

import java.util.List;
import java.util.Optional;

/**
 * Represents a removal in a diff.
 * Uses Java 16+ Record.
 */
public record Removal(
    String content,
    Optional<List<Integer>> diffIndices,
    Optional<Integer> matchedIndex,
    Optional<Boolean> isMoved,
    Optional<Boolean> isCombinedMod, // Renamed from Python's _is_combined_mod
    Optional<Integer> combinedNewIndex, // Renamed from Python
    Optional<Integer> originalIndex, // For potential moved removals
    Optional<Integer> newIndex // For potential moved removals
) implements DiffElement {

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
}
