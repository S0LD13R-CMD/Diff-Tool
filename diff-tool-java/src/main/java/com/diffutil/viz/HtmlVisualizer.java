package main.java.com.diffutil.viz;

import main.java.com.diffutil.core.CsvUtil;
import main.java.com.diffutil.model.Addition;
import main.java.com.diffutil.model.DiffElement;
import main.java.com.diffutil.model.Removal;
import main.java.com.diffutil.model.Unchanged;

import java.io.IOException;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Collectors;
import java.util.stream.IntStream;


public class HtmlVisualizer {

    // Simple HTML view (not spreadsheet-like)
    public static void visualizeUnifiedHtml(List<DiffElement> diff, boolean showLineNumbers, String outputFilePath) {
        StringBuilder html = new StringBuilder();

        appendSimpleHtmlHeader(html);

        AtomicInteger lineNum1 = new AtomicInteger(1);
        AtomicInteger lineNum2 = new AtomicInteger(1);

        html.append("            <tbody>\n");

        for (DiffElement element : diff) {
            html.append("                <tr>\n");
            String prefix = "";
            String cssClass = "";
            String symbol = "";

            if (showLineNumbers) {
                 if (element instanceof Addition) {
                    prefix = "[" + lineNum2.getAndIncrement() + "]";
                    symbol = "+";
                    cssClass = "addition";
                 } else if (element instanceof Removal) {
                    prefix = "[" + lineNum1.getAndIncrement() + "]";
                    symbol = "-";
                    cssClass = "removal";
                 } else if (element instanceof Unchanged) {
                     if (element.isMoved().orElse(false)) {
                         prefix = "[" + element.getOriginalIndex().orElse(lineNum1.get()) + "->" + element.getNewIndex().orElse(lineNum2.get()) + "]";
                         symbol = "~";
                         cssClass = "moved";
                     } else {
                         prefix = "[" + lineNum1.get() + "]";
                         symbol = " "; // Space for unchanged
                         cssClass = "unchanged";
                     }
                     lineNum1.getAndIncrement();
                     lineNum2.getAndIncrement();
                 }
                html.append("                    <td class=\"line-number ").append(cssClass).append("\">").append(prefix).append(" ").append(symbol).append("</td>\n");
            } else {
                 if (element instanceof Addition) symbol = "+";
                 else if (element instanceof Removal) symbol = "-";
                 else if (element instanceof Unchanged && element.isMoved().orElse(false)) symbol = "~";
                 else symbol = " ";
                 cssClass = element.getType().name().toLowerCase();
                 html.append("                    <td class=\"line-number ").append(cssClass).append("\">").append(symbol).append("</td>\n");
            }

            // Format content - highlighting not implemented in simple view
            String content = element.getContent() != null ? escapeHtml(element.getContent()) : "";
            html.append("                    <td class=\"").append(cssClass).append("\">").append(content).append("</td>\n");

            html.append("                </tr>\n");
        }

        html.append("            </tbody>\n        </table>\n    </div> \n</body>\n</html>");

        writeToFile(outputFilePath, html.toString());
        System.out.println("\nHTML diff output saved to " + outputFilePath + "\n");
    }

    // Spreadsheet-like HTML view
    public static void visualizeUnifiedSpreadsheetHtml(List<DiffElement> diff, boolean showLineNumbers, String outputFilePath) {
        StringBuilder html = new StringBuilder();
        List<Map<String, Object>> displayElements = new ArrayList<>();
        Map<Integer, List<String>> elementFields = new HashMap<>();
        Map<Integer, Map<String, Integer>> tempPosData = new HashMap<>();
        int maxFieldCount = 0;

        // --- Pass 1: Calculate Line Numbers & Parse Fields ---
        int originalPosCounter = 1;
        int modifiedPosCounter = 1;
        for (int i = 0; i < diff.size(); i++) {
            DiffElement element = diff.get(i);
            Integer currentOriginalPos = null;
            Integer currentModifiedPos = null;

            if (element instanceof Removal) {
                currentOriginalPos = originalPosCounter++;
            } else if (element instanceof Addition) {
                currentModifiedPos = modifiedPosCounter++;
            } else if (element instanceof Unchanged) {
                currentOriginalPos = originalPosCounter++;
                currentModifiedPos = modifiedPosCounter++;
            }

            Map<String, Integer> posMap = new HashMap<>();
            posMap.put("orig", currentOriginalPos);
            posMap.put("mod", currentModifiedPos);
            tempPosData.put(i, posMap);

            // Parse fields
            List<List<String>> parsed = CsvUtil.parseCsvRows(List.of(element.getContent()));
            List<String> fields = parsed.isEmpty() ? new ArrayList<>() : parsed.get(0);
            elementFields.put(i, fields);
            maxFieldCount = Math.max(maxFieldCount, fields.size());
        }

        // --- Pass 2: Build Display Elements, Pairing Modifications ---
        boolean[] processed = new boolean[diff.size()];
        for (int i = 0; i < diff.size(); i++) {
            if (processed[i]) continue;

            DiffElement element = diff.get(i);
            Integer lineNumOrig = tempPosData.get(i).get("orig");
            Integer lineNumMod = tempPosData.get(i).get("mod");

            if (element instanceof Removal && element.getMatchedIndex().isPresent()) {
                int linkedAdditionIndex = element.getMatchedIndex().get();

                if (linkedAdditionIndex < diff.size() &&
                    diff.get(linkedAdditionIndex) instanceof Addition &&
                    diff.get(linkedAdditionIndex).getMatchedIndex().isPresent() &&
                    diff.get(linkedAdditionIndex).getMatchedIndex().get() == i) {

                    processed[linkedAdditionIndex] = true;
                    lineNumMod = tempPosData.get(linkedAdditionIndex).get("mod");

                    List<String> removalFields = elementFields.get(i);
                    List<String> additionFields = elementFields.get(linkedAdditionIndex);
                    List<Map<String, Object>> mergedFields = new ArrayList<>();
                    int localMaxLen = Math.max(removalFields.size(), additionFields.size());
                    List<Integer> diffIndices = element.getDiffIndices().orElse(Collections.emptyList());

                    for (int fieldIdx = 0; fieldIdx < localMaxLen; fieldIdx++) {
                        String oldVal = fieldIdx < removalFields.size() ? removalFields.get(fieldIdx) : "";
                        String newVal = fieldIdx < additionFields.size() ? additionFields.get(fieldIdx) : "";
                        boolean changed = diffIndices.contains(fieldIdx);
                        Map<String, Object> fieldData = new HashMap<>();
                        fieldData.put("old", oldVal);
                        fieldData.put("new", newVal);
                        fieldData.put("changed", changed);
                        fieldData.put("value", newVal); // Store new value for easier access
                        mergedFields.add(fieldData);
                    }

                    Map<String, Object> modElement = new HashMap<>();
                    modElement.put("type", "modified");
                    modElement.put("line_num_orig", lineNumOrig);
                    modElement.put("line_num_mod", lineNumMod);
                    modElement.put("merged_fields", mergedFields);
                    modElement.put("original_index", i);
                    displayElements.add(modElement);
                    processed[i] = true;
                    continue;
                } else {
                     System.err.println("Warning: Invalid link found for Removal at index " + i + ". Linked index: " + linkedAdditionIndex);
                }
            }

            // Handle Standalone elements
            Map<String, Object> displayElement = new HashMap<>();
            displayElement.put("type", element.getType().name().toLowerCase());
            displayElement.put("line_num_orig", lineNumOrig);
            displayElement.put("line_num_mod", lineNumMod);
            displayElement.put("fields", elementFields.get(i));
            displayElement.put("original_index", i);
            displayElements.add(displayElement);
            processed[i] = true;
        }

        // --- Calculate Counts ---
        long addedRows = displayElements.stream().filter(el -> "addition".equals(el.get("type"))).count();
        long removedRows = displayElements.stream().filter(el -> "removal".equals(el.get("type"))).count();
        long modifiedCells = displayElements.stream()
                .filter(el -> "modified".equals(el.get("type")))
                .flatMap(el -> ((List<Map<String, Object>>) el.get("merged_fields")).stream())
                .filter(field -> (Boolean) field.get("changed"))
                .count();

        // --- Determine Header Row --- (Logic from Python)
        List<String> headerRowFields = determineHeaderFields(diff, elementFields, maxFieldCount);
        maxFieldCount = Math.max(maxFieldCount, headerRowFields.size()); // Recalculate max fields based on header
        String headerCellsHtml = headerRowFields.stream()
                                           .map(header -> "<th>" + escapeHtml(header) + "</th>")
                                           .collect(Collectors.joining("\n                        "));

        // --- Generate HTML --- 
        appendSpreadsheetHtmlHeader(html, addedRows, removedRows, modifiedCells);
        appendSpreadsheetHtmlTableStart(html, headerCellsHtml);
        appendSpreadsheetHtmlTableBody(html, displayElements, showLineNumbers, maxFieldCount);
        appendSpreadsheetHtmlFooter(html);

        writeToFile(outputFilePath, html.toString());
        System.out.println("\nHTML diff output saved to " + outputFilePath + "\n");
    }

    // --- Helper Methods for Spreadsheet HTML --- 

    private static List<String> determineHeaderFields(List<DiffElement> diff, Map<Integer, List<String>> elementFields, int currentMaxFields) {
        List<String> headerRowFields = new ArrayList<>();
        boolean headerModified = diff.size() >= 2 && diff.get(0) instanceof Removal && diff.get(1) instanceof Addition;

        if (headerModified) {
            headerRowFields = elementFields.getOrDefault(1, new ArrayList<>());
            System.out.println("DEBUG: Header modified, using new header fields: " + headerRowFields);
        } else if (!elementFields.isEmpty()) {
            List<String> firstRowFields = elementFields.getOrDefault(0, new ArrayList<>());
            // Basic heuristic to detect header-like row
            boolean looksLikeHeader = firstRowFields.stream()
                    .filter(h -> h != null)
                    .anyMatch(h -> h.toLowerCase().matches(".*(id|name|date|col).*|_no"));
            if (!firstRowFields.isEmpty() && looksLikeHeader) {
                headerRowFields = firstRowFields;
                 System.out.println("DEBUG: Header not modified, using detected header fields: " + headerRowFields);
            }
        }

        // Fallback to generic headers
        if (headerRowFields.isEmpty()) {
            int count = Math.max(currentMaxFields, 1); // Ensure at least one column header
            headerRowFields = IntStream.rangeClosed(1, count)
                                      .mapToObj(i -> "Col_" + i)
                                      .collect(Collectors.toList());
             System.out.println("DEBUG: No specific header found, generating generic headers based on max field count: " + count);
        }
        return headerRowFields;
    }

    private static void appendSpreadsheetHtmlHeader(StringBuilder html, long addedRows, long removedRows, long modifiedCells) {
        html.append("<!DOCTYPE html>\n")
            .append("<html>\n")
            .append("<head>\n")
            .append("    <title>CSV Diff Results</title>\n")
            .append("    <style>\n")
            // Append all CSS rules here (copied and adapted from Python version)
            .append("        body { font-family: monospace; background-color: #0d1117; color: #c9d1d9; margin: 0; padding: 0; }\n")
            .append("        .main-container { padding: 20px; }\n") // Removed overflow/max-height
            .append("        .table-scroll-wrapper { overflow-y: auto; max-height: calc(100vh - 75px); }\n") // Added wrapper for scroll
            .append("        table { width: 100%; background-color: #0d1117; margin-top: 0; border-radius: 8px; overflow: hidden; border-spacing: 0; }\n")
            .append("        th, td { border-bottom: 1px solid #30363d; padding: 8px; text-align: left; }\n")
            .append("        tbody tr:last-child td { border-bottom: none; }\n")
            .append("        th { background-color: #161b22; color: #c9d1d9; border-bottom: 1px solid #30363d; }\n") // General TH style
            .append("        tbody tr:first-child th { position: -webkit-sticky; position: sticky; top: 0; background-color: #000000 !important; color: #e0e0e0 !important; z-index: 10; border-bottom: 1px solid #30363d; }\n") // Sticky header row TH
            .append("        tr.addition td:not(:nth-child(-n+3)) { background-color: rgba(46, 160, 67, 0.15); }\n")
            .append("        tr.removal td:not(:nth-child(-n+3)) { background-color: rgba(248, 81, 73, 0.15); }\n")
            .append("        tr td.status-col, tr td.line-num { background-color: #161b22 !important; }\n")
            .append("        tr.modified td { background-color: transparent; }\n")
            .append("        .addition-text { color: #3fb950; }\n")
            .append("        .removal-text { color: #f85149; }\n")
            .append("        .modified-text { color: #d29922; }\n")
            .append("        .unchanged { color: #c9d1d9; }\n")
            .append("        .center-align { text-align: center; }\n")
            .append("        .status-col { background-color: #161b22; min-width: 80px; text-align: center; font-weight: bold; user-select: none; border-color: #30363d; }\n")
            .append("        .line-num { color: #8b949e; min-width: 30px; max-width: 40px; user-select: none; background-color: #161b22; padding: 0 4px; border-color: #30363d; }\n")
            .append("        .line-num-left { text-align: right; padding-right: 6px; }\n")
            .append("        .line-num-right { text-align: left; padding-left: 6px; }\n")
            .append("        .index-header { text-align: center !important; padding: 8px 0; }\n")
            .append("        .arrow { color: #8b949e; padding: 0 5px; }\n")
            .append("        .empty-cell { color: #6e7681; font-style: italic; }\n")
            .append("        * { border-color: #30363d !important; }\n") // Force border color - might be too broad
            .append("        .toggle-container { position: sticky; top: 0; padding: 10px 20px; background-color: #0d1117; z-index: 100; border-bottom: 1px solid #30363d; width: 100%; box-sizing: border-box; display: flex; align-items: center; justify-content: space-between; min-height: 55px; }\n")
            .append("        .info-section { color: #8b949e; font-size: 14px; }\n")
            .append("        .info-section span { margin-left: 15px; }\n")
            .append("        .info-added { color: #3fb950; font-weight: bold; }\n")
            .append("        .info-removed { color: #f85149; font-weight: bold; }\n")
            .append("        .info-modified { color: #d29922; font-weight: bold; }\n")
            .append("        .toggle-button { background-color: #30363d; color: #c9d1d9; border: 1px solid #8b949e; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 14px; font-family: monospace; }\n")
            .append("        .toggle-button:hover { background-color: #484f58; border-color: #c9d1d9; }\n")
            .append("        tbody tr:first-child th.status-col { background-color: #000000 !important; }\n") // Sticky header status column
            .append("        tbody tr:first-child th.line-num { background-color: #000000 !important; color: #8b949e !important; }\n") // Sticky header line num
            .append("        tbody tr:first-child th.line-num.addition-text, tbody tr:first-child th.line-num.removal-text, tbody tr:first-child th.line-num.modified-text { color: #8b949e !important; }\n") // Sticky header line num text color override
            .append("    </style>\n")
            .append("    <script>\n")
            .append("        function toggleEmptyCells() {\n")
            .append("            const emptyCells = document.querySelectorAll('.empty-cell');\n")
            .append("            const button = document.getElementById('toggle-button');\n")
            .append("            for (const cell of emptyCells) {\n")
            .append("                if (cell.style.display === 'none') { cell.style.display = 'inline'; button.textContent = 'Hide (empty) Labels'; } else { cell.style.display = 'none'; button.textContent = 'Show (empty) Labels'; }\n")
            .append("            }\n        }\n")
            .append("        window.addEventListener('DOMContentLoaded', (event) => { document.getElementById('toggle-button').textContent = 'Hide (empty) Labels'; });\n")
            .append("    </script>\n")
            .append("</head>\n")
            .append("<body>\n")
            .append("    <div class=\"toggle-container\">\n")
            .append("        <button id=\"toggle-button\" class=\"toggle-button\" onclick=\"toggleEmptyCells()\">Hide (empty) Labels</button>\n")
            .append("        <div class=\"info-section\">\n")
            .append("             <span>Added: <span class=\"info-added\">" + addedRows + "</span></span>\n")
            .append("             <span>Removed: <span class=\"info-removed\">" + removedRows + "</span></span>\n")
            .append("             <span>Modified Cells: <span class=\"info-modified\">" + modifiedCells + "</span></span>\n")
            .append("        </div>\n    </div>\n");
    }

    private static void appendSpreadsheetHtmlTableStart(StringBuilder html, String headerCellsHtml) {
        html.append("    <div class=\"main-container\">\n")
            .append("        <div class=\"table-scroll-wrapper\">\n")
            .append("            <table>\n")
            .append("                <tbody>\n")
            .append("                    <tr>\n")
            .append("                        <th class=\"status-col\">Status</th>\n")
            .append("                        <th class=\"line-num line-num-left index-header\" colspan=\"2\">Line</th>\n")
            .append("                        " + headerCellsHtml + "\n")
            .append("                    </tr>\n"); // Start of table body content follows
    }

     private static void appendSpreadsheetHtmlTableBody(StringBuilder html, List<Map<String, Object>> displayElements, boolean showLineNumbers, int maxFieldCount) {
        for (Map<String, Object> element : displayElements) {
            String elementType = (String) element.get("type");
            if (Integer.valueOf(0).equals(element.get("original_index"))) {
                continue; // Skip original header row in body
            }

            String rowClass = elementType;
            html.append("                    <tr class=\"").append(rowClass).append("\">\n");

            // Status column
            String statusText = elementType.substring(0, 1).toUpperCase() + elementType.substring(1);
            String statusClass = elementType + "-text";
            html.append("                        <td class=\"status-col ").append(statusClass).append("\">").append(statusText).append("</td>\n");

            // Line numbers
            if (showLineNumbers) {
                String origNumDisplay = element.get("line_num_orig") != null ? String.valueOf(element.get("line_num_orig")) : "";
                String modNumDisplay = element.get("line_num_mod") != null ? String.valueOf(element.get("line_num_mod")) : "";
                String origClass = "removal-text".equals(statusClass) || "modified-text".equals(statusClass) ? "removal-text" : "";
                String modClass = "addition-text".equals(statusClass) || "modified-text".equals(statusClass) ? "addition-text" : "";
                html.append("                        <td class=\"line-num line-num-left center-align ").append(origClass).append("\">").append(origNumDisplay).append("</td>\n");
                html.append("                        <td class=\"line-num line-num-right center-align ").append(modClass).append("\">").append(modNumDisplay).append("</td>\n");
            }

            // Field content
            if ("modified".equals(elementType)) {
                List<Map<String, Object>> mergedFields = (List<Map<String, Object>>) element.get("merged_fields");
                for (Map<String, Object> field : mergedFields) {
                    html.append("                        "); // Indentation
                    if ((Boolean) field.get("changed")) {
                        html.append(generateModifiedTdHtml(field.get("old"), field.get("new")));
                    } else {
                        html.append(generateTdHtml(field.get("value")));
                    }
                    html.append("\n");
                }
                 // Pad remaining cells
                for (int i = mergedFields.size(); i < maxFieldCount; i++) {
                    html.append("                        <td></td>\n");
                }
            } else {
                List<String> fields = (List<String>) element.get("fields");
                for (String field : fields) {
                    html.append("                        ").append(generateTdHtml(field)).append("\n");
                }
                // Pad remaining cells
                for (int i = fields.size(); i < maxFieldCount; i++) {
                    html.append("                        <td></td>\n");
                }
            }
            html.append("                    </tr>\n");
        }
    }

     private static void appendSpreadsheetHtmlFooter(StringBuilder html) {
        html.append("                </tbody>\n            </table>\n        </div>\n    </div>\n</body>\n</html>");
    }

    // --- Simple HTML Helpers ---
    private static void appendSimpleHtmlHeader(StringBuilder html) {
         html.append("<!DOCTYPE html>\n<html>\n<head>\n<title>Diff Results</title>\n<style>\n")
             .append("body { font-family: monospace; }\n")
             .append(".diff-results { list-style: none; padding: 0; margin: 0; }\n")
             .append("li { padding: 2px 5px; white-space: pre; }\n")
             .append(".line-number { display: inline-block; width: 50px; color: grey; text-align: right; margin-right: 10px; user-select: none; }\n") // Basic line number style
             .append(".addition { background-color: #e6ffed; }\n")
             .append(".removal { background-color: #ffeef0; text-decoration: line-through; }\n")
             .append(".moved { background-color: #f0eaff; }\n") // Simple moved style
             .append("td.addition { background-color: #e6ffed; }\n")
             .append("td.removal { background-color: #ffeef0; }\n")
             .append("td.moved { background-color: #f0eaff; }\n")
             .append("</style>\n</head>\n<body>\n<div class=\"main-container\">\n<table>\n");
    }

    // --- General Helpers ---

    private static String escapeHtml(Object obj) {
        if (obj == null) return "";
        String text = obj.toString();
        // Basic HTML escaping
        return text.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
                   .replace("\"", "&quot;")
                   .replace("'", "&#39;");
    }

    private static String generateTdHtml(Object fieldValue) {
        String content = escapeHtml(fieldValue);
        if (content.isEmpty()) {
            return "<td><span class=\"empty-cell\">(empty)</span></td>";
        } else {
            return "<td>" + content + "</td>";
        }
    }

    private static String generateModifiedTdHtml(Object oldVal, Object newVal) {
        String oldDisplay = escapeHtml(oldVal);
        String newDisplay = escapeHtml(newVal);
        oldDisplay = oldDisplay.isEmpty() ? "<span class=\"empty-cell\">(empty)</span>" : oldDisplay;
        newDisplay = newDisplay.isEmpty() ? "<span class=\"empty-cell\">(empty)</span>" : newDisplay;
        return "<td><span class=\"removal-text\">" + oldDisplay + "</span> <span class=\"arrow\">-></span> <span class=\"addition-text\">" + newDisplay + "</span></td>";
    }

    private static void writeToFile(String filePath, String content) {
        try (PrintWriter writer = new PrintWriter(filePath, StandardCharsets.UTF_8)) {
            writer.print(content);
        } catch (IOException e) {
            System.err.println("Error writing HTML output to file: " + filePath + " - " + e.getMessage());
            e.printStackTrace();
        }
    }
}
