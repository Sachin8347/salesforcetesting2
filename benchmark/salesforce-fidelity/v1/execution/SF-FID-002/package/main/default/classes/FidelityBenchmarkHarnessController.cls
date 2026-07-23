global with sharing class FidelityBenchmarkHarnessController {
    @RemoteAction
    global static String run() {
        Map<String, Object> observation = FidelityBenchmarkScenario.run();
        observation.put('observedAt', Datetime.now().formatGmt('yyyy-MM-dd\'T\'HH:mm:ss\'Z\''));
        return JSON.serialize(observation);
    }
}
