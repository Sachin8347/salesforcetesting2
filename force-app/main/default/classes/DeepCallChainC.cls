/**
 * Handles one loop item before passing it deeper into the call chain.
 */
public with sharing class DeepCallChainC {
    public static String processValue(String value, Integer index) {
        return DeepCallChainD.normalizeAndFormat(value, index);
    }
}
