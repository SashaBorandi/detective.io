angular.module('detective').config ["$stateProvider", ($stateProvider)->
    $stateProvider.state('user-topic-create.batch',
        controller: EditTopicBatchCtrl
        templateUrl: '/partial/main/home/dashboard/create/batch/batch.html'
    )
]