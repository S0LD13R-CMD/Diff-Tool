"""Computes diffs of lines."""

from dataclasses import dataclass
from typing import Optional, List, Tuple
import csv
from io import StringIO

@dataclass(frozen=True)
class Addition:
    """Represents an addition in a diff."""
    content: str
    _diff_indices: Optional[List[int]] = None
    _matched_idx: Optional[int] = None  # Index of the matching removal if this is a modified row
    _is_moved: bool = False  # True if this is a row that exists in both files but moved position

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

@dataclass(frozen=True)
class Modification:
    """Represents a modification of a single line."""
    old_content: str
    new_content: str
    diff_indices: List[int]

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

    return mark_segment_changes(list(reversed(results)))

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

def find_best_row_matches(rows1, rows2, similarity_threshold=0.3):
    """Find best matches between rows based on field similarity."""
    matches = []
    used_indices2 = set()
    
    # First phase: find high confidence matches
    for idx1, row1 in enumerate(rows1):
        # Skip completely empty rows
        if not row1 or all(cell.strip() == '' for cell in row1):
            continue
            
        best_match_idx = None
        best_match_score = similarity_threshold  # Only consider matches above threshold
        
        # Find best match for this row
        for idx2, row2 in enumerate(rows2):
            if idx2 in used_indices2:
                continue  # This row is already matched
            
            # Skip completely empty rows    
            if not row2 or all(cell.strip() == '' for cell in row2):
                continue
                
            score = calculate_row_similarity(row1, row2)
            if score > best_match_score:
                best_match_score = score
                best_match_idx = idx2
        
        if best_match_idx is not None:
            matches.append((idx1, best_match_idx, best_match_score))
            used_indices2.add(best_match_idx)
    
    # Second phase: examine remaining unmatched rows and look for potential exact matches
    # that may have been missed due to position differences
    unmatched_indices1 = set(range(len(rows1))) - set(m[0] for m in matches)
    unmatched_indices2 = set(range(len(rows2))) - used_indices2
    
    # Look for potential exact or near-exact matches between remaining unmatched rows
    for idx1 in sorted(unmatched_indices1):
        row1 = rows1[idx1]
        
        # Skip completely empty rows
        if not row1 or all(cell.strip() == '' for cell in row1):
            continue
            
        for idx2 in sorted(unmatched_indices2):
            row2 = rows2[idx2]
            
            # Skip completely empty rows    
            if not row2 or all(cell.strip() == '' for cell in row2):
                continue
                
            # Check for near matches with a lower threshold
            score = calculate_row_similarity(row1, row2)
            if score > 0.2:  # Much lower threshold for the second pass
                matches.append((idx1, idx2, score))
                used_indices2.add(idx2)
                unmatched_indices2.remove(idx2)
                break
            
    # Sort by score descending, to prioritize most confident matches
    matches.sort(key=lambda m: m[2], reverse=True)
    return matches

def identify_row_field_differences(row1, row2):
    """Identify which fields differ between two rows."""
    diff_indices = []
    for idx, (field1, field2) in enumerate(zip(row1, row2)):
        if field1 != field2:
            diff_indices.append(idx)
    
    return diff_indices

def diff_csv(text1, text2):
    """CSV-aware diff that compares rows field-by-field."""
    rows1 = parse_csv_rows(text1)
    rows2 = parse_csv_rows(text2)
    
    # Find best matches between rows
    matches = find_best_row_matches(rows1, rows2)
    
    # Create lookup dictionaries for matched rows
    matched_idx1_to_idx2 = {m[0]: m[1] for m in matches}
    matched_idx2_to_idx1 = {m[1]: m[0] for m in matches}
    
    # Track processed indices from file2
    processed_idx2 = set()
    
    # Build the initial diff result preserving original order
    initial_results = []
    
    # First add headers if they're identical
    if rows1 and rows2 and rows1[0] == rows2[0]:
        initial_results.append(Unchanged(text1[0]))
        processed_idx2.add(0)  # Mark header as processed
    
    # Process all rows from file1 in order
    for idx1, row1 in enumerate(rows1):
        # Skip header if we already added it
        if idx1 == 0 and rows2 and rows1[0] == rows2[0]:
            continue
            
        if idx1 in matched_idx1_to_idx2:
            # This row has a match in file2
            idx2 = matched_idx1_to_idx2[idx1]
            row2 = rows2[idx2]
            processed_idx2.add(idx2)
            
            if row1 == row2:
                # Identical rows - check if they're in same position
                if idx1 == idx2:
                    # Same position - truly unchanged
                    initial_results.append(Unchanged(text1[idx1]))
                else:
                    # Same content but different position
                    # Only mark as moved if they're more than 3 lines apart
                    if abs(idx1 - idx2) > 3:
                        # Far enough to be considered moved
                        results.append(Unchanged(text1[idx1], 
                                              _is_moved=True,
                                              _original_index=idx1 + 1, 
                                              _new_index=idx2 + 1))
                    else:
                        # Too close to be considered moved - treat as unchanged
                        initial_results.append(Unchanged(text1[idx1]))
            else:
                # Initially mark as separate removal and addition
                # Post-processing will merge these if they qualify as a modification
                initial_results.append(Removal(text1[idx1])) 
                initial_results.append(Addition(text2[idx2])) 
        else:
            # Row was removed in file2
            initial_results.append(Removal(text1[idx1]))
    
    # Now add any rows from file2 that weren't matched to file1
    for idx2, row2 in enumerate(rows2):
        if idx2 not in processed_idx2:
            # This is a new row in file2
            initial_results.append(Addition(text2[idx2]))
    
    # Final post-processing pass: look for consecutive removal/addition pairs that are highly similar
    final_results = []
    i = 0
    while i < len(initial_results):
        current_element = initial_results[i]
        next_element = initial_results[i+1] if (i + 1 < len(initial_results)) else None
        
        # Check for Removal followed by Addition
        if (isinstance(current_element, Removal) and 
            isinstance(next_element, Addition)):
            
            removal = current_element
            addition = next_element
            is_modification = False
            diff_indices = []
            
            try:
                removal_row = next(csv.reader([removal.content]))
                addition_row = next(csv.reader([addition.content]))
                
                # Calculate similarity based on field differences
                total_fields = max(len(removal_row), len(addition_row))
                if total_fields > 0: # Avoid division by zero for empty rows
                    matching_fields = 0
                    current_diff_indices = []
                    max_len = max(len(removal_row), len(addition_row))
                    min_len = min(len(removal_row), len(addition_row))

                    for idx in range(min_len):
                        if removal_row[idx] == addition_row[idx]:
                            matching_fields += 1
                        else:
                            current_diff_indices.append(idx)
                    
                    # Fields only in the longer row are also differences
                    num_different_fields = len(current_diff_indices) + (max_len - min_len)
                    
                    match_percentage = matching_fields / max_len
                    
                    # Modification Criteria: >=90% match OR <= 3 differing fields
                    if match_percentage >= 0.9 or num_different_fields <= 3:
                        is_modification = True
                        diff_indices = current_diff_indices
                        # Add indices for fields present only in longer row
                        for idx in range(min_len, max_len):
                            diff_indices.append(idx)
                            
            except (StopIteration, csv.Error):
                # Handle CSV parsing errors
                pass

            # If it qualifies as a modification, add linked pair
            if is_modification:
                removal_pos = len(final_results)
                addition_pos = removal_pos + 1
                
                # Add linked Removal and Addition
                linked_removal = Removal(removal.content, diff_indices, _matched_idx=addition_pos)
                linked_addition = Addition(addition.content, diff_indices, _matched_idx=removal_pos)
                
                final_results.append(linked_removal)
                final_results.append(linked_addition)
                
                i += 2 # Skip both original elements
                continue # Move to the next potential pair

        # If not a modification pair, add the current element
        final_results.append(current_element)
        i += 1
            
    return final_results

def mark_segment_changes(diff_result):
    """Marks which segments differ in matched line pairs.
    
    For each consecutive pair of Removal and Addition, identifies which 
    comma-separated segments differ and marks them with _diff_indices.
    """
    processed_diff = []
    i = 0
    
    while i < len(diff_result):
        # If we're not at the end and have a removal followed by an addition
        if (i < len(diff_result) - 1 and 
            isinstance(diff_result[i], Removal) and 
            isinstance(diff_result[i+1], Addition)):
            
            removal = diff_result[i]
            addition = diff_result[i+1]
            
            # If they don't already have diff_indices, try to determine them
            if not hasattr(removal, '_diff_indices') or removal._diff_indices is None:
                # Split content by comma and compare segments
                removal_segments = removal.content.split(",")
                addition_segments = addition.content.split(",")
                
                # If they have the same number of segments, compare each one
                if len(removal_segments) == len(addition_segments):
                    diff_indices = []
                    for idx, (removal_seg, addition_seg) in enumerate(
                        zip(removal_segments, addition_segments)):
                        if removal_seg.strip() != addition_seg.strip():
                            diff_indices.append(idx)
                    
                    # If we found differences, create new tagged Removal and Addition
                    if diff_indices:
                        # Print for debugging
                        print(f"Found differences at indices {diff_indices}:")
                        print(f"  REMOVAL: {removal.content}")
                        print(f"  ADDITION: {addition.content}")
                        
                        # Create new objects with the diff indices
                        processed_diff.append(Removal(removal.content, diff_indices))
                        processed_diff.append(Addition(addition.content, diff_indices))
                        
                        # Skip both original elements
                        i += 2
                        continue
            
        # If no special handling was applied, just add the current element
        processed_diff.append(diff_result[i])
        i += 1
    
    return processed_diff
