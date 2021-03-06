from app.detective.topics.energy.models import *
from app.detective.modelrules           import ModelRules
from app.detective.neomatch             import Neomatch
from app.detective.models               import *

def topics_rules():
    # ModelRules is a singleton that record every model rules
    rules = ModelRules()
    # Disable editing on some model
    rules.model(Country).add(is_editable=False)
    # Records "invisible" fields
    rules.model(FundraisingRound).field("personal_payer").add(is_visible=False)
    rules.model(Organization).field("adviser").add(is_visible=False)
    rules.model(Organization).field("board_member").add(is_visible=False)
    rules.model(Organization).field("company_register_link").add(is_visible=False)
    rules.model(Organization).field("litigation_against").add(is_visible=False)
    rules.model(Organization).field("monitoring_body").add(is_visible=False)
    rules.model(Organization).field("partner").add(is_visible=False)
    rules.model(Organization).field("website_url").add(is_visible=False)
    rules.model(Person).field("previous_activity_in_organization").add(is_visible=False)
    rules.model(Person).field("website_url").add(is_visible=False)
    rules.model(EnergyProduct).field("operator").add(is_visible=False)
    rules.model(EnergyProject).field("ended").add(is_visible=False)
    rules.model(EnergyProject).field("partner").add(is_visible=False)

    rules.model(Country).add(person_set=Neomatch(
        title="Persons educated or based in this country",
        target_model=Person,
        match="""
            (root)<-[r:`person_has_based_in+`|`person_has_educated_in+`]-({select})
        """
    ))

    rules.model(Person).add(organizationkey_set=Neomatch(
        title="Organizations this person has a key position in",
        target_model=Organization,
        match="""
            (root)-[:`organization_has_key_person+`]-({select})
        """
    ))

    rules.model(Person).add(organizationadviser_set=Neomatch(
        title="Organizations this person is an adviser to",
        target_model=Organization,
        match="""
            (root)-[:`organization_has_adviser+`]-({select})
        """
    ))

    rules.model(Person).add(organizationboard_set=Neomatch(
        title="Organizations this person is a board member of",
        target_model=Organization,
        match="""
            (root)-[:`organization_has_board_member+`]-({select})
        """
    ))


    rules.model(Country).add(product_set= Neomatch(
        title="Energy products distributed in this country",
        target_model=EnergyProduct,
        match="""
            (root)<--()<-[:`energy_product_has_distribution+`]-({select})
        """
    ))

    rules.model(Country).add(project_set=Neomatch(
        title="Energy projects active in this country",
        target_model=EnergyProject,
        match="""
            (root)-[:`energy_project_has_activity_in_country+`]-({select})
        """
    ))

    rules.model(EnergyProduct).add(country_set= Neomatch(
        title="Countries where this product is distributed",
        target_model=Country,
        match="""
            (root)-[:`energy_product_has_distribution+`]-()-[:`distribution_has_activity_in_country+`]-({select})
        """
    ))

    rules.model(Organization).add(energyproject_set=Neomatch(
        title="Energy projects this organization owns",
        target_model=EnergyProject,
        match="""
            (root)-[:`energy_project_has_owner+`]-({select})
        """
    ))

    rules.model(EnergyProduct).add(energyproduct_set=Neomatch(
        title="Energy project this product belongs to",
        target_model=EnergyProject,
        match="""
            (root)-[:`energy_project_has_product+`]-({select})
        """
    ))

    rules.model(Price).add(transform='{currency} {units}')
    rules.model(FundraisingRound).add(transform='{currency} {units}')

    def to_twitter_profile_url(data, field=None):
        th = data["twitter_handle"]
        if not th:
            return th
        elif th.startswith("http://") or th.startswith("https://"):
            return th
        elif th.startswith("@"):
            return "http://twitter.com/%s" % th[1:]
        else:
            return "http://twitter.com/%s" % th

    rules.model(Organization).field("twitter_handle").add(transform=to_twitter_profile_url)
    rules.model(Person).field("twitter_handle").add(transform=to_twitter_profile_url)
    rules.model(EnergyProject).field("twitter_handle").add(transform=to_twitter_profile_url)

    return rules