trigger AccountAfterUpdate on Account (after update) {
    FidelityRecursiveAccountHandler.afterUpdate(Trigger.new);
}
