class IndividualSearchCtrl extends IndividualListCtrl
    constructor:->
        super      
        @location.url("/") unless @routeParams.q?
    # Manage research here
    getVerbose: =>
        @scope.verbose_name = "individual"
        @scope.verbose_name_plural = "individuals"
        @Page.title @scope.verbose_name_plural          
    # Define search parameter using route's params
    getParams: =>
        # No query, no search
        return false unless @routeParams.q?
        id    : "rdf_search"
        limit : @scope.limit
        offset: @scope.limit * (@scope.page - 1)
        q     : @routeParams.q
        type  : "summary"

# Register the controller
angular.module('detective').controller 'individualSearchCtrl', IndividualSearchCtrl