from aiogram.fsm.state import State, StatesGroup


class ConsentStates(StatesGroup):
    general = State()
    special = State()


class QuestionnaireStates(StatesGroup):
    # ── ЭТАП 1: Быстрый старт (10 вопросов) ──
    q1_name = State()              # 1. Имя
    q2_birth_year = State()        # 2. Год рождения
    q2_confirm_age = State()
    q3_height = State()            # 2C. Рост (часть вопроса 2)
    q4_body_type = State()         # 4. Телосложение
    q12_nationality = State()      # 5. Национальность
    q6_city = State()              # 6. Город (кнопки)
    q6_district = State()          # 6b. Район (текст)
    q5_education = State()         # 7. Образование
    q5_university = State()
    q6_work_choice = State()       # 8. Работа
    q6_occupation = State()
    q16_religiosity = State()      # 9. Религиозность
    q_marital_status = State()     # 10. Семейное положение
    q_children = State()           # 10b. Дети (только если разведён/вдовец)
    q21_photo_type = State()       # 3. Фото (позиция 3 в анкете)
    q21_photo_upload = State()
    q22_parent_phone = State()     # Телефон (необязательно, убран из Этапа 1)
    stage1_complete = State()      # Экран завершения Этапа 1

    # ── ЭТАП 2: Расширенный профиль ──
    ext_housing = State()
    ext_housing_parent = State()
    ext_car = State()
    ext_address = State()
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
    ext_parent_phone = State()
    ext_parent_telegram = State()
    ext_candidate_telegram = State()
    ext_address_text = State()
    ext_address_link = State()
    ext_location = State()
    ext_confirm = State()


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
    summary = State()           # Экран резюме анкеты
    confirm = State()


class SearchStates(StatesGroup):
    browsing = State()
    filter_age = State()  # ожидаем ввод возраста "20-30" (legacy)
    age_from = State()    # ввод нижней границы кастомного диапазона
    age_to = State()      # ввод верхней границы кастомного диапазона


class PaymentStates(StatesGroup):
    choose_method = State()
    awaiting_screenshot = State()
    awaiting_contact_screenshot = State()  # Скриншот оплаты за контакт


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


class EditProfileStates(StatesGroup):
    name = State()
    birth_year = State()
    height_weight = State()
    city = State()
    occupation = State()
    photo = State()
    phone = State()

class ModeratorReplyStates(StatesGroup):
    awaiting_reply = State()
