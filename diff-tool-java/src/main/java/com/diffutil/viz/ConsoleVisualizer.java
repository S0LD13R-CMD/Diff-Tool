package com.diffutil.viz;

import com.diffutil.model.DiffElement;
import java.util.ArrayList;
import java.util.List;

public class ConsoleVisualizer {

    /**
     * Visualizes a diffing result in a unified view to the console.
     */
    public static void visualizeUnified(List<DiffElement> diff, boolean showLineNumbers) {
        List<String> diffLines = formatDiffLines(diff, showLineNumbers);
        System.out.println("\nShowing diff results:\n");
        for (String line : diffLines) {
            System.out.println(line);
        }
    }

    private static List<String> formatDiffLines(List<DiffElement> diff, boolean showLineNumbers) {
        List<String> result = new ArrayList<>();
        int maxLineNum = Math.max(getApproxOriginalLineCount(diff), getApproxNewLineCount(diff));
        int numDigits = String.valueOf(maxLineNum).length();
        // Ensure minimum 1 digit for formatting
        numDigits = Math.max(1, numDigits);
        String prefixFormat = String.format("[%%%dd] ", numDigits);
        String spacing = "  "; // Two spaces after prefix

        int lineNum1 = 1;
        int lineNum2 = 1;

        for (DiffElement element : diff) {
            String prefix = "";
            String lineContent = element.getContent() != null ? element.getContent() : ""; // Handle null content

            // Apply segment highlighting if applicable
            if (element.getDiffIndices().isPresent() && !element.getDiffIndices().get().isEmpty()) {
                lineContent = highlightSegmentsConsole(lineContent, element.getDiffIndices().get());
            }

            if (showLineNumbers) {
                switch (element.getType()) {
                    case ADDITION:
                        prefix = String.format(prefixFormat, lineNum2);
                        lineNum2++;
                        result.add(ColorUtil.green(prefix + "+ " + spacing + lineContent));
                        break;
                    case REMOVAL:
                        prefix = String.format(prefixFormat, lineNum1);
                        lineNum1++;
                        result.add(ColorUtil.red(prefix + "- " + spacing + lineContent));
                        break;
                    case UNCHANGED:
                        // Check for moved lines
                        if (element.isMoved().orElse(false)) {
                            int origIdx = element.getOriginalIndex().orElse(lineNum1);
                            int newIdx = element.getNewIndex().orElse(lineNum2);
                            String origPrefix = String.format(prefixFormat, origIdx);
                            String newPrefix = String.format(prefixFormat, newIdx);
                            prefix = origPrefix + "->" + newPrefix;
                            result.add(ColorUtil.purple(prefix + "~ " + spacing + lineContent));
                        } else {
                            prefix = String.format(prefixFormat, lineNum1);
                            result.add(prefix + "  " + spacing + lineContent); // Note: Two spaces for unchanged
                        }
                        lineNum1++;
                        lineNum2++;
                        break;
                }
            } else {
                // No line numbers
                switch (element.getType()) {
                    case ADDITION:
                        result.add(ColorUtil.green("+ " + spacing + lineContent));
                        break;
                    case REMOVAL:
                        result.add(ColorUtil.red("- " + spacing + lineContent));
                        break;
                    case UNCHANGED:
                         if (element.isMoved().orElse(false)) {
                             result.add(ColorUtil.purple("~ " + spacing + lineContent));
                         } else {
                             result.add("  " + spacing + lineContent);
                         }
                        break;
                }
            }
        }
        return result;
    }

     // Helper to highlight specific segments for console output
    private static String highlightSegmentsConsole(String content, List<Integer> diffIndices) {
        if (content == null || diffIndices == null || diffIndices.isEmpty()) {
            return content;
        }
        String[] segments = content.split(",", -1); // Split and keep trailing empty strings
        StringBuilder highlighted = new StringBuilder();
        for (int i = 0; i < segments.length; i++) {
            if (diffIndices.contains(i)) {
                highlighted.append(ColorUtil.yellow(segments[i]));
            } else {
                highlighted.append(segments[i]);
            }
            if (i < segments.length - 1) {
                highlighted.append(",");
            }
        }
        return highlighted.toString();
    }

    // Helper to estimate line count for formatting
    private static int getApproxOriginalLineCount(List<DiffElement> diff) {
        return (int) diff.stream()
            .filter(el -> el.getType() == DiffElement.ElementType.REMOVAL || el.getType() == DiffElement.ElementType.UNCHANGED)
            .count();
    }

    private static int getApproxNewLineCount(List<DiffElement> diff) {
         return (int) diff.stream()
            .filter(el -> el.getType() == DiffElement.ElementType.ADDITION || el.getType() == DiffElement.ElementType.UNCHANGED)
            .count();
    }
}
