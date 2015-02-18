import inspect

# Class that manage rules througt a local object name
class HasRules(object):
    def __init__(self):
        # Default rules for this object
        self.registered_rules = {}

    # Add a rule
    def add(self, **kwargs):
        # Treats arguments as a dictionary of rules
        for name, value in kwargs.items():
            # Each rule can only have one value
            self.set(name, value)
        # Allows chaining
        return self

    # Get all registered rules
    def all(self): return self.registered_rules
    # Get one rule
    def get(self, name, default=None): return self.all().get(name, default)
    # Set a rule with key/value pair
    def set(self, name, value):
        self.registered_rules[name] = value
        # Allows chaining
        return self

# Field class to register rules associated to a field
class Field(HasRules):
    def __init__(self, name, model):
        self.name = name
        self.model = model
        # Call parent constructor
        super(Field, self).__init__()
        # Default rules for this models
        self.registered_rules["is_visible"] = True
        self.registered_rules["priority"] = 0

# Model class to register rules associated to a model
class Model(HasRules):
    # Record the associated model
    def __init__(self, model):
        # Check that the model is a class
        if not inspect.isclass(model): print model
        if not inspect.isclass(model) or not hasattr(model, "_meta"):
            raise Exception("You can only registed model's class.")
        self.model = model
        self.name  = "%s.%s" % (model.__module__, model.__name__)
        # Get the model fields
        self.field_names = model._meta.get_all_field_names()
        # Field of the model
        self.registered_fields = {}
        # Register all field
        for name in self.field_names: self.register_field(name)
        # Call parent constructor
        super(Model, self).__init__()
        # Default rules for this models
        self.registered_rules["is_editable"]   = True
        self.registered_rules["is_searchable"] = True


    # Register a field rule
    def register_field(self, field):
        # If the field is not registered yet
        if field not in self.registered_fields:
            # Register the field
            self.registered_fields[field] = Field(name=field, model=self.model)

        return self.registered_fields[field]

    # Shortcut to register field
    field = register_field
    # List of registered model ordered by priority
    def fields(self, ordered=True):
        if not ordered:
            return self.registered_fields
        else:
            def sortkey(field):
                return (
                    -field.get("is_visible"),
                    -field.get("priority"),
                    field.name
                )
            # Sor the list
            return sorted(self.registered_fields.values(), key=sortkey)


# This class is a Singleton that register model layout
# @src http://stackoverflow.com/questions/42558/python-and-the-singleton-pattern
class ModelRules(object):

    __instance = None
    # Override __new__ to avoid create new instance (singleton)
    def __new__(self, *args, **kwargs):
        if not self.__instance:
            self.__instance = super(ModelRules, self).__new__(self, *args, **kwargs)
            # List of registered model
            self.registered_models = {}
        return self.__instance

    # This method will add the given model to the register list
    def register_model(self, model):
        name  = "%s.%s" % (model.__module__, model.__name__)
        # Soft validation:
        # we stop double registering
        # without raise an exception
        if name not in self.registered_models:
            self.registered_models[name] = Model(model)

        return self.registered_models[name]

    # Get model (shortcut to register_model)
    model = register_model
    # List of registered model
    def models(self): return self.registered_models

    # Get model's rules by its name
    def by_name(self, name):
        for model in self.registered_models:
            rules = self.registered_models[model]
            if rules.name == name: return rules
        return None
