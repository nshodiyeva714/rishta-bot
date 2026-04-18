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
    q12_nationality_custom = State()  # 5a. Ввод своей национальности
    q6_city = State()              # 6. Страна (кнопки)
    q6_region = State()            # 6a. Область Узбекистана (кнопки)
    q6_district = State()          # 6b. Район (текст)
    q5_education = State()         # 7. Образование
    q5_university = State()
    q6_work_choice = State()       # 8. Работа
    q6_occupation = State()
    q16_religiosity = State()      # 9. Религиозность
    q_marital_status = State()     # 10. Семейное положение
    q_children = State()           # 10b. Дети (только если разведён/вдовец)
    q11_parent_phone = State()     # 11. Телефон родителей (обязательно)
    q12_parent_telegram = State()  # 12. TG родителей (skip, но хотя бы один TG)
    q13_candidate_telegram = State()  # 13. TG кандидата (skip, но хотя бы один TG)
    q14_address = State()          # 14. Адрес — выбор (text/geo/link/skip)
    q14_address_text = State()     # 14a. Ввод текста адреса
    q14_location = State()         # 14b. Ожидание геоточки
    q14_address_link = State()     # 14c. Ввод ссылки на карту
    q21_photo_type = State()       # 3. Фото (позиция 3 в анкете)
    q21_photo_upload = State()
    q22_parent_phone = State()     # Телефон (необязательно, убран из Этапа 1)
    stage1_complete = State()      # Экран завершения Этапа 1

    # ── ЭТАП 2: Расширенный профиль ──
    ext_housing = State()
    ext_housing_parent = State()
    ext_car = State()
    ext_address = State()
    ext_father = State()
    ext_mother = State()
    ext_brothers = State()
    ext_sisters = State()
    ext_position = State()
    ext_health = State()
    ext_character = State()
    ext_ideal_family = State()
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
    nationality = State()
    nationality_custom = State()
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
    story = State()


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
    nationality_custom = State()
    parent_phone = State()
    parent_telegram = State()
    candidate_telegram = State()
    # ── Новые поля Этапа 2 ──
    father = State()
    mother = State()
    siblings_brothers = State()
    siblings_sisters = State()
    siblings_position = State()
    character = State()
    health = State()
    about = State()
    housing = State()
    housing_parent = State()
    car = State()
    address = State()             # выбор text/geo/link
    address_text = State()
    address_location = State()    # reply-kb геоточка
    address_link = State()

class ModeratorReplyStates(StatesGroup):
    awaiting_reply = State()


class ModeratorEditStates(StatesGroup):
    choosing_field = State()
    editing_value = State()


class ContactStates(StatesGroup):
    waiting_screenshot = State()
    waiting_question = State()
    waiting_reply = State()  # оператор пишет ответ пользователю


class VipPaymentStates(StatesGroup):
    waiting_screenshot = State()  # Путь А — скриншот оплаты
    waiting_question = State()  # Путь Б — текст вопроса модератору
    waiting_screenshot_moderator = State()  # Путь Б — скриншот после разговора


class VipModReplyStates(StatesGroup):
    awaiting_reply = State()  # модератор пишет ответ на VIP-вопрос пользователя
