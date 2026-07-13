/**
 * REST entry for Jataka backend/dashboard to provision CEO demo fixtures.
 *
 * Security:
 * - Declared `with sharing` so org sharing rules apply to Case/Account/custom-object DML.
 * - Only creates/refreshes records with the stable JATAKA_DEMO_ prefix via
 *   JatakaDemoFixtureService (no arbitrary record mutation).
 * - Intended for connected demo orgs / CEO walkthrough provisioning, not public anonymous access.
 *
 * POST body:
 * { "action": "seed" | "status", "scenarioId": "knowledge-publish-blocked" | "all" }
 */
@RestResource(urlMapping='/jataka/v1/demo-fixtures')
global with sharing class JatakaDemoFixtureRest {
    global class ActionRequest {
        public String action;
        public String scenarioId;
    }

    global class FixtureRecordDto {
        public String objectApiName;
        public String recordId;
        public String externalKey;
        public String label;
        public String status;
        public String caseNumber;
        public Boolean created;
    }

    global class SeedResultDto {
        public Boolean success;
        public String message;
        public String scenarioId;
        public List<FixtureRecordDto> records;
    }

    @HttpPost
    global static SeedResultDto postAction() {
        ActionRequest body = (ActionRequest) JSON.deserialize(
            RestContext.request.requestBody.toString(),
            ActionRequest.class
        );

        String actionName = body == null || String.isBlank(body.action)
            ? 'seed'
            : body.action.trim().toLowerCase();
        String scenarioId = body == null ? 'all' : body.scenarioId;

        if (actionName == 'status') {
            return toDto(JatakaDemoFixtureService.status(scenarioId));
        }
        if (actionName == 'seed') {
            return toDto(JatakaDemoFixtureService.seed(scenarioId));
        }
        throw new IllegalArgumentException('Unsupported action: ' + actionName);
    }

    @HttpGet
    global static SeedResultDto getStatus() {
        String scenarioId = RestContext.request.params.get('scenarioId');
        return toDto(JatakaDemoFixtureService.status(scenarioId));
    }

    private static SeedResultDto toDto(JatakaDemoFixtureService.SeedResult source) {
        SeedResultDto dto = new SeedResultDto();
        dto.success = source.success;
        dto.message = source.message;
        dto.scenarioId = source.scenarioId;
        dto.records = new List<FixtureRecordDto>();
        if (source.records != null) {
            for (JatakaDemoFixtureService.FixtureRecord row : source.records) {
                FixtureRecordDto fr = new FixtureRecordDto();
                fr.objectApiName = row.objectApiName;
                fr.recordId = row.recordId;
                fr.externalKey = row.externalKey;
                fr.label = row.label;
                fr.status = row.status;
                fr.caseNumber = row.caseNumber;
                fr.created = row.created;
                dto.records.add(fr);
            }
        }
        return dto;
    }
}
