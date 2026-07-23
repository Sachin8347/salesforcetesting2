global with sharing class FidelityBenchmarkScenario {
    global static Map<String, Object> seed() {
        Account parent = new Account(Name = 'Fidelity UI Contract');
        insert parent;
        Contract record = new Contract(
            AccountId = parent.Id,
            StartDate = Date.newInstance(2026, 1, 1),
            ContractTerm = 12,
            Status = 'Draft'
        );
        insert record;
        return new Map<String, Object>{'contractId' => record.Id};
    }

    global static Map<String, Object> run() {
        Datetime boundary = Datetime.newInstanceGmt(2026, 1, 1, 0, 30, 0);
        return new Map<String, Object>{
            'renewalDate' => FidelityRenewalDateService.renewalDate(boundary),
            'expectedUtcDate' => Date.newInstance(2026, 1, 1)
        };
    }
}
