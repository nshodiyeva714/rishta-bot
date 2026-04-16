from aiogram.fsm.state import State, StatesGroup


class ConsentStates(StatesGroup):
    general = State()
    special = State()


class LanguageStates(StatesGroup):
    choose = State()


class QuestionnaireStates(StatesGroup):
    # ── ЭТАП 1: Быстрый старт (10 вопросов) ──
    q1_name = State()              # 1. Имя
    q2_birth_year = State()        # 2. Год рождения
    q2_confirm_age = State()
    q3_height = State()            # 3. Рост
    q4_weight = State()            # 4. Вес
    q12_nationality = State()      # 5. Национальность
    q9_city_district = State()     # 6. Город и район
    q5_education = State()         # 7. Образование
    q5_university = State()
    q6_work_choice = State()       # 8. Работа
    q6_occupation = State()
    q16_religiosity = State()      # 9. Религиозность
    q_marital_status = State()     # 10. Семейное положение
    q_children = State()           # 10b. Дети (только если разведён/вдовец)
    q21_photo_type = State()       # Фото (необязательно)
    q21_photo_upload = State()
    q22_parent_phone = State()     # Телефон (необязательно)

    # ── ЭТАП 2: Расширенный профиль ──
    ext_housing = State()
    ext_housing_parent = State()
    ext_car = State()
    ext_address = State()
    ext_search_scope = State()
    ext_preferred_city = State()
    ext_preferred_district = State()
    ext_preferred_country = State()
    ext_family_region = State()
    ext_father = State()
    ext_mother = State()
    ext_brothers = State()
    ext_sisters = State()
    ext_position = State()
    ext_health = State()
    ext_character = State()
    ext_ideal_family = State()
    ext_qualities = State()
    ext_plans = State()
    ext_parent_telegram = State()
    ext_candidate_telegram = State()
    ext_location = State()
    ext_status = State()
    ext_confirm = State()

    # Legacy (для обратной совместимости — не используются в новом потоке)
    q7_housing = State()
    q7_parent_housing = State()
    q8_car = State()
    q9_address = State()
    q10b_search_scope = State()
    q10b_preferred_city = State()
    q10b_preferred_district = State()
    q10b_preferred_country = State()
    q11_family_region = State()
    q13_father = State()
    q14_mother = State()
    q15_brothers = State()
    q15_sisters = State()
    q15_position = State()
    q17_marital = State()
    q18_children = State()
    q19_health = State()
    q20_character = State()
    q20a_ideal_family = State()
    q20a_qualities = State()
    q20a_plans = State()
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
    filter_age = State()  # ожидаем ввод возраста "20-30"


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


class FeedbackSuggestionStates(StatesGroup):
    awaiting_text = State()


class ModeratorContactStates(StatesGroup):
    awaiting_message = State()


class ModeratorReplyStates(StatesGroup):
    awaiting_reply = State()
