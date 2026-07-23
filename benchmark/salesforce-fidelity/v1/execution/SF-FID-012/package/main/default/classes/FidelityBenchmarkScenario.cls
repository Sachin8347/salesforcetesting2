global with sharing class FidelityBenchmarkScenario {
    global static Map<String, Object> seed() {
        insert new List<Account>{
            new Account(Name = 'Fidelity UI Search Alpha'),
            new Account(Name = 'Fidelity UI Search Beta')
        };
        return new Map<String, Object>{
            'normalizedSearchTerm' => '%Fidelity UI Search%'
        };
    }

    global static Map<String, Object> run() {
        List<Account> result =
            FidelityAccountSearchController.search('%\' OR Name != \'');
        return new Map<String, Object>{'resultCount' => result.size()};
    }
}
