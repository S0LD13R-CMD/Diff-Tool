package com.diffutil.core;

import com.diffutil.model.DiffElement;
import com.diffutil.viz.HtmlVisualizer;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.List;

public class Main {

    public static void main(String[] args) {
        // --- Configuration ---
        // MODIFY THESE PATHS TO YOUR ACTUAL INPUT FILES
        String file1Path = "diff-tool-java/data.csv"; // Updated path
        String file2Path = "diff-tool-java/data1.csv"; // Updated path
        String outputHtmlPath = "diff_output.html"; // Output path in project root
        boolean showLineNumbers = true;
        // --- End Configuration ---

        try {
            System.out.println("Reading file 1: " + file1Path);
            List<String> lines1 = Files.readAllLines(Paths.get(file1Path));

            System.out.println("Reading file 2: " + file2Path);
            List<String> lines2 = Files.readAllLines(Paths.get(file2Path));

            System.out.println("Calculating diff...");
            List<DiffElement> diffResult = Differ.diff(lines1, lines2);

            System.out.println("Generating HTML visualization...");
            HtmlVisualizer.visualizeUnifiedSpreadsheetHtml(diffResult, showLineNumbers, outputHtmlPath);

            System.out.println("Diff process completed. Output saved to: " + outputHtmlPath);

        } catch (IOException e) {
            System.err.println("Error during diff process: " + e.getMessage());
            e.printStackTrace();
        }
    }
}