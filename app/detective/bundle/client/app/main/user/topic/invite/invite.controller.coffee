class window.AddCollaboratorsCtrl
    # Injects dependancies
    @$inject: ['$scope', '$stateParams', '$state', 'Topic', 'Page', 'topic', 'collaborators', 'administrators', 'User', '$modal']
    constructor: (@scope,  @stateParams, @state, @Topic, @Page, @topic, collaborators, @administrators, @User, @modal)->
        @Page.title "Add new collaborators"
        @scope.topic = @topic
        # Transform search result
        @scope.prepareSearch = (objects=[])->
            # Fetchs and returns the objects list
            for object in objects
                # Create a new field "name" using the "username"
                object["name"] = object["username"]
                # Return the updated object
                object

        @scope.$watch "collaborator", (newVal, oldVal)=>
            if typeof newVal is typeof {}
                @scope.collaborator_name = newVal.username
        , yes

        # Send an invitation to the given person
        @scope.invite = ()=>
            collaborator = @scope.collaborator_name
            @scope.loading = yes
            @scope.invited = null

            @Topic.invite({id: @topic.id}, {collaborator: collaborator}, =>
                @scope.loading = no
                # Success notification
                @scope.invited = collaborator
                @scope.collaborator_name = ""
                @scope.collaborator = undefined
                do @updateCollaborators
            # Error
            , => @scope.loading = no)

        ##
        # Collaborators
        @collaborator_loading = []

        @scope.collaborators = collaborators

        @scope.orderCollaborators = @orderCollaborators
        @scope.isYou = @isYou
        @scope.isOwner = @isOwner
        @scope.isAdmin = @isAdmin
        @scope.changePermission = @changePermission
        @scope.removeCollaborator = @removeCollaborator
        #
        ##

    orderCollaborators: (user) =>
        if user.id is @topic.author.id then 1 else (if @isAdmin user then 2 else 3)

    isYou: (user) =>
        user.id is @User.id

    isOwner: (user) =>
        user.id is @topic.author.id

    isAdmin: (user) =>
        for admin in @administrators
            if admin.id is user.id
                return yes
        no

    changePermission: (user) =>
        modal = @modal.open
            templateUrl: '/partial/components/modal/modal.html'
            controller: ['$scope', ($scope) =>
                $scope.title = "Change the status of <strong>#{user.username}</strong> on the topic <strong>#{@topic.title}</strong>?"
                $scope.buttons =
                    yes : "Yes"
                    no : "No"
                $scope.modal = modal
            ]
        modal.result.then (isYes) =>
            if isYes
                @scope.loading = yes
                (@Topic.grant_admin { id : @topic.id }, { collaborator : user , grant : not (@isAdmin user) }).$promise.then =>
                    @scope.loading = no
                    do @updateCollaborators

    removeCollaborator: (user) =>
        modal = @modal.open
            templateUrl: '/partial/components/modal/modal.html'
            controller: ['$scope', ($scope) =>
                $scope.title = "Remove <strong>#{user.username}</strong> from the collaborators of the topic <strong>#{@topic.title}</strong>?"
                $scope.buttons =
                    yes : "Yes"
                    no : "No"
                $scope.modal = modal
            ]
        modal.result.then (isYes) =>
            if isYes
                @scope.loading = yes
                @Topic.leave { id : @topic.id }, { collaborator : user.id }, =>
                    @scope.loading = no
                    do @updateCollaborators

    updateCollaborators: =>
        @scope.loading = yes
        (@Topic.collaborators { id : @topic.id }).$promise.then (data) =>
            @scope.loading = no
            @scope.collaborators = data
        (@Topic.administrators { id : @topic.id }).$promise.then (data) =>
            @administrators = data

    @resolve:
        collaborators: ["Topic", "topic", (Topic, topic) ->
            (Topic.collaborators id : topic.id).$promise
        ]
        administrators: ["Topic", "topic", (Topic, topic) ->
            (Topic.administrators id : topic.id).$promise
        ]

angular.module('detective').controller 'addCollaboratorsCtrl', AddCollaboratorsCtrl