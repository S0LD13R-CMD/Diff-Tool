package com.diffutil.core;

import java.util.List;
import java.util.Objects;

/**
 * Utility class for computing the Longest Common Subsequence (LCS) table.
 */
public class Lcs {

    /**
     * Computes the Longest Common Subsequence table for two lists.
     * Works for List<String> (lines) or List<List<String>> (parsed rows).
     *
     * @param <T>   The type of elements in the lists (e.g., String, List<String>).
     * @param list1 The first list.
     * @param list2 The second list.
     * @return A 2D array representing the LCS table.
     */
    public static <T> int[][] computeLcsTable(List<T> list1, List<T> list2) {
        int n = list1.size();
        int m = list2.size();
        int[][] lcs = new int[n + 1][m + 1];

        for (int i = 0; i <= n; i++) {
            for (int j = 0; j <= m; j++) {
                if (i == 0 || j == 0) {
                    lcs[i][j] = 0;
                } else if (Objects.equals(list1.get(i - 1), list2.get(j - 1))) {
                    // Elements are equal, increment diagonal
                    lcs[i][j] = 1 + lcs[i - 1][j - 1];
                } else {
                    // Elements are different, take max from left or top
                    lcs[i][j] = Math.max(lcs[i - 1][j], lcs[i][j - 1]);
                }
            }
        }
        return lcs;
    }
}
