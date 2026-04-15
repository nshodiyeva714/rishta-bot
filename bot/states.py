from aiogram.fsm.state import State, StatesGroup


class ConsentStates(StatesGroup):
    general = State()
    special = State()


class LanguageStates(StatesGroup):
    choose = State()


class QuestionnaireStates(StatesGroup):
    q1_name = State()
    q2_birth_year = State()
    q2_confirm_age = State()
    q3_height = State()
    q4_weight = State()
    q5_education = State()
    q5_university = State()
    q6_occupation = State()
    q7_housing = State()
    q7_parent_housing = State()
    q8_car = State()
    q9_city_district = State()
    q9_address = State()
    q10b_search_scope = State()
    q10b_preferred_city = State()
    q10b_preferred_district = State()
    q10b_preferred_country = State()
    q11_family_region = State()
    q12_nationality = State()
    q13_father = State()
    q14_mother = State()
    q15_brothers = State()
    q15_sisters = State()
    q15_position = State()
    q16_religiosity = State()
    q17_marital = State()
    q18_children = State()
    q19_health = State()
    q20_character = State()
    q20a_ideal_family = State()
    q20a_qualities = State()
    q20a_plans = State()
    q21_photo_type = State()
    q21_photo_upload = State()
    q22_parent_phone = State()
    q22_parent_telegram = State()
    q22_candidate_telegram = State()
    q22_location = State()
    q23_status = State()


class TariffStates(StatesGroup):
    choose = State()


class RequirementStates(StatesGroup):
    age = State()
    education = State()
    residence = State()
    residence_city = State()
    residence_district = State()
    nationality = State()
    religiosity = State()
    marital_status = State()
    children = State()
    car_required = State()
    housing_required = State()
    job_required = State()
    other_wishes = State()
    confirm = State()


class SearchStates(StatesGroup):
    browsing = State()


class PaymentStates(StatesGroup):
    choose_method = State()
    awaiting_screenshot = State()


class MeetingStates(StatesGroup):
    date = State()
    time = State()


class FeedbackStates(StatesGroup):
    result = State()
    story = State()


class ComplaintStates(StatesGroup):
    reason = State()
    details = State()


class ModeratorContactStates(StatesGroup):
    awaiting_message = State()


class ModeratorReplyStates(StatesGroup):
    awaiting_reply = State()
