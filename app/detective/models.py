from .utils                     import get_topics
from app.detective              import utils
from app.detective.permissions  import create_permissions, remove_permissions
from django.contrib.auth.models import User
from django.core.exceptions     import ValidationError
from django.db                  import models
from django.db.models.fields    import FieldDoesNotExist
from jsonfield                  import JSONField
from tinymce.models             import HTMLField
from django.contrib.auth.models import Group

import inspect
import os
import random
import string

PUBLIC = (
    (True, "Yes, public"),
    (False, "No, just for a small group of users"),
)

FEATURED = (
    (True, "Yes, show it on the homepage"),
    (False, "No, stay out of the ligth"),
)

class QuoteRequest(models.Model):
    RECORDS_SIZE = (
        (0, "Less than 200"),
        (200, "Between 200 and 1000"),
        (1000, "Between 1000 & 10k"),
        (10000, "More than 10k"),
        (-1, "I don't know yet"),
    )
    USERS_SIZE = (
        (1, "1"),
        (5, "1-5"),
        (0, "More than 5"),
        (-1, "I don't know yet"),
    )
    name     = models.CharField(max_length=100)
    employer = models.CharField(max_length=100)
    email    = models.EmailField(max_length=100)
    phone    = models.CharField(max_length=100, blank=True, null=True)
    domain   = models.TextField(help_text="Which domain do you want to investigate on?")
    records  = models.IntegerField(choices=RECORDS_SIZE, blank=True, null=True, help_text="How many entities do you plan to store?")
    users    = models.IntegerField(choices=USERS_SIZE, blank=True, null=True, help_text="How many people will work on the investigation?")
    public   = models.NullBooleanField(choices=PUBLIC, null=True, help_text="Will the data be public?")
    comment  = models.TextField(blank=True, null=True, help_text="Anything else you want to tell us?")

    def __unicode__(self):
        return "%s - %s" % (self.name, self.email,)

class Topic(models.Model):
    title            = models.CharField(max_length=250, help_text="Title of your topic.")
    # Value will be set for this field if it's blank
    slug             = models.SlugField(max_length=250, unique=True, help_text="Token to use into the url.")
    description      = HTMLField(null=True, blank=True, help_text="A short description of what is your topic.")
    about            = HTMLField(null=True, blank=True, help_text="A longer description of what is your topic.")
    public           = models.BooleanField(help_text="Is your topic public?", default=True, choices=PUBLIC)
    featured         = models.BooleanField(help_text="Is your topic a featured topic?", default=False, choices=FEATURED)
    background       = models.ImageField(null=True, blank=True, upload_to="topics", help_text="Background image displayed on the topic's landing page.")
    author           = models.ForeignKey(User, help_text="Author of this topic.", null=True)
    ontology_as_owl  = models.FileField(null=True, blank=True, upload_to="ontologies", verbose_name="Ontology as OWL", help_text="Ontology file that descibes your field of study.")
    ontology_as_mod  = models.SlugField(blank=True, max_length=250, verbose_name="Ontology as a module", help_text="Module to use to create your topic.")
    ontology_as_json = JSONField(null=True, verbose_name="Ontology as JSON", blank=True)

    def __unicode__(self):
        return self.title

    def get_contributor_group(self):
        try:
            return Group.objects.get(name="%s_contributor" % self.app_label())
        except Group.DoesNotExist:
            create_permissions(self.get_module(), app_label=self.ontology_as_mod)
            return Group.objects.get(name="%s_contributor" % self.app_label())

    def app_label(self):
        if self.slug in ["common", "energy"]:
            return self.slug
        elif not self.ontology_as_mod:
            # Already saved topic
            if self.id:
                cache_key = "prefetched_topic_%s" % self.id
                # Store topic object in a temporary attribute
                # to avoid SQL lazyness
                if getattr(self, cache_key, None) is None:
                    topic = Topic.objects.get(id=self.id)
                    setattr(self, cache_key, topic)
                else:
                    topic = getattr(self, cache_key)
                # Restore the previous ontology_as_mod value
                self.ontology_as_mod = topic.ontology_as_mod
                # Call this function again.
                # Continue if ontology_as_mod is still empty
                if self.ontology_as_mod: return self.app_label()
            while True:
                token = Topic.get_module_token()
                # Break the loop only if the token doesn't exist
                if not Topic.objects.filter(ontology_as_mod=token).exists(): break
            # Save the new token
            self.ontology_as_mod = token
            # Save a first time if no idea given
            models.Model.save(self)
        return self.ontology_as_mod

    @staticmethod
    def get_module_token(size=10, chars=string.ascii_uppercase + string.digits):
        return "topic%s" % ''.join(random.choice(chars) for x in range(size))

    def get_module(self):
        from app.detective import topics
        return getattr(topics, self.app_label())

    def get_models_module(self):
        """ return the module topic_module.models """
        return getattr(self.get_module(), "models", {})

    def get_models(self):
        """ return a list of Model """
        # We have to load the topic's model
        models_module = self.get_models_module()
        models_list   = []
        for i in dir(models_module):
            klass = getattr(models_module, i)
            # Collect every Django's model subclass
            if inspect.isclass(klass) and issubclass(klass, models.Model):
                models_list.append(klass)
        return models_list

    def clean(self):
        models.Model.clean(self)

    def save(self, *args, **kwargs):
        # Ensure that the module field is populated with app_label()
        self.ontology_as_mod = self.app_label()
        # Call the parent save method
        super(Topic, self).save(*args, **kwargs)
        # Refresh the API
        self.reload()

    def reload(self):
        from app.detective.register import topic_models
        # Register the topic's models again
        topic_models(self.get_module().__name__, force=True)

    def has_default_ontology(self):
        try:
            module = self.get_module()
        except ValueError: return False
        # File if it's a virtual module
        if not hasattr(module, "__file__"): return False
        directory = os.path.dirname(os.path.realpath( module.__file__ ))
        # Path to the ontology file
        ontology  = "%s/ontology.owl" % directory
        return os.path.exists(ontology) or hasattr(self.get_module(), "models")

    def get_absolute_path(self):
        if self.author is None:
            return None
        else:
            return "/%s/%s" % (self.author.username, self.slug,)

    def get_absolute_url(self): return self.get_absolute_path()

    def link(self):
        path = self.get_absolute_path()
        if path is None:
            return ''
        else:
            return '<a href="%s">%s</a>' % (path, path, )

    link.allow_tags = True

    @property
    def search_placeholder(self, max_suggestion=5):
        from app.detective import register
        # Get the model's rules manager
        rulesManager = register.topics_rules()
        # List of searchable models
        searchableModels = []
        # Filter searchable models
        for model in self.get_models():
            if rulesManager.model(model).all().get("is_searchable", False):
                searchableModels.append(model)
        names = [ sm._meta.verbose_name_plural.lower() for sm in searchableModels ]
        random.shuffle(names)
        # No more than X names
        if len(names) > max_suggestion:
            names = names[0:max_suggestion]
        if len(names):
            return "Search for " + ", ".join(names[0:-1]) + " and " + names[-1]
        else:
            return "Search..."

    @property
    def module(self):
        return self.ontology_as_mod

class TopicToken(models.Model):
    topic      = models.ForeignKey(Topic, help_text="The topic this token is related to.")
    token      = models.CharField(editable=False, max_length=32, help_text="Title of your article.")
    email      = models.CharField(max_length=255, default=None, null=True, help_text="Email to invite.")
    created_at = models.DateTimeField(auto_now_add=True, default=None, null=True)

    class Meta:
        unique_together = ('topic', 'email',)

    @staticmethod
    def get_random_token(size=32, chars=string.ascii_letters + string.digits):
        return ''.join(random.choice(chars) for x in range(size))

    def save(self):
        if not self.id:
            self.token = self.get_random_token()
            try:
                TopicToken.objects.get(topic=self.topic, token=self.token)
                # Recurcive call to regenerate a random token
                return self.save()
            except TopicToken.DoesNotExist:
                # The topic token MUST not exist yet
                pass
        super(TopicToken, self).save()


class Article(models.Model):
    topic      = models.ForeignKey(Topic, help_text="The topic this article is related to.")
    title      = models.CharField(max_length=250, help_text="Title of your article.")
    slug       = models.SlugField(max_length=250, unique=True, help_text="Token to use into the url.")
    content    = HTMLField(null=True, blank=True)
    public     = models.BooleanField(default=False, help_text="Is your article public?")
    created_at = models.DateTimeField(auto_now_add=True, default=None, null=True)

    def get_absolute_path(self):
        return self.topic.get_absolute_path() + ( "p/%s/" % self.slug )

    def __unicode__(self):
        return self.title

    def link(self):
        path = self.get_absolute_path()
        return '<a href="%s">%s</a>' % (path, path, )
    link.allow_tags = True


# This model aims to describe a research alongside a relationship.
class SearchTerm(models.Model):
    # This field is deduced from the relationship name
    subject    = models.CharField(null=True, blank=True, default='', editable=False, max_length=250, help_text="Kind of entity to look for (Person, Organization, ...).")
    # This field is set automaticly too according the choosen name
    is_literal = models.BooleanField(editable=False, default=False)
    # Every field are required
    label      = models.CharField(null=True, blank=True, default='', max_length=250, help_text="Label of the relationship (typically, an expression such as 'was educated in', 'was financed by', ...).")
    # This field will be re-written by app.detective.admin
    # to be allow dynamic setting of the choices attribute.
    name       = models.CharField(max_length=250, help_text="Name of the relationship inside the subject.")
    topic      = models.ForeignKey(Topic, help_text="The topic this relationship is related to.")

    def find_subject(self):
        subject = None
        # Retreive the subject that match with the instance's name
        field = self.field
        # If any related_model is given, that means its subject is is parent model
        if field is not None:
            subject = field["model"]
            return subject
        else:
            return None

    def clean(self):
        self.subject    = self.find_subject()
        self.is_literal = self.type == "literal"
        models.Model.clean(self)

    @property
    def field(self):
        field = None
        if self.name:
            # Build a cache key with the topic token
            cache_key = "%s__%s__field" % ( self.topic.ontology_as_mod, self.name )
            # Try to use the cache value
            if getattr(self, cache_key, None) is not None:
                field = getattr(self, cache_key)
            else:
                topic_models = self.topic.get_models()
                for model in topic_models:
                    # Retreive every relationship field for this model
                    for f in utils.get_model_fields(model):
                        if f["name"] == self.name:
                            field = f
            # Very small cache to optimize recording
            setattr(self, cache_key, field)
        return field

    @property
    def type(self):
        field = self.field
        if field is None:
            return None
        elif field["type"] == "Relationship":
            return "relationship"
        else:
            return "literal"

    @property
    def target(self):
        if 'related_model' in self.field:
            return self.field["related_model"]
        else:
            return None

# -----------------------------------------------------------------------------
#
#    SIGNALS
#
# -----------------------------------------------------------------------------
from django.db.models import signals

def update_permissions(*args, **kwargs):
    """ create the permissions related to the label module """
    assert kwargs.get('instance')
    # @TODO check that the slug changed or not to avoid permissions hijacking
    if kwargs.get('created', False):
        create_permissions(kwargs.get('instance').get_module(), app_label=kwargs.get('instance').ontology_as_mod)

signals.post_delete.connect(remove_permissions, sender=Topic)
signals.post_save.connect(update_permissions, sender=Topic)
# EOF