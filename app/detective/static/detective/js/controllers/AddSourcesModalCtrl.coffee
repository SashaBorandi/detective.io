class window.AddSourcesModalCtrl
    # Injects dependencies
    @$inject: ['$scope', '$q', '$filter', '$modalInstance', 'Individual', 'UtilsFactory', "fields", "field", "meta"]
    constructor: (@scope, @q, @filter, @modalInstance, @Individual, @UtilsFactory,  @fields, @field, @meta)->
        @fields = angular.copy @fields
        @fields.field_sources = [] if not @fields.field_sources?
        @updateMasterSources()
        # Scope variables
        @scope.loading    = no
        @scope.individual = @Individual
        # Description of the model's fields
        @scope.meta = @meta

        # Scope functions
        # Cancel button just closes the modal
        @scope.cancel           = @close
        @scope.save             = @save
        @scope.updateSource     = @updateSource
        @scope.addSource        = @addSource
        @scope.deleteSource     = @deleteSource
        @scope.getFieldValue    = @getFieldValue
        @scope.getSources       = @getSources
        @scope.getSourcesRefs   = @getSourcesRefs
        @scope.isSourceURLValid = @isSourceURLValid

        # Description of the relationship (source, target, through model)
        @scope.fields = @fields

    close: (result=@fields.field_sources)=>
        @modalInstance.close(result)

    save: (form, close=no)=>
        # if form is passed to the save function it has to be valid.
        return unless form.$valid if form?
        @scope.focused = undefined
        @scope.loading = yes
        @meta.updating[@field.name] = true
        data  =
            field_sources: @cleanSources()
        params  =
            id:   @meta.id
            type: @meta.type

        # Update individual sources
        promise = @Individual.update(params, data).$promise

        promise.then (data)=>
            @updateMasterSources()

            @scope.loading = no
            @meta.updating[@field.name] = false

            @close(@fields.field_sources) if close

    isFieldRich: (field)=>
        field.rules.is_rich or no

    getFieldValue: ()=>
        field_value = @fields[@field.name]
        # field type switch
        switch @field.type
            when 'CharField'
                if @isFieldRich(@field)
                    field_value = @field.verbose_name
            when 'DateTimeField'
                format  = "shortDate"
                field_value =  @filter("date")(field_value, format)
            when 'Relationship'
                field_value = @field.verbose_name

        unless field_value?
            field_value = @field.verbose_name

        field_value


    getSources: (fields=@fields) => _.where fields.field_sources, field: @field.name

    getSourcesRefs: ()=> _.map @getSources(), (s)-> s.reference

    addSource: (value)=>
        @fields.field_sources.push
            reference: value
            field: @field.name

        @scope.focused = value

    cleanSources: =>
        _.map @fields.field_sources, (v)-> _.omit v, 'focus'

    updateMasterSources: =>
        @master_sources = @getSources angular.copy @fields

    deleteSource: (source, $event)=>
        @fields.field_sources = _.reject @fields.field_sources, _.matches
                field: source.field
                reference: source.reference
        @scope.focused = undefined

    hasSources: =>
        sources = @getSources()
        (not _.isEmpty sources) and _.some sources, (e)-> e? and e.reference?

    isSourceURLValid: (source)=>
        return false unless source?
        @UtilsFactory.isValidURL(source.reference)

angular.module('detective.controller').controller 'addSourcesModalCtrl', AddSourcesModalCtrl