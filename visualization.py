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
    header_row_fields = []
    max_field_count = max(len(fields) for fields in element_fields.values()) if element_fields else 0

    # Check if the header itself was modified (Removal at index 0, Addition at index 1)
    header_modified = False
    if (len(diff) >= 2 and 
        isinstance(diff[0], Removal) and 
        isinstance(diff[1], Addition)):
        # Basic check assumes first R/A pair is header change. Could be more robust.
        header_modified = True

    if header_modified:
        # Use the fields from the new header (Addition at index 1)
        header_row_fields = element_fields.get(1, [])
        print("DEBUG: Header modified, using new header fields:", header_row_fields)
    elif element_fields: # Header not modified, use original logic
        first_row_fields = element_fields.get(0)
        # Try to use first row if it looks like a header, otherwise generate
        if first_row_fields and any(h.lower() in ['id', 'name', 'date', 'col'] for h in first_row_fields if isinstance(h, str)):
             header_row_fields = first_row_fields
             print("DEBUG: Header not modified, using detected header fields:", header_row_fields)
        # else: generate below if needed
    
    # If no specific header fields determined, generate generic ones
    if not header_row_fields:
        header_row_fields = [f'Col_{i+1}' for i in range(max_field_count)]
        print("DEBUG: No specific header found, generating generic headers:", header_row_fields)
    
    # Ensure max_field_count reflects the chosen header, or the max seen
    max_field_count = max(max_field_count, len(header_row_fields))

    # Generate HTML for header cells
    header_cells_html = "\n".join([f'<th>{str(header)}</th>' for header in header_row_fields]) # Ensure header is string
    # -------------------------------------

    # --- HTML Generation --- 
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
            margin: 0; /* Remove default body margin */
            padding: 0; /* Remove default body padding */
        }
        .main-container {
            padding: 20px; /* Add padding to a container div instead */
        }
        table { 
            border-collapse: collapse; 
            width: 100%; 
            background-color: #0d1117;
            border-color: #30363d;
            margin-top: 0; /* Remove potential top margin */
        }
        th, td { 
            border: 1px solid #30363d; 
            padding: 8px; 
            text-align: left; 
        }
        th { 
            background-color: #161b22; 
            color: #c9d1d9;
            position: sticky;
            top: 0;
            z-index: 10;
            border-color: #30363d;
        }
        /* Apply background color to all cells except the first three cells (status and index columns) */
        tr.addition td:not(:nth-child(-n+3)) { background-color: rgba(46, 160, 67, 0.15); }
        tr.removal td:not(:nth-child(-n+3)) { background-color: rgba(248, 81, 73, 0.15); }
        
        /* Status column and line number columns should keep their background for ALL row types */
        tr td.status-col, tr td.line-num {
            background-color: #161b22 !important;
            border-color: #30363d;
        }
        
        /* For modified rows, don't apply background highlighting */
        tr.modified td {
            background-color: transparent;
        }
        
        /* Status text colors */
        .addition-text { color: #3fb950; }
        .removal-text { color: #f85149; }
        .modified-text { color: #d29922; }
        .unchanged { color: #c9d1d9; }
        
        /* Center-aligned columns */
        .center-align {
            text-align: center;
        }
        
        /* Status column styling */
        .status-col {
            background-color: #161b22;
            min-width: 80px;
            text-align: center;
            font-weight: bold;
            user-select: none;
            border-right: none; /* No right border to merge with index */
            border-color: #30363d;
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
            border-color: #30363d;
        }
        /* Remove right border from first index column */
        .line-num-left {
            border-right: none;
            text-align: right;
            padding-right: 6px;
            border-left: none; /* Remove border with status column */
            border-color: #30363d;
        }
        /* Remove left border from second index column */
        .line-num-right {
            border-left: none;
            text-align: left;
            padding-left: 6px;
            border-color: #30363d;
        }
        
        /* Index header with centered text in table header */
        .index-header {
            text-align: center !important;
            padding: 8px 0;
            border-left: none; /* Remove border with status header */
            border-color: #30363d;
        }
        
        .arrow { color: #8b949e; padding: 0 5px; }
        
        .row-id { font-weight: bold; }
        
        .file-header { 
            font-weight: bold; 
            background-color: #161b22;
            color: #c9d1d9;
            border-color: #30363d;
        }

        /* Empty cell styling */
        .empty-cell {
            color: #6e7681;
            font-style: italic;
        }
        
        /* Style for truly empty cells - visible when (empty) text is hidden */
        /* .truly-empty { ... } removed as it was empty */
        
        /* Force all borders to be #30363d */
        * {
            border-color: #30363d !important;
        }

        /* Toggle button styling */
        .toggle-container {
            position: sticky;
            top: 0;
            padding: 10px 20px; /* Add horizontal padding */
            background-color: #0d1117;
            z-index: 100;
            /* margin-bottom: 15px; Removed, table margin handles spacing */
            border-bottom: 1px solid #30363d;
            width: 100%; /* Ensure full width */
            box-sizing: border-box; /* Include padding in width calculation */
        }

        /* First row sticky styling */
        tr:first-child {
            position: sticky;
            top: 55px; /* Adjust position below toggle button height */
            background-color: #000000; /* Black background */
            z-index: 50;
        }
        
        /* Make sticky header cells black */
        tr:first-child td {
            background-color: #000000 !important; 
            color: #e0e0e0; /* Slightly lighter text for contrast */
        }
        
        /* Keep status column styling consistent in sticky header */
        tr:first-child td.status-col {
            background-color: #000000 !important;
            color: inherit; /* Inherit color from parent td */
        }
        
        /* Keep index column styling consistent */
         tr:first-child td.line-num {
             background-color: #000000 !important;
             color: #8b949e; /* Keep original grey for indices */
         }
         
         /* Adjust color specifically for line number text in colored states */
         tr:first-child td.addition-text, tr:first-child td.removal-text, tr:first-child td.modified-text {
             color: #8b949e !important; /* Override status colors for indices */
         }

        .toggle-button {
            background-color: #238636;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-family: monospace;
        }

        .toggle-button:hover {
            background-color: #2ea043;
        }
    </style>
    <script>
        function toggleEmptyCells() {
            const emptyCells = document.querySelectorAll('.empty-cell');
            const button = document.getElementById('toggle-button');
            
            // Toggle visibility
            for (const cell of emptyCells) {
                if (cell.style.display === 'none') {
                    cell.style.display = 'inline';
                    button.textContent = 'Hide (empty) Labels';
                    
                    // No need to modify parent cell styling since we want consistent backgrounds
                } else {
                    cell.style.display = 'none';
                    button.textContent = 'Show (empty) Labels';
                    
                    // No need to modify parent cell styling since we want consistent backgrounds
                }
            }
        }
        
        // Initialize on page load
        window.addEventListener('DOMContentLoaded', (event) => {
            // Start with empty cells visible by default
            document.getElementById('toggle-button').textContent = 'Hide (empty) Labels';
        });
    </script>
</head>
<body>
    <div class="toggle-container">
        <button id="toggle-button" class="toggle-button" onclick="toggleEmptyCells()">Hide (empty) Labels</button>
    </div>
    <div class="main-container"> 
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
        # --- Skip rendering the original header row in the data body ---
        if element.get('original_index') == 0: 
            # Check if the first element is the header, assuming header is always at original index 0
            # This prevents duplicating the header row shown in the sticky thead
            continue 
        # --------------------------------------------------------------

        element_type = element['type']
        row_class = element_type # Use type directly as class (e.g., 'modified', 'addition')
        html_content.append(f'<tr class="{row_class}">\n')
        
        # Status column
        status_text = element_type.capitalize()
        status_class = f"{element_type}-text" # e.g., modified-text
        html_content.append(f'<td class="status-col {status_class}">{status_text}</td>\n')
        
        # Line numbers if enabled
        if show_line_numbers:
            orig_num_display = element.get('line_num_orig', '')
            mod_num_display = element.get('line_num_mod', '')
            
            orig_class = "removal-text" if element_type in ['removal', 'modified'] else ""
            mod_class = "addition-text" if element_type in ['addition', 'modified'] else ""
            
            html_content.append(f'<td class="line-num line-num-left center-align {orig_class}">{orig_num_display}</td>\n')
            html_content.append(f'<td class="line-num line-num-right center-align {mod_class}">{mod_num_display}</td>\n')
        
        # Field content
        if element_type == 'modified':
            for field in element['merged_fields']:
                if field['changed']:
                    old_display = f'<span class="empty-cell">(empty)</span>' if field["old"] == '' else field["old"]
                    new_display = f'<span class="empty-cell">(empty)</span>' if field["new"] == '' else field["new"]
                    html_content.append(f'<td><span class="removal-text">{old_display}</span> <span class="arrow">-></span> <span class="addition-text">{new_display}</span></td>\n')
                else:
                    value = field.get("value", "")
                    display = f'<span class="empty-cell">(empty)</span>' if value == '' else value
                    html_content.append(f'<td>{display}</td>\n')
            # Add empty cells if needed
            for _ in range(max_field_count - len(element['merged_fields'])):
                html_content.append('<td></td>\n')
        else:
            fields_to_display = element.get('fields', [])
            for field in fields_to_display:
                display = f'<span class="empty-cell">(empty)</span>' if field == '' else field
                html_content.append(f'<td>{display}</td>\n')
            # Add empty cells if needed
            for _ in range(max_field_count - len(fields_to_display)):
                html_content.append('<td></td>\n')
        
        html_content.append('</tr>\n')
    
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

    processed_indices = set()
    display_elements = []
    element_fields = {}
    temp_pos_data = {} # Dictionary to store temporary position data

    # --- Pass 1: Calculate Correct Line Numbers & Parse Fields ---
    original_pos_counter = 1
    modified_pos_counter = 1
    for i, element in enumerate(diff):
        current_original_pos = None
        current_modified_pos = None

        # Determine line numbers based on element type
        if isinstance(element, Removal):
            current_original_pos = original_pos_counter
            original_pos_counter += 1
        elif isinstance(element, Addition):
            current_modified_pos = modified_pos_counter
            modified_pos_counter += 1
        elif isinstance(element, Unchanged):
            current_original_pos = original_pos_counter
            current_modified_pos = modified_pos_counter
            original_pos_counter += 1
            modified_pos_counter += 1

        # Store position info in the dictionary
        temp_pos_data[i] = {
            'orig': current_original_pos,
            'mod': current_modified_pos
        }
        
        # Parse fields (remains the same)
        try:
            with StringIO(element.content) as f:
                reader = csv.reader(f)
                fields = next(reader)
                element_fields[i] = fields
        except (StopIteration, csv.Error):
            element_fields[i] = element.content.split(',')

    # Determine max field count
    max_field_count = 0
    for fields in element_fields.values():
        max_field_count = max(max_field_count, len(fields))

    # --- Pass 2: Build Display Elements, Pairing Modifications ---
    for i, element in enumerate(diff):
        if i in processed_indices:
            continue

        # Retrieve correctly calculated position data
        line_num_orig = temp_pos_data[i].get('orig') # Use .get for safety
        line_num_mod = temp_pos_data[i].get('mod')  # Use .get for safety

        # --- Modification Handling (using _matched_idx) ---
        # Check if it's a Removal AND has a valid _matched_idx
        if isinstance(element, Removal) and hasattr(element, '_matched_idx') and element._matched_idx is not None:
            # _matched_idx stores the index of the corresponding Addition in the *current* diff list
            linked_addition_index = element._matched_idx 
            
            # --- Corrected Logic --- 
            # Check if the linked index is valid and points to a corresponding Addition
            if (linked_addition_index < len(diff) and 
                isinstance(diff[linked_addition_index], Addition) and
                hasattr(diff[linked_addition_index], '_matched_idx') and
                diff[linked_addition_index]._matched_idx == i):
                
                # Valid modification pair found!
                addition = diff[linked_addition_index]
                processed_indices.add(linked_addition_index) # Mark addition index as processed
                
                # Retrieve addition's modified position from temp data using its original index
                # NOTE: temp_pos_data uses the original index 'i' for the removal,
                # and 'linked_addition_index' for the addition.
                line_num_mod = temp_pos_data.get(linked_addition_index, {}).get('mod')
                
                # --- Create 'modified' display element --- 
                removal_fields = element_fields.get(i, [])
                addition_fields = element_fields.get(linked_addition_index, [])
                merged_fields = []
                max_local_len = max(len(removal_fields), len(addition_fields))
                # Get diff indices from Removal (they should be the same for the linked Addition)
                diff_indices = getattr(element, '_diff_indices', []) 

                for field_idx in range(max_local_len):
                    old_val = removal_fields[field_idx] if field_idx < len(removal_fields) else ''
                    new_val = addition_fields[field_idx] if field_idx < len(addition_fields) else ''
                    # Use diff_indices to mark change accurately
                    changed = field_idx in diff_indices 
                    merged_fields.append({
                        'old': old_val, 'new': new_val, 'changed': changed,
                        'value': new_val 
                    })
                
                display_elements.append({
                    'type': 'modified',
                    'line_num_orig': line_num_orig, 
                    'line_num_mod': line_num_mod,  
                    'merged_fields': merged_fields,
                    'original_index': i # Keep original index for sorting
                })
                processed_indices.add(i) # Mark removal index as processed
                continue # Skip to next element in outer loop
            # --- End Corrected Logic ---
            else:
                 # If the link is invalid for some reason, fall through to treat as standalone Removal
                 print(f"Warning: Invalid link found for Removal at index {i}. Linked index: {linked_addition_index}")
                 pass

        # --- Handling Standalone or Unmatched Elements ---
        # Additions are only added if they haven't been processed as part of a modification
        if isinstance(element, Addition):
            if i not in processed_indices:
                display_elements.append({
                    'type': 'addition',
                    'line_num_orig': None, 
                    'line_num_mod': line_num_mod,
                    'fields': element_fields.get(i, []),
                    'original_index': i 
                })
                processed_indices.add(i)
        # Removals are only added if they haven't been processed as part of a modification
        elif isinstance(element, Removal):
            if i not in processed_indices:
                display_elements.append({
                    'type': 'removal',
                    'line_num_orig': line_num_orig,
                    'line_num_mod': None, 
                    'fields': element_fields.get(i, []),
                    'original_index': i
                })
                processed_indices.add(i)
        elif isinstance(element, Unchanged):
            # Unchanged are always added
            display_elements.append({
                'type': 'unchanged',
                'line_num_orig': line_num_orig,
                'line_num_mod': line_num_mod,
                'fields': element_fields.get(i, []),
                'original_index': i
            })
            processed_indices.add(i)

    # --- Sort Display Elements by Original Position --- 
    # Use original_index as the primary key for stable sorting based on input order
    # Fallback to line_num_orig only if needed (though original_index should be sufficient)
    display_elements.sort(key=lambda x: x.get('original_index')) 

    # --- Calculate Counts for Info Section ---
    added_rows = 0
    removed_rows = 0
    modified_cells = 0
    for element in display_elements:
        if element['type'] == 'addition':
            added_rows += 1
        elif element['type'] == 'removal':
            removed_rows += 1
        elif element['type'] == 'modified':
            # Count changed fields within this modified row
            for field in element.get('merged_fields', []):
                if field.get('changed', False):
                    modified_cells += 1
    # --------------------------------------

    # Extract source file name from arguments if available
    source_file = "Original File"
    try:
        import sys
        if len(sys.argv) > 1:
            source_file = os.path.basename(sys.argv[1])
    except:
        pass

    # --- Determine Header Row for HTML (Improved for header changes) --- 
    header_row_fields = []
    max_field_count = max(len(fields) for fields in element_fields.values()) if element_fields else 0

    # Check if the header itself was modified (Removal at index 0, Addition at index 1)
    header_modified = False
    if (len(diff) >= 2 and 
        isinstance(diff[0], Removal) and 
        isinstance(diff[1], Addition)):
        # Basic check assumes first R/A pair is header change. Could be more robust.
        header_modified = True

    if header_modified:
        # Use the fields from the new header (Addition at index 1)
        header_row_fields = element_fields.get(1, [])
        print("DEBUG: Header modified, using new header fields:", header_row_fields)
    elif element_fields: # Header not modified, use original logic
        first_row_fields = element_fields.get(0)
        # Try to use first row if it looks like a header, otherwise generate
        if first_row_fields and any(h.lower() in ['id', 'name', 'date', 'col'] for h in first_row_fields if isinstance(h, str)):
             header_row_fields = first_row_fields
             print("DEBUG: Header not modified, using detected header fields:", header_row_fields)
        # else: generate below if needed
    
    # If no specific header fields determined, generate generic ones
    if not header_row_fields:
        header_row_fields = [f'Col_{i+1}' for i in range(max_field_count)]
        print("DEBUG: No specific header found, generating generic headers:", header_row_fields)
    
    # Ensure max_field_count reflects the chosen header, or the max seen
    max_field_count = max(max_field_count, len(header_row_fields))

    # Generate HTML for header cells
    header_cells_html = "\n".join([f'<th>{str(header)}</th>' for header in header_row_fields]) # Ensure header is string
    # -------------------------------------

    # --- HTML Generation --- 
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>CSV Diff Results</title>
        <style>
            body {{ 
                font-family: monospace; 
                background-color: #0d1117; 
                color: #c9d1d9; 
                margin: 0;
                padding: 0;
            }}
            .main-container {{
                padding: 20px; 
            }}
            table {{ 
                border-collapse: collapse; 
                width: 100%; 
                background-color: #0d1117;
                border-color: #30363d;
                margin-top: 0; 
            }}
            th, td {{ 
                border: 1px solid #30363d; 
                padding: 8px; 
                text-align: left; 
            }}
            th {{
                background-color: #161b22; 
                color: #c9d1d9;
                position: sticky;
                /* Adjust sticky top based on toggle container height */
                top: 55px; /* Height of toggle container */ 
                z-index: 10;
                border-color: #30363d;
            }}
            tr.addition td:not(:nth-child(-n+3)) {{ background-color: rgba(46, 160, 67, 0.15); }}
            tr.removal td:not(:nth-child(-n+3)) {{ background-color: rgba(248, 81, 73, 0.15); }}
            
            tr td.status-col, tr td.line-num {{
                background-color: #161b22 !important;
                border-color: #30363d;
            }}
            tr.modified td {{
                background-color: transparent;
            }}
            .addition-text {{ color: #3fb950; }}
            .removal-text {{ color: #f85149; }}
            .modified-text {{ color: #d29922; }}
            .unchanged {{ color: #c9d1d9; }}
            .center-align {{
                text-align: center;
            }}
            .status-col {{
                background-color: #161b22;
                min-width: 80px;
                text-align: center;
                font-weight: bold;
                user-select: none;
                border-right: none; 
                border-color: #30363d;
            }}
            .line-num {{ 
                color: #8b949e; 
                min-width: 30px; 
                max-width: 40px;
                user-select: none;
                background-color: #161b22;
                padding-left: 4px;
                padding-right: 4px;
                border-color: #30363d;
            }}
            .line-num-left {{
                border-right: none;
                text-align: right;
                padding-right: 6px;
                border-left: none; 
                border-color: #30363d;
            }}
            .line-num-right {{
                border-left: none;
                text-align: left;
                padding-left: 6px;
                border-color: #30363d;
            }}
            .index-header {{
                text-align: center !important;
                padding: 8px 0;
                border-left: none; 
                border-color: #30363d;
            }}
            .arrow {{ color: #8b949e; padding: 0 5px; }}
            .row-id {{ font-weight: bold; }}
            .file-header {{ 
                font-weight: bold; 
                background-color: #161b22;
                color: #c9d1d9;
                border-color: #30363d;
            }}
            .empty-cell {{
                color: #6e7681;
                font-style: italic;
            }}
            * {{ border-color: #30363d !important; }}

            /* Toggle container - now using flex */
            .toggle-container {{
                position: sticky;
                top: 0;
                padding: 10px 20px; 
                background-color: #0d1117; 
                z-index: 100;
                border-bottom: 1px solid #30363d;
                width: 100%; 
                box-sizing: border-box; 
                display: flex; /* Use flexbox */
                align-items: center; /* Vertically align items */
                justify-content: space-between; /* Space out button and info */
                min-height: 55px; /* Ensure minimum height for sticky header positioning */
            }}

            /* Info Section Styling */
            .info-section {{
                color: #8b949e; /* Grey text */
                font-size: 14px;
            }}
            .info-section span {{
                margin-left: 15px; /* Space between info items */
            }}
            .info-added {{ color: #3fb950; font-weight: bold; }}
            .info-removed {{ color: #f85149; font-weight: bold; }}
            .info-modified {{ color: #d29922; font-weight: bold; }}

            /* Updated Toggle button styling */
            .toggle-button {{
                background-color: #30363d; /* Grey background */
                color: #c9d1d9; /* Light grey text */
                border: 1px solid #8b949e; /* Slightly lighter border */
                padding: 8px 16px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                font-family: monospace;
            }}
            .toggle-button:hover {{
                background-color: #484f58; /* Slightly lighter grey on hover */
                border-color: #c9d1d9;
            }}

            /* == Sticky Table Header Row Styles == */
            /* Target the first row within the tbody */
            tbody tr:first-child th {{
                position: sticky;
                /* Position below the .toggle-container (height: 55px) */
                top: 55px; 
                background-color: #000000 !important; /* Black background */
                color: #e0e0e0 !important; /* Lighter text for contrast */
                z-index: 50; /* Below toggle-container but above table body */
            }}
            /* Keep status column consistent in sticky header */
            tbody tr:first-child th.status-col {{
                 background-color: #000000 !important;
                 /* Inherit color or set explicitly if needed */
            }}
            /* Keep index columns consistent in sticky header */
             tbody tr:first-child th.line-num {{
                 background-color: #000000 !important;
                 color: #8b949e !important; /* Keep original grey for indices */
             }}
             /* Ensure index text color override in sticky header */
             tbody tr:first-child th.line-num.addition-text,
             tbody tr:first-child th.line-num.removal-text,
             tbody tr:first-child th.line-num.modified-text {{
                 color: #8b949e !important; /* Override status colors for indices */
             }}
            /* == End Sticky Table Header Row Styles == */

        </style>
        <script>
            function toggleEmptyCells() {{
                const emptyCells = document.querySelectorAll('.empty-cell');
                const button = document.getElementById('toggle-button');
                for (const cell of emptyCells) {{
                    if (cell.style.display === 'none') {{
                        cell.style.display = 'inline';
                        button.textContent = 'Hide (empty) Labels';
                    }} else {{
                        cell.style.display = 'none';
                        button.textContent = 'Show (empty) Labels';
                    }}
                }}
            }}
            window.addEventListener('DOMContentLoaded', (event) => {{
                document.getElementById('toggle-button').textContent = 'Hide (empty) Labels';
            }});
        </script>
    </head>
    <body>
        <div class="toggle-container">
            <button id="toggle-button" class="toggle-button" onclick="toggleEmptyCells()">Hide (empty) Labels</button>
            <div class="info-section">
                 <span>Added: <span class="info-added">{added_rows}</span></span>
                 <span>Removed: <span class="info-removed">{removed_rows}</span></span>
                 <span>Modified Cells: <span class="info-modified">{modified_cells}</span></span>
            </div>
        </div>
        <div class="main-container"> 
            <table>
                <!-- Ensure the header row is generated within tbody -->
                <tbody>
                    <tr>
                        <!-- Header Cells (using th for semantics) -->
                        <th class="status-col">Status</th>
                        <th class="line-num line-num-left index-header" colspan="2">Line</th> 
                        <!-- Generate header cells for data columns --> 
                        {header_cells_html}
                    </tr>
    """

    # --- HTML Table Body Generation ---
    for element in display_elements:
        # --- Skip rendering the original header row in the data body ---
        if element.get('original_index') == 0: 
            # Check if the first element is the header, assuming header is always at original index 0
            # This prevents duplicating the header row shown in the sticky thead
            continue 
        # --------------------------------------------------------------

        element_type = element['type']
        row_class = element_type # Use type directly as class (e.g., 'modified', 'addition')
        html_content += f'<tr class="{row_class}">\n'
        
        # Status column
        status_text = element_type.capitalize()
        status_class = f"{element_type}-text" # e.g., modified-text
        html_content += f'<td class="status-col {status_class}">{status_text}</td>\n'
        
        # Line numbers if enabled
        if show_line_numbers:
            orig_num_display = element.get('line_num_orig', '')
            mod_num_display = element.get('line_num_mod', '')
            
            orig_class = "removal-text" if element_type in ['removal', 'modified'] else ""
            mod_class = "addition-text" if element_type in ['addition', 'modified'] else ""
            
            html_content += f'<td class="line-num line-num-left center-align {orig_class}">{orig_num_display}</td>\n'
            html_content += f'<td class="line-num line-num-right center-align {mod_class}">{mod_num_display}</td>\n'
        
        # Field content
        if element_type == 'modified':
            for field in element['merged_fields']:
                if field['changed']:
                    old_display = f'<span class="empty-cell">(empty)</span>' if field["old"] == '' else field["old"]
                    new_display = f'<span class="empty-cell">(empty)</span>' if field["new"] == '' else field["new"]
                    html_content += f'<td><span class="removal-text">{old_display}</span> <span class="arrow">-></span> <span class="addition-text">{new_display}</span></td>\n'
                else:
                    value = field.get("value", "")
                    display = f'<span class="empty-cell">(empty)</span>' if value == '' else value
                    html_content += f'<td>{display}</td>\n'
            # Add empty cells if needed
            for _ in range(max_field_count - len(element['merged_fields'])):
                html_content += '<td></td>\n'
        else:
            fields_to_display = element.get('fields', [])
            for field in fields_to_display:
                display = f'<span class="empty-cell">(empty)</span>' if field == '' else field
                html_content += f'<td>{display}</td>\n'
            # Add empty cells if needed
            for _ in range(max_field_count - len(fields_to_display)):
                html_content += '<td></td>\n'
        
        html_content += '</tr>\n'
    
    # --- HTML Closing --- 
    html_content += """
                </tbody>
            </table>
        </div> 
    </body>
    </html>
    """
    
    # Write to file
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"\nHTML diff output saved to {output_file}\n")
    
    return output_file
