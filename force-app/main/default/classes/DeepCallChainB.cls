/**
 * Iterates over every input value and delegates each item to class C.
 */
public with sharing class DeepCallChainB {
    public static List<String> processValues(List<String> values) {
        List<String> results = new List<String>();
        if (values == null) {
            return results;
        }

        for (Integer index = 0; index < values.size(); index++) {
            results.add(DeepCallChainC.processValue(values[index], index));
        }
        return results;
    }
}
