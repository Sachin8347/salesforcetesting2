/**
 * DEMO TRAP — Limit Firewall / JATAKA_PROFILE.
 * Intentionally anti-pattern: SOQL + DML inside a for-loop.
 * Do not use in production logic. Exists so Kamikaze can project O(n²)
 * governor-limit breaches at scale (e.g. 15k records).
 */
public with sharing class BadLoopExample {
    public void updateAccounts(List<Account> accs) {
        if (accs == null) {
            return;
        }
        for (Account a : accs) {
            // THE POISON PILL: SOQL inside a FOR loop
            List<Contact> cons = [
                SELECT Id
                FROM Contact
                WHERE AccountId = :a.Id
            ];
            a.Description = 'Updated ' + String.valueOf(cons.size()) + ' contacts';
            // THE POISON PILL: DML inside a FOR loop
            update a;
        }
    }
}
