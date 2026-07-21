/**
 * Entry point for the deep call-chain example.
 *
 * Call path:
 * DeepCallChainA -> DeepCallChainB -> DeepCallChainC
 *     -> DeepCallChainD -> DeepCallChainE
 */
public with sharing class DeepCallChainA {
    public static List<String> execute(List<String> values) {
        return DeepCallChainB.processValues(values);
    }
}
