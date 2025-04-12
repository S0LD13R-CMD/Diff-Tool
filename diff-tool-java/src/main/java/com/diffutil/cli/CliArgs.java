package com.diffutil.cli;

import picocli.CommandLine.Command;
import picocli.CommandLine.Option;
import picocli.CommandLine.Parameters;

import java.io.File;

@Command(name = "diff-tool",
         mixinStandardHelpOptions = true,
         version = "Diff Tool 1.0",
         description = "Compares two files and displays the differences.")
public class CliArgs implements Runnable {

    @Parameters(index = "0", description = "The original file to diff.")
    private File file1;

    @Parameters(index = "1", description = "The updated file to diff.")
    private File file2;

    // Using Option with arity=0 acts like a boolean flag
    @Option(names = {"--show_line_numbers"}, negatable = true, description = "Show line numbers (default: true). Use --no-show_line_numbers to hide.")
    boolean showLineNumbers = true; // Default is true

    @Option(names = {"--html_output"}, negatable = true, description = "Generate HTML output (default: true). Use --no-html_output for console.")
    boolean htmlOutput = true; // Default is true

    @Option(names = {"--output_file"}, defaultValue = "diff_output.html", description = "Output HTML file name (default: ${DEFAULT-VALUE}).")
    String outputFileName;

    @Option(names = {"--simple_html"}, description = "Generate simple HTML view instead of spreadsheet view.")
    boolean simpleHtml = false;

    // Getters for the Main class to access arguments
    public File getFile1() { return file1; }
    public File getFile2() { return file2; }
    public boolean isShowLineNumbers() { return showLineNumbers; }
    public boolean isHtmlOutput() { return htmlOutput; }
    public String getOutputFileName() { return outputFileName; }
    public boolean isSimpleHtml() { return simpleHtml; }

    // Picocli calls this method if the class implements Runnable
    // We don't do the main logic here, Main.java will handle it.
    @Override
    public void run() {
        // Validation could be added here if needed
        if (!file1.exists()) {
            System.err.println("Error: File 1 does not exist: " + file1.getPath());
            System.exit(1);
        }
        if (!file2.exists()) {
            System.err.println("Error: File 2 does not exist: " + file2.getPath());
            System.exit(1);
        }
    }
}
