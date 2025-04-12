package main.java.com.diffutil.core;

import main.java.com.diffutil.model.Addition;
import main.java.com.diffutil.model.DiffElement;
import main.java.com.diffutil.model.Removal;
import main.java.com.diffutil.model.Unchanged;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

public class Differ {

    /**
     * Computes the optimal diff of the two given lists of lines.
     * Detects if the input looks like CSV and calls the appropriate diff method.
     */
    public static List<DiffElement> diff(List<String> lines1, List<String> lines2) {
        // Basic CSV detection (similar to Python version)
        long commaLines1 = lines1.stream().filter(line -> line.contains(",")).count();
        long commaLines2 = lines2.stream().filter(line -> line.contains(",")).count();

        // Use a threshold (e.g., 80%) to decide if it's likely CSV
        boolean likelyCsv = (lines1.size() > 0 && (double) commaLines1 / lines1.size() > 0.8) &&
                            (lines2.size() > 0 && (double) commaLines2 / lines2.size() > 0.8);

        if (likelyCsv) {
            return diffCsv(lines1, lines2);
        } else {
            return diffTraditional(lines1, lines2);
        }
    }

    /**
     * Traditional line-based diff algorithm using LCS.
     */
    private static List<DiffElement> diffTraditional(List<String> lines1, List<String> lines2) {
        int[][] lcsTable = Lcs.computeLcsTable(lines1, lines2);
        List<DiffElement> results = new ArrayList<>();

        int i = lines1.size();
        int j = lines2.size();

        while (i > 0 || j > 0) {
            if (i > 0 && j > 0 && Objects.equals(lines1.get(i - 1), lines2.get(j - 1))) {
                results.add(new Unchanged(lines1.get(i - 1)));
                i--;
                j--;
            } else if (j > 0 && (i == 0 || lcsTable[i][j - 1] >= lcsTable[i - 1][j])) {
                results.add(new Addition(lines2.get(j - 1)));
                j--;
            } else if (i > 0 && (j == 0 || lcsTable[i][j - 1] < lcsTable[i - 1][j])) {
                results.add(new Removal(lines1.get(i - 1)));
                i--;
            } else {
                 System.err.println("Error: Unexpected state in LCS traceback (traditional)");
                 break; // Should not happen
            }
        }
        Collections.reverse(results);
        return results;
    }

    /**
     * CSV-aware diff using LCS for row alignment and post-processing for modifications.
     */
    private static List<DiffElement> diffCsv(List<String> lines1, List<String> lines2) {
        List<List<String>> rows1 = CsvUtil.parseCsvRows(lines1);
        List<List<String>> rows2 = CsvUtil.parseCsvRows(lines2);

        // --- Step 1 & 2: Compute LCS on rows and build initial diff list ---
        int[][] lcsTable = Lcs.computeLcsTable(rows1, rows2);
        List<DiffElement> initialResults = new ArrayList<>();
        int i = rows1.size();
        int j = rows2.size();

        // Check for identical headers separately to handle edge cases
        boolean identicalHeaders = !rows1.isEmpty() && !rows2.isEmpty() && Objects.equals(rows1.get(0), rows2.get(0));

        while (i > 0 || j > 0) {
            boolean isHeaderRow1 = i == 1 && identicalHeaders;
            boolean isHeaderRow2 = j == 1 && identicalHeaders;

            if (isHeaderRow1 && isHeaderRow2) {
                // Skip identical headers during traceback
                i--;
                j--;
                continue;
            }

            if (i > 0 && j > 0 && Objects.equals(rows1.get(i - 1), rows2.get(j - 1))) {
                initialResults.add(new Unchanged(lines1.get(i - 1))); // Use original line content
                i--;
                j--;
            } else if (j > 0 && (i == 0 || lcsTable[i][j - 1] >= lcsTable[i - 1][j])) {
                initialResults.add(new Addition(lines2.get(j - 1))); // Use original line content
                j--;
            } else if (i > 0 && (j == 0 || lcsTable[i][j - 1] < lcsTable[i - 1][j])) {
                initialResults.add(new Removal(lines1.get(i - 1))); // Use original line content
                i--;
            } else {
                 System.err.println("Error: Unexpected state in LCS traceback (CSV)");
                 break; // Should not happen
            }
        }

        // Add identical header explicitly if it exists
        if (identicalHeaders) {
            initialResults.add(new Unchanged(lines1.get(0)));
        }

        Collections.reverse(initialResults);

        // --- Step 3: Post-processing to identify Modifications ---
        List<DiffElement> finalResults = new ArrayList<>();
        boolean[] processed = new boolean[initialResults.size()];
        int finalIndexCounter = 0; // To calculate matched indices for final list

        for (int idx = 0; idx < initialResults.size(); idx++) {
            if (processed[idx]) {
                continue;
            }

            DiffElement currentElement = initialResults.get(idx);

            if (idx + 1 < initialResults.size() &&
                currentElement instanceof Removal &&
                initialResults.get(idx + 1) instanceof Addition) {

                Removal removal = (Removal) currentElement;
                Addition addition = (Addition) initialResults.get(idx + 1);

                // Parse rows only if needed for similarity check
                List<String> removalRow = CsvUtil.parseCsvRows(List.of(removal.getContent())).get(0);
                List<String> additionRow = CsvUtil.parseCsvRows(List.of(addition.getContent())).get(0);

                double similarityScore = calculateRowSimilarity(removalRow, additionRow);
                boolean isIdMatch = !removalRow.isEmpty() && !additionRow.isEmpty() &&
                                    Objects.equals(removalRow.get(0), additionRow.get(0));

                // Similarity threshold
                if (isIdMatch || similarityScore >= 0.8) {
                    List<Integer> diffIndices = identifyRowFieldDifferences(removalRow, additionRow);

                    int removalFinalIdx = finalIndexCounter;
                    int additionFinalIdx = finalIndexCounter + 1;

                    finalResults.add(new Removal(removal.getContent(), diffIndices, additionFinalIdx));
                    finalResults.add(new Addition(addition.getContent(), diffIndices, removalFinalIdx));

                    processed[idx] = true;
                    processed[idx + 1] = true;
                    finalIndexCounter += 2;
                    idx++; // Increment idx again as we processed two elements
                    continue;
                }
            }

            // Default: Add element as is
            finalResults.add(currentElement);
            processed[idx] = true;
            finalIndexCounter++;
        }

        return finalResults;
    }

    /**
     * Calculates a similarity score between two rows (lists of fields).
     * Translation of the Python version's logic.
     */
    private static double calculateRowSimilarity(List<String> row1, List<String> row2) {
        if (row1 == null || row2 == null || row1.isEmpty() || row2.isEmpty()) {
            return 0.0;
        }

        // 1. Exact Match
        if (Objects.equals(row1, row2)) {
            return 1.0;
        }

        // 2. ID Match (First Column)
        if (Objects.equals(row1.get(0), row2.get(0))) {
            return 0.95; // High score for ID match
        }

        // 3. Near Match (Few Differences)
        int matchingFields = 0;
        int minLen = Math.min(row1.size(), row2.size());
        int maxLen = Math.max(row1.size(), row2.size());
        int differentFields = 0;

        for (int i = 0; i < minLen; i++) {
            if (Objects.equals(row1.get(i), row2.get(i))) {
                matchingFields++;
            } else {
                differentFields++;
            }
        }
        // Count fields present only in the longer row as differences
        differentFields += (maxLen - minLen);

        if (differentFields == 1) return 0.90;
        if (differentFields == 2) return 0.85;
        if (differentFields == 3) return 0.80;

        // 4. Percentage Match (Scaled)
        if (maxLen == 0) {
            return 0.0;
        }
        double matchPercentage = (double) matchingFields / maxLen;
        return matchPercentage * 0.7; // Scale down general percentage match
    }

    /**
     * Identifies indices where fields differ between two rows.
     */
    private static List<Integer> identifyRowFieldDifferences(List<String> row1, List<String> row2) {
        List<Integer> diffIndices = new ArrayList<>();
        int maxLen = Math.max(row1.size(), row2.size());
        for (int idx = 0; idx < maxLen; idx++) {
            String field1 = (idx < row1.size()) ? row1.get(idx) : null;
            String field2 = (idx < row2.size()) ? row2.get(idx) : null;
            if (!Objects.equals(field1, field2)) {
                diffIndices.add(idx);
            }
        }
        return diffIndices;
    }
}
