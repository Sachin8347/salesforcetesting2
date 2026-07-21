@IsTest
private class DeepCallChainTest {
    @IsTest
    static void execute_processesEveryValueThroughTheFullChain() {
        List<String> results = DeepCallChainA.execute(
            new List<String>{ ' alpha ', 'beta', null }
        );

        System.assertEquals(
            new List<String>{ 'Item 1: ALPHA', 'Item 2: BETA', 'Item 3: ' },
            results
        );
    }

    @IsTest
    static void execute_handlesNullAndEmptyLists() {
        System.assertEquals(0, DeepCallChainA.execute(null).size());
        System.assertEquals(
            0,
            DeepCallChainA.execute(new List<String>()).size()
        );
    }
}
