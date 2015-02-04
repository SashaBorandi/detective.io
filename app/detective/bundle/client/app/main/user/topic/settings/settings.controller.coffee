#=require TopicFormCtrl
class window.EditTopicCtrl extends window.TopicFormCtrl
    @$inject: TopicFormCtrl.$inject.concat ['$rootScope', 'topic', 'TopicSkeleton']
    constructor: (@scope, @state, @TopicsFactory, @Page, @User, @EVENTS, @rootScope, @topic, @TopicSkeleton)->
        super
        @init   = yes
        @master = angular.copy @topic
        # Scope attributes
        @scope.topic = @topic
        @scope.saved = no
        # Scope methods
        @scope.deleteTopicBackground = @deleteTopicBackground

        @scope.$on @EVENTS.topic.user_updated, (e, previous, next)=>
            # workaround to properly handle saved state & avoid "saved" state
            # on init
            changes = @topicChanges @scope.topic
            @scope.saved = _.isEmpty(changes) and not @init
            # we leave the init mode
            @init = no if @init

        @scope.$on @EVENTS.topic.updated, (e, topic)=>
            # avoid reference binding, otherwise @topicChanges will return an
            # empty object everytime.
            @master = angular.copy topic

        @Page.title "Settings of #{@topic.title}"

    deleteTopicBackground: =>
        @topic.background = null

    topicChanges: (topic)=>
        clean = (val)->
            val = angular.copy val
            if val == "" or val == undefined
                # Empty input must be null
                val = null
            val
        now = topic
        prev = @master
        changes = {}
        for prop of now
            now_val  = clean now[prop]
            prev_val = clean prev[prop]
            if typeof now_val isnt "function" and prop.indexOf("$") != 0
                unless angular.equals prev_val, now_val
                    changes[prop] = now_val
        changes

    edit: (panel='main')=>
        @scope.loading[panel] = yes
        @scope.saved = no
        changes = @topicChanges @scope.topic

        @TopicsFactory.update id: @scope.topic.id, changes, (data)=>
                @scope.$broadcast @EVENTS.topic.updated, data
                @scope.saved = yes
                @scope.loading[panel] = no
            , (response)=>
                @scope.loading[panel] = no
                @scope.saved = no
                if response.status is 400
                    @scope.error = response.data.topic



angular.module('detective').controller 'editTopicCtrl', EditTopicCtrl