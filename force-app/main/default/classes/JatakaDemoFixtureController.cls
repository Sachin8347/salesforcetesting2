/**
 * Thin Aura-enabled entry for MCP/Brum visibility and manual demo seeding.
 */
public with sharing class JatakaDemoFixtureController {
    @AuraEnabled
    public static JatakaDemoFixtureService.SeedResult seedDemoFixtures(String scenarioId) {
        try {
            return JatakaDemoFixtureService.seed(scenarioId);
        } catch (Exception e) {
            throw new AuraHandledException('Demo fixture seed failed: ' + e.getMessage());
        }
    }

    @AuraEnabled(cacheable=true)
    public static JatakaDemoFixtureService.SeedResult getDemoFixtureStatus(String scenarioId) {
        return JatakaDemoFixtureService.status(scenarioId);
    }
}
