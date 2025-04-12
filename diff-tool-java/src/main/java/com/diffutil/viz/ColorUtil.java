package main.java.com.diffutil.viz;

/**
 * Utility class for ANSI terminal colors.
 */
public class ColorUtil {

    public static final String ANSI_RESET = "\u001B[0m";
    public static final String ANSI_RED = "\u001B[31m";
    public static final String ANSI_GREEN = "\u001B[32m";
    public static final String ANSI_YELLOW = "\u001B[33m"; // For highlighting segments
    public static final String ANSI_PURPLE = "\u001B[35m"; // For moved lines

    public static String color(String text, String colorCode) {
        return colorCode + text + ANSI_RESET;
    }

    public static String red(String text) {
        return color(text, ANSI_RED);
    }

    public static String green(String text) {
        return color(text, ANSI_GREEN);
    }

     public static String yellow(String text) {
        return color(text, ANSI_YELLOW);
    }

    public static String purple(String text) {
        return color(text, ANSI_PURPLE);
    }
} 