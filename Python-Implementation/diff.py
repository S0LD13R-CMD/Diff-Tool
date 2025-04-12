"""A tool for diffing two given files.

Example usage:
    $ python3 diff.py file1.txt file2.txt

There are also some optional flags below.
"""

from argparse import ArgumentParser
from differ import diff
from visualization import visualize_unified, visualize_unified_html, visualize_unified_spreadsheet_html

def _setup_arg_parser():
    """Sets up the command line argument parser."""
    parser = ArgumentParser(description="A tool for diffing.")

    parser.add_argument("file1", help="The original file to diff.")
    parser.add_argument("file2", help="The updated file to diff.")

    parser.add_argument("--show_line_numbers",
                        default=True,
                        action='store_true',
                        help="If set, line numbers are shown.")
    parser.add_argument("--hide_line_numbers",
                        default=False,
                        action='store_true',
                        help="If set, hide line numbers.")
    parser.add_argument("--html_output",
                        default=True,
                        action='store_true',
                        help="If set, generates an HTML file with the diff results.")
    parser.add_argument("--console_output",
                        default=False,
                        action='store_true',
                        help="If set, outputs diff results to console instead of HTML.")
    parser.add_argument("--output_file",
                        default="diff_output.html",
                        help="The name of the output HTML file (if using HTML output).")
    parser.add_argument("--simple_html",
                        default=False,
                        action='store_true',
                        help="If set, generates a simpler HTML view without spreadsheet formatting.")

    return parser

def _read_lines_from_file(path):
    """Returns the lines without trailing new lines read from the given path."""
    with open(path, 'r') as f:
        return [line for line in f.read().splitlines()]

def main():
    args = _setup_arg_parser().parse_args()

    lines1 = _read_lines_from_file(args.file1)
    lines2 = _read_lines_from_file(args.file2)

    diff_result = diff(lines1, lines2)

    # Override show_line_numbers if hide_line_numbers is specified
    show_line_numbers = args.show_line_numbers and not args.hide_line_numbers

    if args.console_output:
        # Console unified view
        visualize_unified(diff_result, show_line_numbers)
    else:
        # Default to HTML output
        if args.simple_html:
            # Unified HTML view (non-spreadsheet)
            visualize_unified_html(diff_result, show_line_numbers, args.output_file)
        else:
            # Default to spreadsheet-like HTML view
            visualize_unified_spreadsheet_html(diff_result, show_line_numbers, args.output_file)

if __name__ == '__main__':
    main()
