/**
 * Leaf of the example call chain. It produces the final string value.
 */
public with sharing class DeepCallChainE {
    public static String formatResult(String value, Integer index) {
        return 'Item ' + String.valueOf(index + 1) + ': ' + value;
    }
}
