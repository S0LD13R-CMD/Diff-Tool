package main.java.com.diffutil.core;

import com.opencsv.CSVParserBuilder;
import com.opencsv.CSVReader;
import com.opencsv.CSVReaderBuilder;
import com.opencsv.exceptions.CsvException;

import main.java.com.diffutil.model.DiffElement;

import java.io.IOException;
import java.io.StringReader;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

public class CsvUtil {

    /**
     * Parses lines of text presumed to be CSV into lists of fields (rows).
     *
     * @param lines The lines of text to parse.
     * @return A list where each element is a list of strings representing a row's fields.
     */
    public static List<List<String>> parseCsvRows(List<String> lines) {
        List<List<String>> allRows = new ArrayList<>();
        if (lines == null) {
            return allRows;
        }

        // Use OpenCSV to handle potential complexities (quotes, commas within fields)
        for (String line : lines) {
            // Skip empty lines directly to avoid parser errors
            if (line.trim().isEmpty()) {
                allRows.add(new ArrayList<>()); // Add an empty list for an empty line
                continue;
            }
            try (StringReader stringReader = new StringReader(line);
                 // Use a standard comma parser
                 CSVReader csvReader = new CSVReaderBuilder(stringReader)
                                             .withCSVParser(new CSVParserBuilder().build()) // Default parser
                                             .build()) {

                // Read the single line - should produce one row (String[])
                String[] fields = csvReader.readNext();
                if (fields != null) {
                     // Convert String[] to List<String>
                    allRows.add(Arrays.stream(fields).collect(Collectors.toList()));
                } else {
                    // Handle cases where parsing might yield null (e.g., only delimiters?)
                    allRows.add(new ArrayList<>());
                }
            } catch (IOException | CsvValidationException e) {
                // If a line fails to parse as CSV, treat it as a single-column row
                // This matches Python's fallback behavior if csv.reader fails
                System.err.println("Warning: Failed to parse line as CSV: [" + line + "]. Treating as single field. Error: " + e.getMessage());
                allRows.add(List.of(line));
            } catch (CsvException e) {
              // TODO Auto-generated catch block
              e.printStackTrace();
              allRows.add(List.of(line)); // Fallback
            }
        }
        return allRows;
    }
    
    // Dummy CsvValidationException class if not using a version of OpenCSV that includes it 
    // or to avoid adding a specific dependency if not strictly needed.
    // Remove this if your OpenCSV version provides it or handle differently.
    private static class CsvValidationException extends Exception {
        public CsvValidationException(String message) {
            super(message);
        }
    }
}
