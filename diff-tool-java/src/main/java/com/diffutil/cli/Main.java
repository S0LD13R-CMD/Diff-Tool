package com.diffutil.cli;

import com.diffutil.core.Differ;
import com.diffutil.model.DiffElement;
import com.diffutil.viz.ConsoleVisualizer;
import com.diffutil.viz.HtmlVisualizer;
import picocli.CommandLine;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.List;

public class Main {

    public static void main(String[] args) {
        CliArgs cliArgs = new CliArgs();
        CommandLine cmd = new CommandLine(cliArgs);

        // Parse arguments and handle errors/help requests
        int exitCode = cmd.execute(args);
        if (exitCode != 0) {
            // Picocli handles help/version printing before this point
            // Exit if there was a parsing error or validation failed in run()
            System.exit(exitCode);
        }

        try {
            // Read file contents
            List<String> lines1 = Files.readAllLines(cliArgs.getFile1().toPath(), StandardCharsets.UTF_8);
            List<String> lines2 = Files.readAllLines(cliArgs.getFile2().toPath(), StandardCharsets.UTF_8);

            // Perform the diff
            List<DiffElement> diffResult = Differ.diff(lines1, lines2);

            // Visualize based on arguments
            if (cliArgs.isHtmlOutput()) {
                if (cliArgs.isSimpleHtml()) {
                    HtmlVisualizer.visualizeUnifiedHtml(diffResult, cliArgs.isShowLineNumbers(), cliArgs.getOutputFileName());
                } else {
                    HtmlVisualizer.visualizeUnifiedSpreadsheetHtml(diffResult, cliArgs.isShowLineNumbers(), cliArgs.getOutputFileName());
                }
            } else {
                ConsoleVisualizer.visualizeUnified(diffResult, cliArgs.isShowLineNumbers());
            }

        } catch (IOException e) {
            System.err.println("Error reading files: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        } catch (Exception e) {
            System.err.println("An unexpected error occurred: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }
}
