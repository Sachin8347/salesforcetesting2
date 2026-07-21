/**
 * Normalizes the loop item and delegates final rendering to class E.
 */
public with sharing class DeepCallChainD {
    public static String normalizeAndFormat(String value, Integer index) {
        String normalizedValue = value == null ? '' : value.trim().toUpperCase();
        return DeepCallChainE.formatResult(normalizedValue, index);
    }
}
