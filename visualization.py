"""Visualizes diffing results."""

import math
from differ import Addition, Removal, Unchanged, Modification

_TERM_CODE_RED = 31
_TERM_CODE_GREEN = 32
_TERM_CODE_YELLOW = 33  # For highlighting changes within lines
_TERM_CODE_BLUE = 34    # For indicating matched but moved rows
_TERM_CODE_PURPLE = 35  # For indicating rows that are moved but unchanged

# Represents a filler block for diff views.
_EMPTY_FILLER_CHANGE = Unchanged("")

def _color(content, term_code):
    """Colors the content using the given Terminal code."""
    return f"\x1b[{term_code}m{content}\x1b[0m"

def _red(content):
    """Colors the text in red."""
    return _color(content, _TERM_CODE_RED)

def _green(content):
    """Colors the text in green."""
    return _color(content, _TERM_CODE_GREEN)

def _yellow(content):
    """Colors the text in yellow."""
    return _color(content, _TERM_CODE_YELLOW)

def _blue(content):
    """Colors the text in blue."""
    return _color(content, _TERM_CODE_BLUE)

def _purple(content):
    """Colors the text in purple."""
    return _color(content, _TERM_CODE_PURPLE)

def _highlight_segments(content, diff_indices):
    """Highlights specific comma-separated segments in the content string."""
    if not diff_indices:
        return content
    
    segments = content.split(',')
    highlighted_segments = []
    
    for i, segment in enumerate(segments):
        if i in diff_indices:
            # Convert to string in case it's a numeric type
            highlighted_segments.append(_yellow(str(segment)))
        else:
            highlighted_segments.append(segment)
    
    return ','.join(highlighted_segments)

def _format_diff_lines(diff, pad=0, show_line_numbers=False, original_diff=None):
    """Formats the lines of a diffing result with lines padded."""
    result = []

    num_digits = math.ceil(math.log(max(1, len(diff)), 10))
    prefix_format = f"[%.{num_digits}d] "

    line_num1 = 1  # For original file
    line_num2 = 1  # For new file
    spacing = " " * 2
    # +1 to account for "+" and "-".
    hidden_spacing = pad + len(spacing) + 1

    for element in diff:
        prefix = ""
        if show_line_numbers:
            if element is _EMPTY_FILLER_CHANGE:
                prefix = " " * len(prefix_format % 0)
            else:
                # Determine which line number to show based on element type
                if isinstance(element, Addition):
                    # For additions, show line number from new file
                    prefix = prefix_format % line_num2
                    if not isinstance(element, Modification):
                        line_num2 += 1
                elif isinstance(element, Removal):
                    # For removals, show line number from original file
                    prefix = prefix_format % line_num1
                    if not isinstance(element, Modification):
                        line_num1 += 1
                elif isinstance(element, Unchanged):
                    # For unchanged lines, the decision is more complex
                    if hasattr(element, '_is_moved') and element._is_moved:
                        if hasattr(element, '_original_index') and element._original_index is not None:
                            # If we have the original index, use it
                            prefix = prefix_format % element._original_index
                        else:
                            # No original index info, use current counter
                            prefix = prefix_format % line_num1
                    else:
                        # Regular unchanged element - use current counters
                        prefix = prefix_format % line_num1
                    
                    # Increment both counters for unchanged lines
                    line_num1 += 1
                    line_num2 += 1

        if isinstance(element, Addition):
            # Check if this is a matched row (partial change)
            is_matched = hasattr(element, '_matched_idx') and element._matched_idx is not None
            
            # Highlight specific segments if diff_indices are present
            if hasattr(element, '_diff_indices') and element._diff_indices:
                content_to_show = _highlight_segments(element.content, element._diff_indices)
                
                if is_matched:
                    # Just show the content with highlighted changes (no green background)
                    result.append(f"{prefix}+{spacing}{content_to_show.ljust(pad)}")
                else:
                    # Full green for unmatched additions
                    result.append(_green(f"{prefix}+{spacing}{content_to_show.ljust(pad)}"))
            else:
                # No specific field highlighting
                result.append(_green(f"{prefix}+{spacing}{element.content.ljust(pad)}"))
        elif isinstance(element, Removal):
            # Check if this is a matched row (partial change)
            is_matched = hasattr(element, '_matched_idx') and element._matched_idx is not None
            
            # Check if this is a combined modification to be displayed on one line
            if hasattr(element, '_is_combined_mod') and element._is_combined_mod:
                # Get both indices
                old_index = line_num1
                if hasattr(element, '_combined_new_index') and original_diff is not None:
                    # Get the addition from the original diff
                    from_index = element._combined_new_index
                    # Create a combined format with both indices
                    old_prefix = prefix_format % old_index
                    # Calculate approximate new index - it may not be exact
                    new_prefix = prefix_format % line_num2
                    combined_prefix = f"{old_prefix}→{new_prefix}"
                    
                    # Get the addition element and its content
                    addition_content = None
                    if from_index < len(original_diff) and isinstance(original_diff[from_index], Addition):
                        addition_content = original_diff[from_index].content
                    
                    # Create a combined display with both the removal and addition content
                    if addition_content:
                        # Build a side-by-side comparison within the same line
                        combined_content = f"{element.content} → {addition_content}"
                        
                        # If there are specific field differences, highlight them
                        if hasattr(element, '_diff_indices') and element._diff_indices:
                            # First highlight the removal part
                            removal_content = _highlight_segments(element.content, element._diff_indices)
                            # Then highlight the addition part
                            addition_content = _highlight_segments(addition_content, element._diff_indices)
                            combined_content = f"{removal_content} → {addition_content}"
                        
                        # Display the combined line with both indices
                        result.append(f"{combined_prefix} ±{spacing}{combined_content.ljust(pad)}")
                    else:
                        # Fall back to normal display if something went wrong
                        result.append(_red(f"{prefix}-{spacing}{element.content.ljust(pad)}"))
                else:
                    # Fall back to normal display
                    result.append(_red(f"{prefix}-{spacing}{element.content.ljust(pad)}"))
                
                # Increment line counter for the addition we're combining
                line_num2 += 1
                
                # Skip this element's normal processing
                continue
            
            # Highlight specific segments if diff_indices are present
            if hasattr(element, '_diff_indices') and element._diff_indices:
                content_to_show = _highlight_segments(element.content, element._diff_indices)
                
                if is_matched:
                    # Just show the content with highlighted changes (no red background)
                    result.append(f"{prefix}-{spacing}{content_to_show.ljust(pad)}")
                else:
                    # Full red for unmatched removals
                    result.append(_red(f"{prefix}-{spacing}{content_to_show.ljust(pad)}"))
            else:
                # No specific field highlighting
                result.append(_red(f"{prefix}-{spacing}{element.content.ljust(pad)}"))
        elif isinstance(element, Unchanged):
            # Check if this row is marked as moved
            if hasattr(element, '_is_moved') and element._is_moved:
                # Show moved rows in purple to make them stand out
                # For unified view, show both original and new indices
                if hasattr(element, '_original_index') and hasattr(element, '_new_index'):
                    # Show both indices
                    original_prefix = prefix_format % element._original_index
                    new_prefix = prefix_format % element._new_index
                    # Combined format: [old→new]
                    display_prefix = f"{original_prefix}" + "→ " + f"{new_prefix}"
                    # Replace the calculated prefix with our custom one
                    result.append(_purple(f"{display_prefix} ~{spacing}{element.content.ljust(pad)}"))
                else:
                    # No indices information available
                    result.append(_purple(f"{prefix}~{spacing}{element.content.ljust(pad)}"))
            else:
                # Regular unchanged row
                result.append(f"{prefix} {spacing}{element.content.ljust(pad)}")
        elif isinstance(element, Modification):
            # Should not reach here as modifications are converted to Addition/Removal pairs
            pass

    return result

def _identify_modifications(diff):
    """Processes a diff list to identify and group modifications.
    
    This is a legacy function that's superseded by the segment-level diffing
    in differ.py, but kept for compatibility with the existing code.
    """
    # The mark_segment_changes in differ.py already does this work
    return diff

def visualize_unified(diff, show_line_numbers):
    """Visualizes a diffing result in a unified view."""
    from differ import Removal  # Import the class to create new instances
    
    # Process the diff to combine modification pairs (removal followed by addition)
    processed_diff = []
    i = 0
    
    while i < len(diff):
        element = diff[i]
        
        # Check for paired modifications (removal followed by addition)
        if (i < len(diff) - 1 and 
            isinstance(element, Removal) and 
            isinstance(diff[i+1], Addition)):
            
            # If they have matched indices pointing to each other
            if (hasattr(element, '_matched_idx') and 
                element._matched_idx is not None and
                element._matched_idx == i+1):
                
                # Create a new Removal with the combined flag set
                new_removal = Removal(
                    content=element.content,
                    _diff_indices=element._diff_indices if hasattr(element, '_diff_indices') else None,
                    _matched_idx=element._matched_idx,
                    _is_moved=element._is_moved if hasattr(element, '_is_moved') else False,
                    _is_combined_mod=True,
                    _combined_new_index=i+1
                )
                
                processed_diff.append(new_removal)
                i += 2  # Skip both elements
                continue
            
        # Regular element - add as is
        processed_diff.append(element)
        i += 1
    
    # Now format the lines
    diff_lines = _format_diff_lines(processed_diff,
                                   show_line_numbers=show_line_numbers,
                                   original_diff=diff)  # Pass the original diff for reference
    
    print("\nShowing field-by-field diff with highlighted changes:\n")
    for line in diff_lines:
        print(line)

def _html_color(content, css_class):
    """Wraps content in a span with the specified CSS class."""
    return f'<span class="{css_class}">{content}</span>'

def _html_red(content):
    """Wraps content in a span with the removal CSS class."""
    return _html_color(content, "removal")

def _html_green(content):
    """Wraps content in a span with the addition CSS class."""
    return _html_color(content, "addition")

def _html_yellow(content):
    """Wraps content in a span with the modified CSS class."""
    return _html_color(content, "modified")

def _html_purple(content):
    """Wraps content in a span with the moved CSS class."""
    return _html_color(content, "moved")

def _html_highlight_segments(content, diff_indices):
    """Highlights specific comma-separated segments in the content string with HTML."""
    if not diff_indices:
        return content
    
    segments = content.split(',')
    highlighted_segments = []
    
    for i, segment in enumerate(segments):
        if i in diff_indices:
            # Convert to string in case it's a numeric type
            highlighted_segments.append(_html_yellow(str(segment)))
        else:
            highlighted_segments.append(segment)
    
    return ','.join(highlighted_segments)

def _html_strikethrough(content):
    """Wraps content in a strikethrough span with the removal CSS class."""
    return f'<span class="removal strikethrough">{content}</span>'

def visualize_unified_html(diff, show_line_numbers, output_file="diff_output.html"):
    """Generates an HTML visualization of the diffing result."""
    from differ import Removal, Addition, Unchanged
    import csv
    from io import StringIO
    
    # Create a dictionary to store rows by their ID
    rows_by_id = {}
    
    # Extract CSV fields from each element for easier processing
    element_fields = {}
    for i, element in enumerate(diff):
        if isinstance(element, (Removal, Addition, Unchanged)):
            with StringIO(element.content) as f:
                reader = csv.reader(f)
                try:
                    fields = next(reader)
                    element_fields[i] = fields
                except StopIteration:
                    element_fields[i] = []  # Empty line
    
    # First pass - collect all rows by ID and track their positions
    for i, element in enumerate(diff):
        if isinstance(element, (Removal, Addition, Unchanged)):
            # Extract ID from the first column (assuming CSV format)
            parts = element.content.split(',')
            if len(parts) > 0:
                row_id = parts[0]
                if row_id not in rows_by_id:
                    rows_by_id[row_id] = []
                # Store the element, its index, and type
                elem_type = 'removal' if isinstance(element, Removal) else 'addition' if isinstance(element, Addition) else 'unchanged'
                rows_by_id[row_id].append({
                    'element': element,
                    'index': i,
                    'type': elem_type
                })
    
    # Build a list of elements to display (with special handling for modified rows)
    display_elements = []
    processed_indices = set()
    
    # First, process elements in their original order
    for i, element in enumerate(diff):
        if i in processed_indices:
            continue
            
        if isinstance(element, Removal):
            # Check if this is part of a modification (has a matching addition with same ID)
            parts = element.content.split(',')
            if len(parts) > 0:
                row_id = parts[0]
                # Find if there's a corresponding addition
                has_matching_addition = False
                addition_index = None
                
                for entry in rows_by_id.get(row_id, []):
                    if entry['type'] == 'addition' and entry['index'] > i:
                        has_matching_addition = True
                        addition_index = entry['index']
                        break
                
                if has_matching_addition and addition_index is not None:
                    # This is a modified row - handle specially
                    addition = diff[addition_index]
                    
                    # Compute the differences
                    removal_fields = element_fields.get(i, [])
                    addition_fields = element_fields.get(addition_index, [])
                    
                    diff_indices = []
                    for idx, (r_field, a_field) in enumerate(zip(removal_fields, addition_fields)):
                        if r_field != a_field:
                            diff_indices.append(idx)
                        
                    # Create a special display element
                    display_elements.append({
                        'type': 'modified',
                        'removal': element,
                        'addition': addition,
                        'diff_indices': diff_indices,
                        'row_id': row_id,
                        'removal_fields': removal_fields,
                        'addition_fields': addition_fields
                    })
                    
                    # Mark both indices as processed
                    processed_indices.add(i)
                    processed_indices.add(addition_index)
                    continue
        
        # If not handled as a special case, add the element as is
        if i not in processed_indices:
            display_elements.append({
                'type': element.__class__.__name__.lower(),
                'element': element,
                'fields': element_fields.get(i, [])
            })
            processed_indices.add(i)
    
    # Get header row (field names)
    header_row = []
    for i, element in enumerate(diff):
        if i in element_fields and element_fields[i] and element_fields[i][0] == 'ID':
            header_row = element_fields[i]
            break
    
    # If we couldn't find a header row with 'ID', use the first row we found
    if not header_row and element_fields:
        for idx in sorted(element_fields.keys()):
            if element_fields[idx]:
                header_row = element_fields[idx]
                break
    
    # HTML content generation
    html_content = []
    
    # Start with the HTML structure and CSS
    html_content.append("""<!DOCTYPE html>
<html>
<head>
    <title>CSV Diff Results</title>
    <style>
        body { 
            font-family: monospace; 
            background-color: #0d1117; 
            color: #c9d1d9; 
            margin: 0;
            padding: 20px;
        }
        table { 
            border-collapse: collapse; 
            width: 100%; 
            background-color: #0d1117;
        }
        th, td { 
            border: 1px solid #30363d; 
            padding: 8px; 
            text-align: left; 
        }
        th { 
            background-color: #161b22; 
            color: #c9d1d9;
        }
        /* Apply background color to all cells except the first three cells (status and index columns) */
        tr.addition td:not(:nth-child(-n+3)) { background-color: rgba(46, 160, 67, 0.15); }
        tr.removal td:not(:nth-child(-n+3)) { background-color: rgba(248, 81, 73, 0.15); }
        /* Status text colors */
        .addition-text { color: #3fb950; }
        .removal-text { color: #f85149; }
        .modified-text { color: #d29922; }
        .unchanged { color: #c9d1d9; }
        /* Center-aligned columns */
        .center-align {
            text-align: center;
        }
        /* Status column styling - match index columns */
        .status-col {
            background-color: #161b22;
            border-right: none;
        }
        
        /* Index column styling */
        .line-num { 
            color: #8b949e; 
            min-width: 30px; 
            max-width: 40px;
            user-select: none;
            background-color: #161b22;
            padding-left: 4px;
            padding-right: 4px;
        }
        /* Remove right border from first index column */
        .line-num-left {
            border-right: none;
            text-align: right;
            padding-right: 6px;
            border-left: none; /* Remove border with status column */
        }
        /* Remove left border from second index column */
        .line-num-right {
            border-left: none;
            text-align: left;
            padding-left: 6px;
        }
        /* Index number divider */
        .index-separator {
            color: #30363d;
            display: inline-block;
            width: 100%;
            text-align: center;
            font-weight: normal;
            position: relative;
        }
        /* Combined column look for the line number header cells */
        .line-num-header {
            border-right: none;
            background-color: #161b22;
            text-align: center;
            padding-right: 0;
        }
        .line-num-header-right {
            border-left: none;
            background-color: #161b22;
            text-align: center;
            padding-left: 0;
        }
        /* Index header with centered text in table header */
        .index-header {
            text-align: center !important;
            padding: 8px 0;
        }
        .arrow { color: #8b949e; padding: 0 5px; }
        .row-id { font-weight: bold; }
        .file-header { 
            font-weight: bold; 
            background-color: #161b22;
            color: #c9d1d9;
        }
    </style>
</head>
<body>
    <div class="title">CSV Diff Results (Unified View)</div>
    <div class="diff-container">
        <table>
            <thead>
                <tr>
                    <th>Line</th>
                    <th>Content</th>
                </tr>
            </thead>
            <tbody>
""")
    
    # Initialize line numbers
    line_num1 = 1  # For original file
    line_num2 = 1  # For new file
    
    # Process each element for display
    for element in display_elements:
        line_html = '<tr>'
        
        # Special handling for modified rows
        if isinstance(element, dict) and element.get('type') == 'modified':
            removal = element['removal']
            addition = element['addition']
            diff_indices = element['diff_indices']
            row_id = element['row_id']
            
            # Show line numbers if requested
            if show_line_numbers:
                # For modified rows, show both line numbers
                line_html += f'<td class="line-number">[{line_num1}→{line_num2}] ±</td>'
                
                # Update counters
                line_num1 += 1
                line_num2 += 1
            else:
                line_html += '<td class="line-number">±</td>'
            
            # Split by comma for CSV
            removal_parts = removal.content.split(',')
            addition_parts = addition.content.split(',')
            
            # Create a table cell with the content
            line_html += '<td>'
            
            # Create row cells
            cells = []
            for idx, (r_part, a_part) in enumerate(zip(removal_parts, addition_parts)):
                if idx in diff_indices:
                    # This field changed - show both old and new values with appropriate coloring
                    cells.append(f'<span class="removal">{r_part}</span> <span class="arrow">→</span> <span class="addition">{a_part}</span>')
                else:
                    # Unchanged field
                    cells.append(a_part)
            
            line_html += ','.join(cells)
            line_html += '</td>'
        else:
            # Normal processing for other elements
            if show_line_numbers:
                if isinstance(element, dict) and element.get('type') == 'addition':
                    line_html += f'<td class="line-number">[{line_num2}] +</td>'
                    line_num2 += 1
                elif isinstance(element, dict) and element.get('type') == 'removal':
                    line_html += f'<td class="line-number">[{line_num1}] -</td>'
                    line_num1 += 1
                elif isinstance(element, dict) and element.get('type') == 'unchanged':
                    elem = element.get('element')
                    if hasattr(elem, '_is_moved') and elem._is_moved:
                        if hasattr(elem, '_original_index') and hasattr(elem, '_new_index'):
                            line_html += f'<td class="line-number">[{elem._original_index}]→[{elem._new_index}] ~</td>'
                        else:
                            line_html += f'<td class="line-number">[{line_num1}] ~</td>'
                    else:
                        line_html += f'<td class="line-number">[{line_num1}]  </td>'
                    
                    line_num1 += 1
                    line_num2 += 1
            else:
                if isinstance(element, dict) and element.get('type') == 'addition':
                    line_html += '<td class="line-number">+</td>'
                elif isinstance(element, dict) and element.get('type') == 'removal':
                    line_html += '<td class="line-number">-</td>'
                elif isinstance(element, dict) and element.get('type') == 'unchanged':
                    elem = element.get('element')
                    if hasattr(elem, '_is_moved') and elem._is_moved:
                        line_html += '<td class="line-number">~</td>'
                    else:
                        line_html += '<td class="line-number"> </td>'
            
            # Format content
            line_html += '<td>'
            if isinstance(element, dict) and element.get('type') == 'addition':
                elem = element.get('element')
                if hasattr(elem, '_diff_indices') and elem._diff_indices:
                    line_html += _html_green(_html_highlight_segments(elem.content, elem._diff_indices))
                else:
                    line_html += _html_green(elem.content)
            elif isinstance(element, dict) and element.get('type') == 'removal':
                elem = element.get('element')
                if hasattr(elem, '_diff_indices') and elem._diff_indices:
                    line_html += _html_red(_html_highlight_segments(elem.content, elem._diff_indices))
                else:
                    line_html += _html_red(elem.content)
            elif isinstance(element, dict) and element.get('type') == 'unchanged':
                elem = element.get('element')
                if hasattr(elem, '_is_moved') and elem._is_moved:
                    line_html += _html_purple(elem.content)
                else:
                    line_html += elem.content
            line_html += '</td>'
        
        line_html += '</tr>'
        html_content.append(line_html)
    
    # Close the HTML
    html_content.append("""
            </tbody>
        </table>
    </div>
</body>
</html>""")
    
    # Write to file
    with open(output_file, 'w') as f:
        f.write('\n'.join(html_content))
    
    print(f"\nHTML diff output saved to {output_file}\n")

def visualize_unified_spreadsheet_html(diff, show_line_numbers, output_file="diff_output_unified_spreadsheet.html"):
    """Generates an HTML visualization of the diffing result in a unified spreadsheet-like format."""
    from differ import Removal, Addition, Unchanged
    import csv
    from io import StringIO
    import os
    
    # Create a dictionary to store rows by their ID
    rows_by_id = {}
    
    # First pass - collect all rows by ID and track their positions
    for i, element in enumerate(diff):
        if isinstance(element, (Removal, Addition, Unchanged)):
            # Extract ID from the first column (assuming CSV format)
            parts = element.content.split(',')
            if len(parts) > 0:
                row_id = parts[0]
                if row_id not in rows_by_id:
                    rows_by_id[row_id] = []
                # Store the element, its index, and type
                elem_type = 'removal' if isinstance(element, Removal) else 'addition' if isinstance(element, Addition) else 'unchanged'
                rows_by_id[row_id].append({
                    'element': element,
                    'index': i,
                    'type': elem_type
                })
    
    # Extract CSV fields from each element for easier processing
    element_fields = {}
    for i, element in enumerate(diff):
        if isinstance(element, (Removal, Addition, Unchanged)):
            with StringIO(element.content) as f:
                reader = csv.reader(f)
                try:
                    fields = next(reader)
                    element_fields[i] = fields
                except StopIteration:
                    element_fields[i] = []  # Empty line
    
    # Determine how many columns we need by finding the max field count
    max_field_count = 0
    for fields in element_fields.values():
        max_field_count = max(max_field_count, len(fields))
    
    # Find the header row (first row from either file)
    header_fields = []
    
    # First try to find a row that has 'ID' as first column in either file
    for idx, fields in sorted(element_fields.items()):
        if fields and fields[0] == 'ID':
            header_fields = fields
            break
    
    # If no ID column found, just use the first row we encounter
    if not header_fields and element_fields:
        first_idx = min(element_fields.keys())
        header_fields = element_fields[first_idx]
    
    # If still no header, use generic field names
    if not header_fields:
        header_fields = [f"Field {i+1}" for i in range(max_field_count)]
    
    # Keep track of row positions in the original file
    original_positions = {}
    modified_positions = {}
    
    # First, build a mapping of row IDs to their positions in each file
    orig_position = 1
    mod_position = 1
    
    # Process the diff to extract all positions first
    for i, element in enumerate(diff):
        if isinstance(element, (Removal, Unchanged)):
            parts = element.content.split(',')
            if parts and len(parts) > 0:
                row_id = parts[0]
                original_positions[row_id] = orig_position
                orig_position += 1
                
                # If unchanged, also track in modified file
                if isinstance(element, Unchanged):
                    modified_positions[row_id] = mod_position
                    mod_position += 1
                
        if isinstance(element, (Addition, Unchanged)):
            parts = element.content.split(',')
            if parts and len(parts) > 0:
                row_id = parts[0]
                if row_id not in modified_positions:
                    modified_positions[row_id] = mod_position
                    mod_position += 1
    
    # Now build the display elements with corrected line numbers
    display_elements = []
    for row_id, elements in rows_by_id.items():
        if len(elements) == 1:
            # Simple case - added or removed or unchanged
            element = elements[0]['element']
            elem_type = elements[0]['type']
            index = elements[0]['index']
            
            if show_line_numbers:
                if elem_type == 'removal':
                    line_num_orig = original_positions.get(row_id, index + 1)
                    line_num_mod = ''
                elif elem_type == 'addition':
                    line_num_orig = ''
                    line_num_mod = modified_positions.get(row_id, index + 1)
                else:  # unchanged
                    line_num_orig = original_positions.get(row_id, index + 1)
                    line_num_mod = modified_positions.get(row_id, index + 1)
            else:
                line_num_orig = line_num_mod = ''
            
            display_elements.append({
                'type': elem_type,
                'line_num_orig': line_num_orig,
                'line_num_mod': line_num_mod,
                'fields': element_fields[index],
                'id': row_id
            })
        elif len(elements) == 2:
            # Modified row - need to show both versions
            removal = None
            addition = None
            for e in elements:
                if e['type'] == 'removal':
                    removal = e
                elif e['type'] == 'addition':
                    addition = e
            
            if removal and addition:
                if show_line_numbers:
                    line_num_orig = original_positions.get(row_id, removal['index'] + 1)
                    line_num_mod = modified_positions.get(row_id, addition['index'] + 1)
                else:
                    line_num_orig = line_num_mod = ''
                
                # Create merged fields to show both versions
                removal_fields = element_fields[removal['index']]
                addition_fields = element_fields[addition['index']]
                
                merged_fields = []
                for i in range(max(len(removal_fields), len(addition_fields))):
                    if i < len(removal_fields) and i < len(addition_fields):
                        old_val = removal_fields[i]
                        new_val = addition_fields[i]
                        if old_val != new_val:
                            merged_fields.append({
                                'old': old_val,
                                'new': new_val,
                                'changed': True
                            })
                        else:
                            merged_fields.append({
                                'value': old_val,
                                'changed': False
                            })
                    elif i < len(removal_fields):
                        merged_fields.append({
                            'old': removal_fields[i],
                            'new': '',
                            'changed': True
                        })
                    elif i < len(addition_fields):
                        merged_fields.append({
                            'old': '',
                            'new': addition_fields[i],
                            'changed': True
                        })
                
                display_elements.append({
                    'type': 'modified',
                    'line_num_orig': line_num_orig,
                    'line_num_mod': line_num_mod,
                    'merged_fields': merged_fields,
                    'id': row_id
                })
    
    # Sort display elements by line number - put all modifications, additions, and removals first
    # Then append unchanged items ordered by their line number
    if show_line_numbers:
        # First, separate changed and unchanged elements
        changed_elements = [e for e in display_elements if e['type'] != 'unchanged']
        unchanged_elements = [e for e in display_elements if e['type'] == 'unchanged']
        
        # Sort changed elements by original line number
        changed_elements.sort(key=lambda x: (
            int(x['line_num_orig']) if isinstance(x['line_num_orig'], str) and x['line_num_orig'].isdigit() 
            else x['line_num_orig'] if isinstance(x['line_num_orig'], int)
            else float('inf')
        ))
        
        # Sort unchanged elements by original line number
        unchanged_elements.sort(key=lambda x: (
            int(x['line_num_orig']) if isinstance(x['line_num_orig'], str) and x['line_num_orig'].isdigit() 
            else x['line_num_orig'] if isinstance(x['line_num_orig'], int)
            else float('inf')
        ))
        
        # Alternatively, interleave them based on original line number
        # This maintains the original document ordering
        display_elements = sorted(display_elements, key=lambda x: (
            int(x['line_num_orig']) if isinstance(x['line_num_orig'], str) and x['line_num_orig'].isdigit() 
            else x['line_num_orig'] if isinstance(x['line_num_orig'], int) 
            else float('inf')
        ))
    
    # Extract source file name from arguments if available
    source_file = "Original File"
    try:
        import sys
        if len(sys.argv) > 1:
            source_file = os.path.basename(sys.argv[1])
    except:
        pass
    
    # Generate HTML
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { 
                font-family: monospace; 
                background-color: #0d1117; 
                color: #c9d1d9; 
                margin: 0;
                padding: 20px;
            }
            table { 
                border-collapse: collapse; 
                width: 100%; 
                background-color: #0d1117;
            }
            th, td { 
                border: 1px solid #30363d; 
                padding: 8px; 
                text-align: left; 
            }
            th { 
                background-color: #161b22; 
                color: #c9d1d9;
            }
            /* Apply background color to all cells except the first three cells (status and index columns) */
            tr.addition td:not(:nth-child(-n+3)) { background-color: rgba(46, 160, 67, 0.15); }
            tr.removal td:not(:nth-child(-n+3)) { background-color: rgba(248, 81, 73, 0.15); }
            /* Status text colors */
            .addition-text { color: #3fb950; }
            .removal-text { color: #f85149; }
            .modified-text { color: #d29922; }
            .unchanged { color: #c9d1d9; }
            /* Center-aligned columns */
            .center-align {
                text-align: center;
            }
            /* Status column styling - match index columns */
            .status-col {
                background-color: #161b22;
                border-right: none;
            }
            
            /* Index column styling */
            .line-num { 
                color: #8b949e; 
                min-width: 30px; 
                max-width: 40px;
                user-select: none;
                background-color: #161b22;
                padding-left: 4px;
                padding-right: 4px;
            }
            /* Remove right border from first index column */
            .line-num-left {
                border-right: none;
                text-align: right;
                padding-right: 6px;
                border-left: none; /* Remove border with status column */
            }
            /* Remove left border from second index column */
            .line-num-right {
                border-left: none;
                text-align: left;
                padding-left: 6px;
            }
            /* Index number divider */
            .index-separator {
                color: #30363d;
                display: inline-block;
                width: 100%;
                text-align: center;
                font-weight: normal;
                position: relative;
            }
            /* Apply a dividing line between the indices */
            .index-separator::after {
                content: "";
                position: absolute;
                top: 50%;
                left: 0;
                right: 0;
                border-top: 1px solid #30363d;
                z-index: 1;
            }
            /* Put the text on top of the line */
            .index-separator span {
                background-color: #161b22;
                position: relative;
                z-index: 2;
                padding: 0 4px;
            }
            /* Combined column look for the line number header cells */
            .line-num-header {
                border-right: none;
                background-color: #161b22;
                text-align: center;
                padding-right: 0;
            }
            .line-num-header-right {
                border-left: none;
                background-color: #161b22;
                text-align: center;
                padding-left: 0;
            }
            /* Index header with centered text in table header */
            .index-header {
                text-align: center !important;
                padding: 8px 0;
            }
            .arrow { color: #8b949e; padding: 0 5px; }
            .row-id { font-weight: bold; }
            .file-header { 
                font-weight: bold; 
                background-color: #161b22;
                color: #c9d1d9;
            }
        </style>
    </head>
    <body>
        <table>
            <thead>
                <tr>
                    <th class="center-align">Status</th>
    """
    
    if show_line_numbers:
        html_content += """
                    <th colspan="2" class="center-align index-header">Index</th>
        """
    
    # Add a single unified header that spans all data columns
    data_columns = max_field_count
    html_content += f'<th colspan="{data_columns}" class="file-header">{source_file}</th>\n'
    
    html_content += """
            </thead>
            <tbody>
    """
    
    for element in display_elements:
        element_type = element['type']
        
        # Apply row class for added and deleted rows (but exclude the status column from highlighting)
        if element_type in ('addition', 'removal'):
            html_content += f'<tr class="{element_type}">\n'
        else:
            html_content += f'<tr>\n'
        
        # Status column with colored text instead of background
        status_text = "Added" if element_type == "addition" else "Removed" if element_type == "removal" else "Modified" if element_type == "modified" else "Unchanged"
        
        # Apply text color classes to status text
        if element_type == "addition":
            html_content += f'<td class="center-align status-col addition-text">{status_text}</td>\n'
        elif element_type == "removal":
            html_content += f'<td class="center-align status-col removal-text">{status_text}</td>\n'
        elif element_type == "modified":
            html_content += f'<td class="center-align status-col modified-text">{status_text}</td>\n'
        else:
            html_content += f'<td class="center-align status-col">{status_text}</td>\n'
        
        # Line numbers if enabled
        if show_line_numbers:
            # Index columns with colored text
            if element_type == "addition":
                html_content += f'<td class="line-num line-num-left center-align"></td>\n'
                html_content += f'<td class="line-num line-num-right center-align addition-text">{element["line_num_mod"]}</td>\n'
            elif element_type == "removal":
                html_content += f'<td class="line-num line-num-left center-align removal-text">{element["line_num_orig"]}</td>\n'
                html_content += f'<td class="line-num line-num-right center-align"></td>\n'
            elif element_type == "modified":
                html_content += f'<td class="line-num line-num-left center-align removal-text">{element["line_num_orig"]}</td>\n'
                html_content += f'<td class="line-num line-num-right center-align addition-text">{element["line_num_mod"]}</td>\n'
            else:
                html_content += f'<td class="line-num line-num-left center-align">{element["line_num_orig"]}</td>\n'
                html_content += f'<td class="line-num line-num-right center-align">{element["line_num_mod"]}</td>\n'
        
        # Handle field content based on element type
        if element_type == 'modified':
            # For modified rows, display both values with different colors
            for i, field in enumerate(element['merged_fields']):
                if 'changed' in field and field['changed']:
                    html_content += f'<td><span class="removal-text">{field["old"]}</span> <span class="arrow">→</span> <span class="addition-text">{field["new"]}</span></td>\n'
                else:
                    html_content += f'<td>{field.get("value", "")}</td>\n'
            
            # Add empty cells to fill up to max fields
            for _ in range(max_field_count - len(element['merged_fields'])):
                html_content += '<td></td>\n'
        else:
            # For additions, removals and unchanged rows
            for i, field in enumerate(element.get('fields', [])):
                html_content += f'<td>{field}</td>\n'
            
            # Add empty cells to fill up to max fields
            for _ in range(max_field_count - len(element.get('fields', []))):
                html_content += '<td></td>\n'
        
        html_content += '</tr>\n'
    
    html_content += """
            </tbody>
        </table>
    </body>
    </html>
    """
    
    # Write to file
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    return output_file
