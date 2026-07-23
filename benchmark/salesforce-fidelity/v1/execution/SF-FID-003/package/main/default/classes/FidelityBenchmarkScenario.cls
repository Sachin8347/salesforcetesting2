global with sharing class FidelityBenchmarkScenario {
    global static Map<String, Object> seed() {
        List<Account> accounts = new List<Account>();
        for (Integer i = 0; i < 200; i++) {
            accounts.add(new Account(Name = 'Fidelity UI Quadratic ' + i));
        }
        insert accounts;
        List<Contact> contacts = new List<Contact>();
        for (Account accountRecord : accounts) {
            contacts.add(new Contact(
                AccountId = accountRecord.Id,
                LastName = accountRecord.Name
            ));
        }
        insert contacts;
        return new Map<String, Object>{
            'accountIds' => new Map<Id, Account>(accounts).keySet()
        };
    }

    global static Map<String, Object> run() {
        List<Account> accounts = [
            SELECT Id FROM Account WHERE Name LIKE 'Fidelity UI Quadratic %'
        ];
        Set<Id> accountIds = new Map<Id, Account>(accounts).keySet();
        List<Contact> contacts = [
            SELECT Id, AccountId FROM Contact WHERE AccountId IN :accountIds
        ];
        Integer beforeCpu = Limits.getCpuTime();
        Map<Id, Integer> scores =
            FidelityHiddenQuadraticService.scoreAccounts(accounts, contacts);
        return new Map<String, Object>{
            'accountCount' => accounts.size(),
            'contactCount' => contacts.size(),
            'resultCount' => scores.size(),
            'cpuMs' => Limits.getCpuTime() - beforeCpu
        };
    }
}
