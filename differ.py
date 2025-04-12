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
    
    # If row lengths are very different, they're less likely to be the same row
    len_diff_factor = min(len(row1), len(row2)) / max(len(row1), len(row2)) if max(len(row1), len(row2)) > 0 else 0
    
    # Check if contents are exactly the same
    if row1 == row2:
        return 1.0  # Exact match should always be preferred
        
    # Calculate how many fields match exactly
    field_matches = sum(1 for f1, f2 in zip(row1, row2) if f1 == f2)
    
    # Take into account the row length - shorter rows match fewer fields
    max_possible_matches = min(len(row1), len(row2))
    
    if max_possible_matches == 0:
        return 0
    
    # Check if first field (ID) matches - give extra weight to ID match
    id_match_bonus = 0.1 if len(row1) > 0 and len(row2) > 0 and row1[0] == row2[0] else 0
    
    # Calculate content fingerprint match (comparing number patterns in the data)
    content_match = 0
    if len(row1) >= 3 and len(row2) >= 3:
        # Compare fingerprints of content after removing punctuation and whitespace
        row1_str = ''.join(str(field) for field in row1[1:])  # Skip ID field
        row2_str = ''.join(str(field) for field in row2[1:])  # Skip ID field
        
        # Calculate character-level similarity as a supplementary measure
        max_str_len = max(len(row1_str), len(row2_str))
        if max_str_len > 0:
            # Count matching characters
            char_matches = 0
            for i in range(min(len(row1_str), len(row2_str))):
                if row1_str[i] == row2_str[i]:
                    char_matches += 1
            content_match = char_matches / max_str_len * 0.2  # Weight of 0.2
    
    # Return percentage of matching fields (0-1) with bonuses for ID match and content similarity
    base_similarity = field_matches / max_possible_matches
    return base_similarity * 0.7 + id_match_bonus + content_match

def find_best_row_matches(rows1, rows2, similarity_threshold=0.5):
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
                
            # Check for exact or near-exact matches with higher threshold
            score = calculate_row_similarity(row1, row2)
            if score > 0.8:  # Higher threshold for the second pass
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
    
    # Build the diff result preserving original order
    results = []
    
    # First add headers if they're identical
    if rows1 and rows2 and rows1[0] == rows2[0]:
        results.append(Unchanged(text1[0]))
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
                    results.append(Unchanged(text1[idx1]))
                else:
                    # Same content but different position
                    # Only mark as moved if they're more than 10 lines apart
                    if abs(idx1 - idx2) > 10:
                        # Far enough to be considered moved
                        # Create with original and new indices (add 1 because line numbers are 1-indexed)
                        results.append(Unchanged(text1[idx1], 
                                              _is_moved=True,
                                              _original_index=idx1 + 1, 
                                              _new_index=idx2 + 1))
                    else:
                        # Too close to be considered moved - treat as unchanged
                        results.append(Unchanged(text1[idx1]))
            else:
                # Modified rows - identify field differences
                diff_indices = identify_row_field_differences(row1, row2)
                
                # Store positions for cross-referencing
                removal_pos = len(results)
                addition_pos = removal_pos + 1
                
                # Add the pair with matched indices
                results.append(Removal(text1[idx1], diff_indices, addition_pos))
                results.append(Addition(text2[idx2], diff_indices, removal_pos))
        else:
            # Row was removed in file2
            results.append(Removal(text1[idx1]))
    
    # Now add any rows from file2 that weren't matched to file1
    for idx2, row2 in enumerate(rows2):
        if idx2 not in processed_idx2:
            # This is a new row in file2
            results.append(Addition(text2[idx2]))
    
    return results

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
