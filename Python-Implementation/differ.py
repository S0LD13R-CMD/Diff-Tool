"""Computes diffs of lines."""

from dataclasses import dataclass
from typing import Optional, List
import csv
from io import StringIO

@dataclass(frozen=True)
class Addition:
    """Represents an addition in a diff."""
    content: str
    _diff_indices: Optional[List[int]] = None
    _matched_idx: Optional[int] = None  # Index of the matching removal if this is a modified row
    _is_moved: bool = False  # True if this is a row that exists in both files but moved position
    _original_index: Optional[int] = None  # Original index in the first file (for moved rows)
    _new_index: Optional[int] = None  # New index in the second file (for moved rows)

@dataclass(frozen=True)
class Removal:
    """Represents a removal in a diff."""
    content: str
    _diff_indices: Optional[List[int]] = None
    _matched_idx: Optional[int] = None  # Index of the matching addition if this is a modified row
    _is_moved: bool = False  # True if this is a row that exists in both files but moved position
    _is_combined_mod: bool = False  # True if this is combined with its addition in the unified view
    _combined_new_index: Optional[int] = None  # Index of the addition in the original diff

@dataclass(frozen=True)
class Unchanged:
    """Represents something unchanged in a diff."""
    content: str
    _is_moved: bool = False  # True if this is a row that exists in both files but moved position
    _original_index: Optional[int] = None  # Original index in the first file (for moved rows)
    _new_index: Optional[int] = None  # New index in the second file (for moved rows)

def _compute_longest_common_subsequence(text1, text2):
    """Computes the longest common subsequence of the two given strings.

    The result is a table where cell (i, j) tells you the length of the
    longest common subsequence of text1[:i] and text2[:j].
    """
    n = len(text1)
    m = len(text2)

    lcs = [[None for _ in range(m + 1)]
                 for _ in range(n + 1)]

    for i in range(0, n + 1):
        for j in range(0, m + 1):
            if i == 0 or j == 0:
                lcs[i][j] = 0
            elif text1[i - 1] == text2[j - 1]:
                lcs[i][j] = 1 + lcs[i - 1][j - 1]
            else:
                lcs[i][j] = max(lcs[i - 1][j], lcs[i][j - 1])

    return lcs

def diff(text1, text2):
    """Computes the optimal diff of the two given inputs.

    The result is a list where all elements are Removals, Additions or
    Unchanged elements.
    """
    # Try to detect if this is a CSV file by checking if most lines have commas
    comma_lines_1 = sum(1 for line in text1 if "," in line)
    comma_lines_2 = sum(1 for line in text2 if "," in line)
    
    # If both files have a high percentage of comma-separated lines, treat as CSV
    if (comma_lines_1 > len(text1) * 0.8 and comma_lines_2 > len(text2) * 0.8):
        return diff_csv(text1, text2)
    
    # Otherwise use the traditional line-based diff
    return diff_traditional(text1, text2)

def diff_traditional(text1, text2):
    """Traditional line-based diff algorithm using LCS."""
    lcs = _compute_longest_common_subsequence(text1, text2)
    results = []

    i = len(text1)
    j = len(text2)

    while i != 0 or j != 0:
        # If we reached the end of text1 (i == 0) or text2 (j == 0), then we
        # just need to print the remaining additions and removals.
        if i == 0:
            results.append(Addition(text2[j - 1]))
            j -= 1
        elif j == 0:
            results.append(Removal(text1[i - 1]))
            i -= 1
        # Otherwise there's still parts of text1 and text2 left. If the
        # currently considered part is equal, then we found an unchanged part,
        # which belongs to the longest common subsequence.
        elif text1[i - 1] == text2[j - 1]:
            results.append(Unchanged(text1[i - 1]))
            i -= 1
            j -= 1
        # In any other case, we go in the direction of the longest common
        # subsequence.
        elif lcs[i - 1][j] <= lcs[i][j - 1]:
            results.append(Addition(text2[j - 1]))
            j -= 1
        else:
            results.append(Removal(text1[i - 1]))
            i -= 1

    return list(reversed(results))

def parse_csv_rows(lines):
    """Parse CSV lines into rows of fields."""
    rows = []
    for line in lines:
        # Use StringIO to simulate a file for the csv reader
        with StringIO(line) as f:
            reader = csv.reader(f)
            try:
                row = next(reader)
                rows.append(row)
            except StopIteration:
                # Empty line
                rows.append([])
    return rows

def calculate_row_similarity(row1, row2):
    """Calculate similarity score between two rows (higher is more similar)."""
    if not row1 or not row2:
        return 0  # Empty rows have no similarity

    # 1. Exact Match
    if row1 == row2:
        return 1.0

    # 2. ID Match (First Column)
    if len(row1) > 0 and len(row2) > 0 and row1[0] == row2[0]:
        # Give a very high score if IDs match, assuming ID is a strong identifier
        return 0.95 

    # 3. Near Match (Few Differences)
    matching_fields = 0
    different_fields_indices = []
    max_len = max(len(row1), len(row2))
    min_len = min(len(row1), len(row2))
    
    for i in range(min_len):
        if row1[i] == row2[i]:
            matching_fields += 1
        else:
            different_fields_indices.append(i)
            
    # Count fields present only in the longer row as differences
    num_different_fields = len(different_fields_indices) + (max_len - min_len)

    if num_different_fields == 1:
        return 0.90
    elif num_different_fields == 2:
        return 0.85
    elif num_different_fields == 3:
        return 0.80
        
    # 4. Percentage Match (Scaled)
    if max_len == 0:
        return 0 # Avoid division by zero if both rows somehow end up empty
        
    match_percentage = matching_fields / max_len
    return match_percentage * 0.7 # Scale down general percentage match

def identify_row_field_differences(row1, row2):
    """Identify which fields differ between two rows."""
    diff_indices = []
    for idx, (field1, field2) in enumerate(zip(row1, row2)):
        if field1 != field2:
            diff_indices.append(idx)
    
    return diff_indices

def diff_csv(text1, text2):
    """CSV-aware diff using LCS for row alignment and post-processing for modifications."""
    rows1 = parse_csv_rows(text1)
    rows2 = parse_csv_rows(text2)
    
    # --- Step 1: Compute LCS on rows ---
    # We treat entire rows (as lists of strings) as the items for LCS
    lcs_table = _compute_longest_common_subsequence(rows1, rows2)
    
    # --- Step 2: Build initial Add/Remove/Unchanged list from LCS table ---
    initial_results = []
    i = len(rows1)
    j = len(rows2)
    
    while i > 0 or j > 0:
        # Check if we should skip the header comparison if they are identical
        # This avoids marking the header as added/removed if only content changed
        is_header_row1 = (i == 1 and rows1[0] == rows2[0]) if (rows1 and rows2) else False
        is_header_row2 = (j == 1 and rows1[0] == rows2[0]) if (rows1 and rows2) else False

        if is_header_row1 and is_header_row2:
             # Both point to identical headers, skip comparison for this iteration
             i -= 1
             j -= 1
             continue
             
        if i > 0 and j > 0 and rows1[i - 1] == rows2[j - 1]:
            # Rows are identical - Unchanged
            # Use original text content for the Unchanged object
            initial_results.append(Unchanged(text1[i - 1]))
            i -= 1
            j -= 1
        elif j > 0 and (i == 0 or lcs_table[i][j - 1] >= lcs_table[i - 1][j]):
            # Row from text2 is not in LCS - Addition
            initial_results.append(Addition(text2[j - 1]))
            j -= 1
        elif i > 0 and (j == 0 or lcs_table[i][j - 1] < lcs_table[i - 1][j]):
            # Row from text1 is not in LCS - Removal
            initial_results.append(Removal(text1[i - 1]))
            i -= 1
        else:
             # Should not happen, but break loop if it does
             print("Error: Unexpected state in LCS traceback")
             break

    # Add header as unchanged if it was identical and skipped
    if rows1 and rows2 and rows1[0] == rows2[0]:
         initial_results.append(Unchanged(text1[0]))

    # Results are built in reverse order, so reverse them
    initial_results.reverse()
    
    # --- Step 3: Post-processing to identify Modifications ---
    final_results = []
    idx = 0
    processed_indices = set() # Keep track of indices used in modification pairs

    while idx < len(initial_results):
        if idx in processed_indices:
            idx += 1
            continue

        current_element = initial_results[idx]

        # Look for adjacent Removal -> Addition sequence
        if (idx + 1 < len(initial_results) and
                isinstance(current_element, Removal) and
                isinstance(initial_results[idx + 1], Addition)):
            
            removal = current_element
            addition = initial_results[idx + 1]
            
            # Parse rows to check for similarity
            try:
                # Use original text lines associated with removal/addition
                removal_row = parse_csv_rows([removal.content])[0]
                addition_row = parse_csv_rows([addition.content])[0]

                # Check similarity (ID match or high similarity)
                similarity_score = calculate_row_similarity(removal_row, addition_row)
                is_id_match = (len(removal_row) > 0 and len(addition_row) > 0 and removal_row[0] == addition_row[0])
                
                # Consider it a modification if ID matches OR similarity is high (e.g., >= 0.8)
                if is_id_match or similarity_score >= 0.8:
                    diff_indices = identify_row_field_differences(removal_row, addition_row)
                    
                    # Link them as a modification pair
                    # Indices point to the *other* element within the final_results list
                    removal_final_idx = len(final_results)
                    addition_final_idx = removal_final_idx + 1
                    
                    linked_removal = Removal(removal.content, diff_indices, _matched_idx=addition_final_idx)
                    linked_addition = Addition(addition.content, diff_indices, _matched_idx=removal_final_idx)
                    
                    final_results.append(linked_removal)
                    final_results.append(linked_addition)
                    
                    # Mark both original indices as processed
                    processed_indices.add(idx)
                    processed_indices.add(idx + 1)
                    idx += 2 # Move past the processed pair
                    continue # Continue to next iteration

            except Exception as e:
                # If parsing or comparison fails, treat as separate R/A
                print(f"Warning: Error processing potential modification at index {idx}: {e}")
                pass # Fall through to default handling

        # Default: Add the element as is if not part of a modification
        final_results.append(current_element)
        processed_indices.add(idx)
        idx += 1

    return final_results
