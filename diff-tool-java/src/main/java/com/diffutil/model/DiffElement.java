package com.diffutil.model;

import java.util.List;
import java.util.Optional;

/**
 * Base interface for elements representing a line in the diff result.
 */
public interface DiffElement {
    String getContent();
    ElementType getType();

    // Optional attributes, mimicking Python's internal attributes
    // Using Optional to handle presence/absence clearly.
    Optional<List<Integer>> getDiffIndices();
    Optional<Integer> getMatchedIndex();
    Optional<Boolean> isMoved();
    Optional<Boolean> isCombinedModification();
    Optional<Integer> getCombinedNewIndex();
    Optional<Integer> getOriginalIndex();
    Optional<Integer> getNewIndex();

    enum ElementType {
        ADDITION, REMOVAL, UNCHANGED
    }
}
