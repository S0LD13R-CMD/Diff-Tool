# Java Diff Tool

This project is a Java implementation of a file diffing tool, similar to the Python version it was derived from.
It supports both standard line-by-line diff and a CSV-aware diff mode.

## Features

*   Compares two text files.
*   Automatically detects likely CSV files and performs row/field-level comparison.
*   Outputs differences to the console or an HTML file.
*   Supports different HTML views (simple, spreadsheet-like).
*   Highlights modified fields within CSV rows in HTML output.

## Prerequisites

*   Java Development Kit (JDK) 11 or higher.
*   Apache Maven (for building).

## Building

Use Maven to compile the project and create an executable JAR:

```bash
mvn clean package
```

This will create a JAR file with dependencies included in the `target/` directory (e.g., `target/diff-tool-java-1.0-SNAPSHOT-jar-with-dependencies.jar`).

## Usage

Run the executable JAR from your terminal:

```bash
java -jar target/diff-tool-java-1.0-SNAPSHOT-jar-with-dependencies.jar <file1> <file2> [options]
```

**Required Arguments:**

*   `<file1>`: Path to the original file.
*   `<file2>`: Path to the updated file.

**Options:**

*   `--simple_html`: Generate simple HTML view instead of spreadsheet view.
*   `--no-html_output`: Output diff results to the console instead of HTML.
*   `--output_file=<fileName>`: Specify the name of the output HTML file (default: `diff_output.html`).
*   `--no-show_line_numbers`: Hide line numbers in the output (default is to show them).
*   `-h`, `--help`: Show help message and exit.
*   `-V`, `--version`: Print version information and exit.

**Examples:**

```bash
# Basic comparison, output to diff_output.html (spreadsheet view)
java -jar target/diff-tool-java-1.0-SNAPSHOT-jar-with-dependencies.jar file_v1.csv file_v2.csv

# Console output, no line numbers
java -jar target/diff-tool-java-1.0-SNAPSHOT-jar-with-dependencies.jar --no-html_output --no-show_line_numbers old.txt new.txt

# Simple HTML output to a specific file
java -jar target/diff-tool-java-1.0-SNAPSHOT-jar-with-dependencies.jar --simple_html --output_file comparison.html doc_v1.txt doc_v2.txt
``` 