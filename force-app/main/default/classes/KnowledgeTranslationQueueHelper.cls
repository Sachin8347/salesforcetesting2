/**
 * L2 fixture: determines whether the running user belongs to a language-specific translation queue.
 * Knowledge Manager rights do not imply membership in the Spanish Translation Group.
 */
public with sharing class KnowledgeTranslationQueueHelper {
    private static final Map<String, String> LANGUAGE_TO_QUEUE = new Map<String, String>{
        KnowledgeTranslationPublishService.LANG_SPANISH =>
            KnowledgeTranslationPublishService.QUEUE_SPANISH
    };

    public static Boolean isCurrentUserQueueMember(String languageCode) {
        String queueName = LANGUAGE_TO_QUEUE.get(languageCode);
        if (String.isBlank(queueName)) {
            return true;
        }

        return isCurrentUserInNamedGroup(queueName);
    }

    public static Boolean isCurrentUserInNamedGroup(String groupDeveloperName) {
        List<GroupMember> memberships = [
            SELECT Id
            FROM GroupMember
            WHERE UserOrGroupId = :UserInfo.getUserId()
            AND Group.DeveloperName = :groupDeveloperName
            LIMIT 1
        ];
        return !memberships.isEmpty();
    }

    public static String getAssignedQueueForLanguage(String languageCode) {
        return LANGUAGE_TO_QUEUE.containsKey(languageCode)
            ? LANGUAGE_TO_QUEUE.get(languageCode)
            : null;
    }
}
