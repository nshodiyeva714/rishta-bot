"""Bilingual text constants for RU and UZ."""

T = {
    # ── Step 0: Consent ──
    "consent_general": {
        "ru": (
            "📄 <b>RISHTA — Условия использования</b>\n\n"
            "Перед началом подтвердите:\n\n"
            "✅ Мне исполнилось 18 лет\n"
            "✅ Я ознакомлен(а) с Политикой конфиденциальности\n"
            "✅ Я согласен(а) на обработку персональных данных\n\n"
            "Продолжая вы принимаете условия платформы Rishta.\n\n"
            "⚠️ Платформа только для лиц старше 18 лет"
        ),
        "uz": (
            "📄 <b>RISHTA — Foydalanish shartlari</b>\n\n"
            "Davom etishdan oldin tasdiqlang:\n\n"
            "✅ Men 18 yoshdan oshganman\n"
            "✅ Maxfiylik siyosati bilan tanishdim\n"
            "✅ Shaxsiy ma'lumotlarni qayta ishlashga roziman\n\n"
            "Davom etish orqali siz Rishta platformasi shartlarini qabul qilasiz.\n\n"
            "⚠️ Platforma faqat 18 yoshdan oshganlar uchun"
        ),
    },
    "consent_special": {
        "ru": (
            "🔐 <b>Дополнительное согласие</b>\n\n"
            "Rishta собирает специальные категории данных:\n"
            "• Национальность\n"
            "• Религиозность\n"
            "• Семейное положение\n"
            "• Состояние здоровья\n"
            "• Фотографии\n\n"
            "По закону РУз ЗРУ-547 требуется ваше явное согласие."
        ),
        "uz": (
            "🔐 <b>Qo'shimcha rozilik</b>\n\n"
            "Rishta maxsus toifadagi ma'lumotlarni yig'adi:\n"
            "• Millat\n"
            "• Dindorlik\n"
            "• Oilaviy holat\n"
            "• Sog'lig'ining xususiyatlari\n"
            "• Fotosuratlar\n\n"
            "O'zR QRQ-547 qonuniga ko'ra sizning aniq roziligingiz talab qilinadi."
        ),
    },
    "consent_declined": {
        "ru": "❌ Вы не приняли условия. Для использования бота необходимо принять условия. Напишите /start чтобы начать заново.",
        "uz": "❌ Siz shartlarni qabul qilmadingiz. Botdan foydalanish uchun shartlarni qabul qilish kerak. Qayta boshlash uchun /start yozing.",
    },

    # ── Step 1: Language ──
    "welcome": {
        "ru": (
            "👋 Assalomu alaykum!\n"
            "Добро пожаловать в <b>Rishta!</b> 🤲\n\n"
            "Первая цифровая платформа для сватовства в Узбекистане.\n\n"
            "📢 @Rishta_uz\n\n"
            "Выберите язык / Tilni tanlang:"
        ),
        "uz": (
            "👋 Assalomu alaykum!\n"
            "<b>Rishta</b>ga xush kelibsiz! 🤲\n\n"
            "O'zbekistondagi birinchi raqamli sovchilik platformasi.\n\n"
            "📢 @Rishta_uz\n\n"
            "Tilni tanlang / Выберите язык:"
        ),
    },

    # ── Step 2: Main menu ──
    "main_menu": {
        "ru": "Что вас интересует?",
        "uz": "Sizni nima qiziqtiradi?",
    },
    "btn_search_bride": {"ru": "👦 Ищем невестку", "uz": "👦 Kelin qidiramiz"},
    "btn_post_daughter": {"ru": "👧 Разместить анкету дочери", "uz": "👧 Qiz anketasini joylashtirish"},
    "btn_search_candidate": {"ru": "🔍 Найти кандидата", "uz": "🔍 Nomzod qidirish"},
    "btn_my_applications": {"ru": "📋 Мои заявки", "uz": "📋 Mening arizalarim"},
    "btn_contact_moderator": {"ru": "💬 Связаться с модератором", "uz": "💬 Moderator bilan bog'lanish"},
    "btn_feedback": {"ru": "💡 Предложение/Обратная связь", "uz": "💡 Taklif yuborish"},
    "btn_about": {"ru": "ℹ️ О платформе", "uz": "ℹ️ Platforma haqida"},
    "user_feedback_prompt": {
        "ru": (
            "💡 <b>Предложения и обратная связь</b>\n\n"
            "Напишите ваше предложение по улучшению бота.\n"
            "Каждое предложение будет рассмотрено! 🙏"
        ),
        "uz": (
            "💡 <b>Taklif va mulohazalar</b>\n\n"
            "Botni yaxshilash bo'yicha takliflaringizni yozing.\n"
            "Har bir taklif ko'rib chiqiladi! 🙏"
        ),
    },
    "user_feedback_thanks": {
        "ru": "✅ Спасибо за предложение! Обязательно рассмотрим 🙏",
        "uz": "✅ Taklifingiz uchun rahmat! Ko'rib chiqamiz 🙏",
    },
    "choose_moderator": {
        "ru": (
            "💬 <b>Выберите модератора</b>\n\n"
            "Выберите одного из двух модераторов.\n"
            "Оба имеют одинаковые полномочия и помогут вам."
        ),
        "uz": (
            "💬 <b>Moderator tanlang</b>\n\n"
            "Ikki moderatordan birini tanlang.\n"
            "Ikkisi ham teng huquqli va yordam bera oladi."
        ),
    },

    # ── Step 3: About ──
    "about": {
        "ru": (
            "ℹ️ <b>О RISHTA</b>\n\n"
            "Rishta — первая цифровая платформа для сватовства в Узбекистане.\n\n"
            "Мы работаем как опытный сват — только охватываем всю страну 🇺🇿\n\n"
            "✅ Каждая анкета проверяется лично\n"
            "✅ Полная конфиденциальность\n"
            "✅ Контакт и адрес — только после оплаты\n"
            "✅ Модератор сопровождает весь процесс\n"
            "✅ Два языка — русский и узбекский\n"
            "✅ Фото защищены от скриншотов 🔒\n\n"
            "📄 <b>Пользовательское соглашение</b>\n"
            "Продолжая использование бота вы подтверждаете:\n"
            "• Вам исполнилось 18 лет\n"
            "• Вы согласны на обработку персональных данных\n"
            "• Вы принимаете условия платформы Rishta\n\n"
            "📄 <b>Политика конфиденциальности</b>\n"
            "Rishta собирает специальные категории данных:\n"
            "• Национальность, религиозность\n"
            "• Семейное положение, состояние здоровья\n"
            "• Фотографии\n"
            "Обработка данных осуществляется в соответствии с ЗРУ-547.\n\n"
            "⚠️ Платформа 18+\n\n"
            "📢 @Rishta_uz · 💬 @Rishta_chat"
        ),
        "uz": (
            "ℹ️ <b>RISHTA HAQIDA</b>\n\n"
            "Rishta — O'zbekistondagi birinchi raqamli sovchilik platformasi.\n\n"
            "Biz tajribali sovchi kabi ishlaymiz — faqat butun mamlakatni qamrab olamiz 🇺🇿\n\n"
            "✅ Har bir anketa shaxsan tekshiriladi\n"
            "✅ To'liq maxfiylik\n"
            "✅ Kontakt va manzil — faqat to'lovdan keyin\n"
            "✅ Moderator butun jarayonni kuzatib boradi\n"
            "✅ Ikki til — rus va o'zbek\n"
            "✅ Fotosuratlar skrinshotdan himoyalangan 🔒\n\n"
            "📄 <b>Foydalanish shartnomasi</b>\n"
            "Botdan foydalanishni davom ettirib siz tasdiqlaysiz:\n"
            "• Siz 18 yoshdan oshgansiz\n"
            "• Shaxsiy ma'lumotlarni qayta ishlashga rozisiz\n"
            "• Rishta platformasi shartlarini qabul qilasiz\n\n"
            "📄 <b>Maxfiylik siyosati</b>\n"
            "Rishta maxsus toifadagi ma'lumotlarni yig'adi:\n"
            "• Millat, dindorlik\n"
            "• Oilaviy holat, sog'liq holati\n"
            "• Fotosuratlar\n"
            "Ma'lumotlar QRQ-547 qonuniga muvofiq qayta ishlanadi.\n\n"
            "⚠️ Platforma 18+\n\n"
            "📢 @Rishta_uz · 💬 @Rishta_chat"
        ),
    },

    # ── Step 4: My applications ──
    "no_profiles": {
        "ru": "📋 У вас пока нет анкет. Создайте первую через главное меню!",
        "uz": "📋 Sizda hali anketalar yo'q. Asosiy menyu orqali birinchisini yarating!",
    },

    # ── Step 5: Questionnaire intro ──
    "quest_son_intro": {
        "ru": (
            "👦 <b>ИЩЕМ НЕВЕСТКУ</b>\n\n"
            "Заполните анкету вашего сына.\n"
            "Все данные строго конфиденциальны 🔒\n\n"
            "✅ Анкета видна всем пользователям\n"
            "✅ Контакт и адрес — только после оплаты\n"
            "📵 Фото защищены от скриншотов"
        ),
        "uz": (
            "👦 <b>KELIN QIDIRAMIZ</b>\n\n"
            "O'g'lingizning anketasini to'ldiring.\n"
            "Barcha ma'lumotlar qat'iy maxfiy 🔒\n\n"
            "✅ Anketa barcha foydalanuvchilarga ko'rinadi\n"
            "✅ Kontakt va manzil — faqat to'lovdan keyin\n"
            "📵 Fotosuratlar skrinshotdan himoyalangan"
        ),
    },
    "quest_daughter_intro": {
        "ru": (
            "👧 <b>РАЗМЕСТИТЬ АНКЕТУ ДОЧЕРИ</b>\n\n"
            "Анкета будет проверена модератором перед публикацией.\n\n"
            "✅ Анкета видна всем пользователям\n"
            "✅ Контакт и адрес — только после оплаты\n"
            "📵 Фото защищены от скриншотов 🔒"
        ),
        "uz": (
            "👧 <b>QIZ ANKETASINI JOYLASHTIRISH</b>\n\n"
            "Anketa nashr etilishdan oldin moderator tomonidan tekshiriladi.\n\n"
            "✅ Anketa barcha foydalanuvchilarga ko'rinadi\n"
            "✅ Kontakt va manzil — faqat to'lovdan keyin\n"
            "📵 Fotosuratlar skrinshotdan himoyalangan 🔒"
        ),
    },

    # ── Questions ──
    "q1": {
        "ru": "👤 <b>Вопрос 1</b>\n\nКак зовут вашего {child}?\n(можно вымышленное имя):",
        "uz": "👤 <b>1-savol</b>\n\n{child}ning ismi?\n(to'qilgan ism ham bo'lishi mumkin):",
    },
    "q2": {
        "ru": "🗓 <b>Вопрос 2</b>\n\nГод рождения (например: 1998):",
        "uz": "🗓 <b>2-savol</b>\n\nTug'ilgan yili (masalan: 1998):",
    },
    "q2_confirm": {
        "ru": "✅ Возраст: {age} — верно?",
        "uz": "✅ Yoshi: {age} — to'g'rimi?",
    },
    "q3": {
        "ru": "📏 <b>Вопрос 3</b>\n\nРост (в см, например: 175):",
        "uz": "📏 <b>3-savol</b>\n\nBo'yi (sm da, masalan: 175):",
    },
    "q4": {
        "ru": "⚖️ <b>Вопрос 4</b>\n\nВес (в кг, например: 70):",
        "uz": "⚖️ <b>4-savol</b>\n\nVazni (kg da, masalan: 70):",
    },
    "q5": {
        "ru": "🎓 <b>Вопрос 5</b>\n\nОбразование:",
        "uz": "🎓 <b>5-savol</b>\n\nMa'lumoti:",
    },
    "q5_university": {
        "ru": "🏫 Укажите название вуза и курс:",
        "uz": "🏫 OTM nomi va kursini kiriting:",
    },
    "q6_choice": {
        "ru": "💼 <b>Вопрос 6</b>\n\nРабота / занятость:",
        "uz": "💼 <b>6-savol</b>\n\nIsh / bandlik:",
    },
    "q6": {
        "ru": "💼 Укажите место работы / род деятельности:",
        "uz": "💼 Ish joyini / faoliyat turini ko'rsating:",
    },
    "q7": {
        "ru": "🏠 <b>Вопрос 7</b>\n\nЖилищные условия:",
        "uz": "🏠 <b>7-savol</b>\n\nYashash sharoiti:",
    },
    "q7_parent_housing": {
        "ru": "🏠 Уточните тип жилья родителей:",
        "uz": "🏠 Ota-onaning uy turini aniqlashtiring:",
    },
    "q8": {
        "ru": "🚗 <b>Вопрос 8</b>\n\nНаличие автомобиля:",
        "uz": "🚗 <b>8-savol</b>\n\nAvtomobil mavjudligi:",
    },
    "q9_city_district": {
        "ru": "🏙 <b>Вопрос 9</b>\n\nВаш город и район:\n(например: Ташкент, Юнусабад)",
        "uz": "🏙 <b>9-savol</b>\n\nShahringiz va tumaningiz:\n(masalan: Toshkent, Yunusobod)",
    },
    "q9_address": {
        "ru": "🏠 <b>Вопрос 10</b>\n\nАдрес (улица/махалля):\n\n⚠️ Адрес передаётся только после оплаты 🔒",
        "uz": "🏠 <b>10-savol</b>\n\nManzil (ko'cha/mahalla):\n\n⚠️ Manzil faqat to'lovdan keyin beriladi 🔒",
    },
    "q10b": {
        "ru": "✈️ <b>Вопрос 11</b>\n\nГде ищете кандидата?",
        "uz": "✈️ <b>11-savol</b>\n\nNomzodni qayerdan qidiryapsiz?",
    },
    "q10b_city": {
        "ru": "🏙 Предпочтительный город:",
        "uz": "🏙 Afzal ko'rilgan shahar:",
    },
    "q10b_district": {
        "ru": "📍 Район (необязательно):",
        "uz": "📍 Tuman (ixtiyoriy):",
    },
    "q10b_country": {
        "ru": "🌍 Где ищете?",
        "uz": "🌍 Qayerdan qidiryapsiz?",
    },
    "req_residence_region": {
        "ru": "Регион кандидата:",
        "uz": "Nomzod hududi:",
    },
    "q11": {
        "ru": "🗺 <b>Вопрос 12</b>\n\nРегион происхождения семьи:",
        "uz": "🗺 <b>12-savol</b>\n\nOila kelib chiqqan hudud:",
    },
    "q12": {
        "ru": "👥 <b>Вопрос 13</b>\n\nНациональность семьи:",
        "uz": "👥 <b>13-savol</b>\n\nOila millati:",
    },
    "q13": {
        "ru": "👨 <b>Вопрос 14</b>\n\nОтец — чем занимается:",
        "uz": "👨 <b>14-savol</b>\n\nOtasi — nima bilan shug'ullanadi:",
    },
    "q14": {
        "ru": "👩 <b>Вопрос 15</b>\n\nМать — чем занимается:",
        "uz": "👩 <b>15-savol</b>\n\nOnasi — nima bilan shug'ullanadi:",
    },
    "q15_brothers": {
        "ru": "👨‍👩‍👧‍👦 <b>Вопрос 16</b>\n\nКоличество братьев (0 если нет):",
        "uz": "👨‍👩‍👧‍👦 <b>16-savol</b>\n\nAkalar/ukalar soni (0 bo'lsa yo'q):",
    },
    "q15_sisters": {
        "ru": "Количество сестёр (0 если нет):",
        "uz": "Opalar/singillar soni (0 bo'lsa yo'q):",
    },
    "q15_position": {
        "ru": "Место в семье:",
        "uz": "Oiladagi o'rni:",
    },
    "q16": {
        "ru": "🕌 <b>Вопрос 17</b>\n\nРелигиозность:",
        "uz": "🕌 <b>17-savol</b>\n\nDindorlik:",
    },
    "q17": {
        "ru": "💍 <b>Вопрос 18</b>\n\nСемейное положение:",
        "uz": "💍 <b>18-savol</b>\n\nOilaviy holat:",
    },
    "q18": {
        "ru": "👶 <b>Вопрос 19</b>\n\nЕсть ли дети:",
        "uz": "👶 <b>19-savol</b>\n\nFarzandlari bormi:",
    },
    "q19": {
        "ru": "❤️ <b>Вопрос 20</b>\n\nОсобенности здоровья (деликатно, если важно):",
        "uz": "❤️ <b>20-savol</b>\n\nSog'lig'ining xususiyatlari (biron bir nuqsoni agar bo'lsa):",
    },
    "q20": {
        "ru": "✨ <b>Вопрос 21</b>\n\nХарактер и увлечения (пара слов):",
        "uz": "✨ <b>21-savol</b>\n\nXarakter va qiziqishlar (bir necha so'z):",
    },
    "q20a_intro": {
        "ru": (
            "💬 <b>Вопрос 21А — Совместимость</b>\n\n"
            "Три необязательных вопроса помогут модератору точнее подобрать пару.\n\n"
            "1️⃣ Как вы представляете идеальную семейную жизнь?"
        ),
        "uz": (
            "💬 <b>21A-savol — Moslik</b>\n\n"
            "Uchta ixtiyoriy savol moderatorga juftlikni aniqroq tanlashga yordam beradi.\n\n"
            "1️⃣ Ideal oilaviy hayotni qanday tasavvur qilasiz?"
        ),
    },
    "q20a_qualities": {
        "ru": "2️⃣ Какие качества в партнёре для вас самые важные?",
        "uz": "2️⃣ Nomzodning qanday fazilatlari siz uchun eng muhim?",
    },
    "q20a_plans": {
        "ru": "3️⃣ Ваши планы на ближайшие 5 лет?",
        "uz": "3️⃣ Yaqin 5 yilga rejalaringiz?",
    },
    "q21": {
        "ru": (
            "📸 <b>Вопрос 22 — Фото</b>\n\n"
            "Как хотите разместить фото?\n\n"
            "🔒 Фото защищено от скриншотов\n"
            "🔒 Видно только после оплаты"
        ),
        "uz": (
            "📸 <b>22-savol — Fotosurat</b>\n\n"
            "Fotosuratni qanday joylashtirmoqchisiz?\n\n"
            "🔒 Fotosurat skrinshotdan himoyalangan\n"
            "🔒 Faqat to'lovdan keyin ko'rinadi"
        ),
    },
    "q21_upload": {
        "ru": "Загрузите фото:",
        "uz": "Fotosuratni yuklang:",
    },
    "q21_closed_face_hint": {
        "ru": (
            "💡 Вы можете:\n"
            "• Закрыть лицо смайликом 😊\n"
            "• Прислать фото со спины\n"
            "• Фото в хиджабе\n\n"
            "Загрузите подготовленное фото:"
        ),
        "uz": (
            "💡 Siz:\n"
            "• Yuzni smaylik bilan yopishingiz mumkin 😊\n"
            "• Orqadan fotosurat yuborishingiz mumkin\n"
            "• Hijobdagi fotosurat\n\n"
            "Tayyorlangan fotosuratni yuklang:"
        ),
    },
    "q22_phone": {
        "ru": "📞 <b>Вопрос 23</b>\n\nНомер телефона родителей:\n(можно без +998, например: 901234567)",
        "uz": "📞 <b>23-savol</b>\n\nOta-onalar telefon raqami:\n(+998 siz ham bo'ladi, masalan: 901234567)",
    },
    "q22_parent_tg": {
        "ru": "📱 Telegram родителей:\n→ @__________",
        "uz": "📱 Ota-onaning Telegrami:\n→ @__________",
    },
    "q22_candidate_tg": {
        "ru": "💬 Telegram {child}:\n→ @__________ (или Пропустить)",
        "uz": "💬 {child}ning Telegrami:\n→ @__________ (yoki O'tkazib yuborish)",
    },
    "q22_location": {
        "ru": "📍 <b>Вопрос 24</b>\n\nМестоположение (необязательно):",
        "uz": "📍 <b>24-savol</b>\n\nJoylashuv (ixtiyoriy):",
    },
    "q23": {
        "ru": "🔍 <b>Вопрос 25</b>\n\nСтатус вашей анкеты:",
        "uz": "🔍 <b>25-savol</b>\n\nAnketangiz holati:",
    },

    # ── Step 6: Tariff ──
    "tariff": {
        "ru": (
            "⭐ <b>Тип размещения</b>\n\nВыберите тариф:\n\n"
            "⭐ VIP анкета — 100,000 сум/мес\n"
            "   • Показывается первой в поиске\n"
            "   • Выделена значком ⭐\n"
            "   • Больше просмотров и обращений\n\n"
            "📋 Обычная анкета — бесплатно\n"
            "   • Стандартное размещение"
        ),
        "uz": (
            "⭐ <b>Joylashtirish turi</b>\n\nTarifni tanlang:\n\n"
            "⭐ VIP anketa — 100,000 so'm/oy\n"
            "   • Qidiruvda birinchi ko'rsatiladi\n"
            "   • ⭐ belgisi bilan ajratilgan\n"
            "   • Ko'proq ko'rishlar va murojaatlar\n\n"
            "📋 Oddiy anketa — bepul\n"
            "   • Standart joylashtirish"
        ),
    },

    # ── Step 7: Requirements ──
    "req_intro": {
        "ru": "📋 Теперь укажите требования к кандидату.",
        "uz": "📋 Endi nomzodga talablarni ko'rsating.",
    },
    "req_age": {
        "ru": "Возраст кандидата:",
        "uz": "Nomzod yoshi:",
    },
    "req_education": {
        "ru": "Образование:",
        "uz": "Ma'lumoti:",
    },
    "req_residence": {
        "ru": "Где проживает кандидат:",
        "uz": "Nomzod qayerda yashaydi:",
    },
    "req_nationality": {
        "ru": "Национальность:",
        "uz": "Millat:",
    },
    "req_religiosity": {
        "ru": "Религиозность:",
        "uz": "Dindorlik:",
    },
    "req_marital": {
        "ru": "Семейное положение:",
        "uz": "Oilaviy holat:",
    },
    "req_children": {
        "ru": "Наличие детей:",
        "uz": "Farzandlari bormi:",
    },
    "req_car": {
        "ru": "Автомобиль:",
        "uz": "Avtomobil:",
    },
    "req_housing": {
        "ru": "Жилищные условия:",
        "uz": "Yashash sharoiti:",
    },
    "req_job": {
        "ru": "Работа/доход:",
        "uz": "Ish/daromad:",
    },
    "req_other": {
        "ru": "Другие пожелания:",
        "uz": "Boshqa istaklar:",
    },

    # ── Step 8: Confirmation ──
    "profile_submitted": {
        "ru": (
            "✅ <b>Анкета принята на проверку!</b>\n\n"
            "🔖 Ваш номер: {display_id}\n\n"
            "Модератор проверит данные в течение 24 часов.\n\n"
            "После публикации вы получите уведомление 🤝\n\n"
            "📢 @Rishta_uz — истории успеха\n"
            "💬 @Rishta_chat — сообщество"
        ),
        "uz": (
            "✅ <b>Anketa tekshiruvga qabul qilindi!</b>\n\n"
            "🔖 Sizning raqamingiz: {display_id}\n\n"
            "Moderator ma'lumotlarni 24 soat ichida tekshiradi.\n\n"
            "Nashr etilgandan so'ng sizga xabar beriladi 🤝\n\n"
            "📢 @Rishta_uz — muvaffaqiyat tarixi\n"
            "💬 @Rishta_chat — jamoa"
        ),
    },

    # ── Step 9: Moderator ──
    "mod_new_profile": {
        "ru": (
            "🆕 <b>НОВАЯ АНКЕТА НА ПРОВЕРКУ</b>\n\n"
            "🔖 {display_id}\n"
            "{icon} {name} · {age}\n"
            "📍 {city}, {district}\n"
            "📞 {phone}\n"
            "VIP: {vip}\n"
            "📸 Фото: {photo}"
        ),
        "uz": (
            "🆕 <b>YANGI ANKETA TEKSHIRUVGA</b>\n\n"
            "🔖 {display_id}\n"
            "{icon} {name} · {age}\n"
            "📍 {city}, {district}\n"
            "📞 {phone}\n"
            "VIP: {vip}\n"
            "📸 Fotosurat: {photo}"
        ),
    },
    "mod_profile_published": {
        "ru": "🎉 Ваша анкета {display_id} опубликована! Теперь она видна другим пользователям.",
        "uz": "🎉 Anketa {display_id} nashr etildi! Endi u boshqa foydalanuvchilarga ko'rinadi.",
    },
    "mod_profile_rejected": {
        "ru": "❌ Анкета {display_id} отклонена модератором. Свяжитесь с модератором для уточнения.",
        "uz": "❌ Anketa {display_id} moderator tomonidan rad etildi. Aniqlashtirish uchun moderator bilan bog'laning.",
    },

    # ── Step 10: Search ──
    "search_title": {
        "ru": "🔍 <b>Найти кандидата</b>\n\nВыберите режим поиска:",
        "uz": "🔍 <b>Nomzod qidirish</b>\n\nQidirish usulini tanlang:",
    },
    "search_no_anketa": {
        "ru": "🔍 <b>Найти кандидата</b>\n\n⚠️ Для поиска сначала разместите свою анкету.",
        "uz": "🔍 <b>Nomzod qidirish</b>\n\n⚠️ Qidirish uchun avval o'z anketangizni joylashtiring.",
    },
    "search_found": {
        "ru": "🔍 <b>Найдено анкет: {total}</b>\nПоказаны: {from_}–{to}",
        "uz": "🔍 <b>Jami: {total} ta anketa topildi</b>\nKo'rsatilmoqda: {from_}–{to}",
    },
    "search_empty": {
        "ru": "🔍 Анкеты не найдены.\n\nПопробуйте изменить фильтры.",
        "uz": "🔍 Anketalar topilmadi.\n\nFiltrlarni o'zgartiring.",
    },
    "search_filters_title": {
        "ru": "🔧 <b>Фильтры поиска</b>\n\n{summary}\n\nЧто настроить?",
        "uz": "🔧 <b>Filtrlar</b>\n\n{summary}\n\nNimani o'zgartirmoqchisiz?",
    },
    "search_filters_empty": {
        "ru": "Фильтры не выбраны — будут показаны все анкеты.",
        "uz": "Filtrlar tanlanmagan — barcha anketalar ko'rsatiladi.",
    },
    "search_filters_cleared": {
        "ru": "✅ Фильтры сброшены!",
        "uz": "✅ Filtrlar tozalandi!",
    },
    "search_filter_age_prompt": {
        "ru": "📅 Введите диапазон возраста (например: 20-30):",
        "uz": "📅 Yosh oralig'ini kiriting (masalan: 20-30):",
    },
    "search_filter_age_error": {
        "ru": "⚠️ Неверный формат. Введите как: 20-30",
        "uz": "⚠️ Noto'g'ri format. Masalan: 20-30",
    },

    # ── Step 11: Notification to girl's family ──
    "notify_interest": {
        "ru": (
            "🔔 <b>Новый интерес к вашей анкете!</b>\n"
            "🔖 {display_id}\n\n"
            "Семья из {city} заинтересовалась анкетой вашей дочери.\n\n"
            "О женихе:\n"
            "• Возраст: {age}\n"
            "• Образование: {education}\n"
            "• Работа: {occupation}\n"
            "• Город: {requester_city}\n"
            "• Статус: {residence}\n\n"
            "Ваш модератор свяжется с вами в ближайшее время. 🤝"
        ),
        "uz": (
            "🔔 <b>Anketangizga yangi qiziqish!</b>\n"
            "🔖 {display_id}\n\n"
            "{city}dan oila qizingizning anketasiga qiziqish bildirdi.\n\n"
            "Kuyov haqida:\n"
            "• Yoshi: {age}\n"
            "• Ma'lumoti: {education}\n"
            "• Ish: {occupation}\n"
            "• Shahar: {requester_city}\n"
            "• Holat: {residence}\n\n"
            "Moderatoringiz tez orada siz bilan bog'lanadi. 🤝"
        ),
    },

    # ── Step 12: Contact moderator ──
    "contact_moderator": {
        "ru": (
            "💬 <b>Связаться с модератором</b>\n\n"
            "Ваш регион: {region}\n\n"
            "👤 Ваш модератор:\n{moderator}\n\n"
            "🕐 Время работы: {hours}\n\n"
            "Напишите модератору и укажите номер анкеты."
        ),
        "uz": (
            "💬 <b>Moderator bilan bog'lanish</b>\n\n"
            "Hududingiz: {region}\n\n"
            "👤 Moderatoringiz:\n{moderator}\n\n"
            "🕐 Ish vaqti: {hours}\n\n"
            "Moderatorga yozing va anketa raqamini ko'rsating."
        ),
    },

    # ── Step 13: Payment ──
    "payment_prompt": {
        "ru": "💳 Хотите получить контакт и адрес семьи?\n🔖 Анкета: {display_id}",
        "uz": "💳 Oila kontakti va manzilini olmoqchimisiz?\n🔖 Anketa: {display_id}",
    },
    "payment_uz": {
        "ru": (
            "💳 <b>Получить контакт и адрес</b>\n\n"
            "Анкета: {display_id}\n\n"
            "💰 Стоимость: 30,000 сум"
        ),
        "uz": (
            "💳 <b>Kontakt va manzil olish</b>\n\n"
            "Anketa: {display_id}\n\n"
            "💰 Narxi: 30,000 so'm"
        ),
    },
    "payment_cis": {
        "ru": "💳 <b>Получить контакт и адрес</b>\n\nАнкета: {display_id}\n\n💰 Стоимость: 30,000 сум",
        "uz": "💳 <b>Kontakt va manzil olish</b>\n\nAnketa: {display_id}\n\n💰 Narxi: 30,000 so'm",
    },
    "payment_intl": {
        "ru": "💳 <b>Получить контакт и адрес</b>\n\nАнкета: {display_id}\n\n💰 Стоимость: $15",
        "uz": "💳 <b>Kontakt va manzil olish</b>\n\nAnketa: {display_id}\n\n💰 Narxi: $15",
    },
    "payment_card_transfer": {
        "ru": (
            "🏦 Переведите на карту:\n"
            "<code>5614 6887 0899 8959</code>\n"
            "Получатель: SHODIYEVA NASIBA\n\n"
            "После перевода пришлите скриншот сюда 👇\n\n"
            "⚠️ <i>Оплата невозвратна после передачи контакта</i>"
        ),
        "uz": (
            "🏦 Kartaga o'tkazing:\n"
            "<code>5614 6887 0899 8959</code>\n"
            "Oluvchi: SHODIYEVA NASIBA\n\n"
            "O'tkazgandan so'ng skrinshot yuboring 👇\n\n"
            "⚠️ <i>Kontakt berilgandan keyin to'lov qaytarilmaydi</i>"
        ),
    },

    # ── Step 14: Moderator payment notification ──
    "mod_payment_manual": {
        "ru": (
            "📩 <b>НОВАЯ ОПЛАТА — ПРОВЕРИТЬ!</b>\n\n"
            "От: @{username} (ID: {user_id})\n"
            "🔖 Анкета: {display_id}\n"
            "💰 Сумма: {amount}\n"
            "📸 Скриншот: см. ниже"
        ),
        "uz": (
            "📩 <b>YANGI TO'LOV — TEKSHIRISH!</b>\n\n"
            "Kimdan: @{username} (ID: {user_id})\n"
            "🔖 Anketa: {display_id}\n"
            "💰 Summa: {amount}\n"
            "📸 Skrinshot: pastda"
        ),
    },

    # ── Step 15: Contact reveal ──
    "contact_revealed": {
        "ru": (
            "✅ <b>Оплата подтверждена!</b>\n"
            "🔖 Анкета: {display_id}\n\n"
            "Контакты и адрес семьи:\n\n"
            "📞 {phone}\n"
            "📱 Telegram родителей: {parent_tg}\n"
            "💬 Telegram {child}: {candidate_tg}\n"
            "📍 {city}, {district}\n"
            "🏠 Адрес: {address}\n\n"
            "⚠️ Просим сохранять уважение к семье и конфиденциальность.\n\n"
            "Модератор предупредил семью о вашем визите 🤝\n\n"
            "Удачи! Пусть всё сложится наилучшим образом 🤲\n\n"
            "Через 14 дней спросим о результате 😊"
        ),
        "uz": (
            "✅ <b>To'lov tasdiqlandi!</b>\n"
            "🔖 Anketa: {display_id}\n\n"
            "Oila kontaktlari va manzili:\n\n"
            "📞 {phone}\n"
            "📱 Ota-onaning Telegrami: {parent_tg}\n"
            "💬 {child}ning Telegrami: {candidate_tg}\n"
            "📍 {city}, {district}\n"
            "🏠 Manzil: {address}\n\n"
            "⚠️ Oilaga hurmat va maxfiylikni saqlashingizni so'raymiz.\n\n"
            "Moderator oilani tashrifingiz haqida ogohlantirdi 🤝\n\n"
            "Omad! Hammasi yaxshi bo'lsin 🤲\n\n"
            "14 kundan so'ng natija haqida so'raymiz 😊"
        ),
    },

    # ── Step 16: Meeting ──
    "meeting_date": {
        "ru": "📅 Хотите запланировать встречу?\n\nУкажите удобную дату (например: 20.04.2026):",
        "uz": "📅 Uchrashuv rejalashtirishni xohlaysizmi?\n\nQulay sanani ko'rsating (masalan: 20.04.2026):",
    },
    "meeting_time": {
        "ru": "⏰ Удобное время (например: 15:00):",
        "uz": "⏰ Qulay vaqt (masalan: 15:00):",
    },
    "meeting_confirmed": {
        "ru": "✅ Отлично!\n\nМодератор передаст семье о встрече {date} в {time} 🤝",
        "uz": "✅ Ajoyib!\n\nModerator oilaga {date} kuni {time} da uchrashuv haqida xabar beradi 🤝",
    },
    "meeting_skip": {
        "ru": "Хорошо! Свяжитесь с семьёй самостоятельно. Удачи! 🤝",
        "uz": "Yaxshi! Oila bilan o'zingiz bog'laning. Omad! 🤝",
    },

    # ── Step 17: Feedback ──
    "feedback_ask": {
        "ru": "🔔 <b>Как прошла встреча?</b>\n🔖 Анкета: {display_id}",
        "uz": "🔔 <b>Uchrashuv qanday o'tdi?</b>\n🔖 Anketa: {display_id}",
    },
    "feedback_nikoh": {
        "ru": (
            "🎉 <b>Поздравляем от всей души!</b>\n\n"
            "Nikohingiz muborak bo'lsin! 💍🤲\n\n"
            "Хотите поделиться историей анонимно? "
            "Это поможет другим семьям найти счастье!"
        ),
        "uz": (
            "🎉 <b>Chin dildan tabriklaymiz!</b>\n\n"
            "Nikohingiz muborak bo'lsin! 💍🤲\n\n"
            "Tarixingizni anonim ravishda baham ko'rmoqchimisiz? "
            "Bu boshqa oilalarga baxt topishga yordam beradi!"
        ),
    },

    # ── Step 18: Reminder ──
    "reminder_30d": {
        "ru": (
            "🔔 <b>Rishta напоминает!</b>\n"
            "🔖 Ваша анкета: {display_id}\n\n"
            "Анкета размещена 30 дней назад.\n"
            "Всё ли актуально?"
        ),
        "uz": (
            "🔔 <b>Rishta eslatadi!</b>\n"
            "🔖 Anketangiz: {display_id}\n\n"
            "Anketa 30 kun oldin joylashtirilgan.\n"
            "Hammasi dolzarbmi?"
        ),
    },

    # ── Step 19: Complaints ──
    "complaint_reason": {
        "ru": "🚩 <b>ПОЖАЛОВАТЬСЯ НА АНКЕТУ</b>\n🔖 {display_id}\n\nУкажите причину:",
        "uz": "🚩 <b>ANKETAGA SHIKOYAT QILISH</b>\n🔖 {display_id}\n\nSababni ko'rsating:",
    },
    "complaint_submitted": {
        "ru": "✅ Жалоба принята.\n\nМодератор рассмотрит в течение 24 часов.\n\nСпасибо за помощь! 🤝",
        "uz": "✅ Shikoyat qabul qilindi.\n\nModerator 24 soat ichida ko'rib chiqadi.\n\nYordamingiz uchun rahmat! 🤝",
    },

    # ── Step 20: Daily report ──
    "daily_report": {
        "ru": (
            "📊 <b>ОТЧЁТ ЗА {date}</b>\n\n"
            "💰 Оплат сегодня: {payments_count}\n"
            "💵 Сумма: {payments_total}\n\n"
            "📈 Новых анкет сегодня: {new_profiles}\n"
            "👁 Всего просмотров: {total_views}\n"
            "🚩 Жалоб: {complaints}\n"
            "❤️ В избранное: {favorites}"
        ),
        "uz": (
            "📊 <b>{date} UCHUN HISOBOT</b>\n\n"
            "💰 Bugungi to'lovlar: {payments_count}\n"
            "💵 Jami: {payments_total}\n\n"
            "📈 Bugungi yangi anketalar: {new_profiles}\n"
            "👁 Jami ko'rishlar: {total_views}\n"
            "🚩 Shikoyatlar: {complaints}\n"
            "❤️ Sevimlilar: {favorites}"
        ),
    },

    # ── Common buttons ──
    "btn_back": {"ru": "🔙 Назад", "uz": "🔙 Ortga"},
    "btn_skip": {"ru": "⏭ Пропустить", "uz": "⏭ O'tkazib yuborish"},
    "btn_yes": {"ru": "✅ Да, верно", "uz": "✅ Ha, to'g'ri"},
    "btn_fix": {"ru": "✏️ Исправить", "uz": "✏️ Tuzatish"},
    "btn_start": {"ru": "✅ Начать", "uz": "✅ Boshlash"},
    "btn_cancel": {"ru": "❌ Назад", "uz": "❌ Ortga"},
    "btn_agree": {"ru": "✅ Согласен и продолжить", "uz": "✅ Roziman va davom etish"},
    "btn_disagree": {"ru": "❌ Не согласен", "uz": "❌ Rozi emasman"},
    "btn_consent_special_yes": {"ru": "✅ Даю согласие", "uz": "✅ Rozilik beraman"},
    "btn_confirm": {"ru": "✅ Подтвердить анкету", "uz": "✅ Anketani tasdiqlash"},
    "btn_send_location": {"ru": "📍 Отправить геолокацию", "uz": "📍 Geolokatsiya yuborish"},
    "btn_send_map_link": {"ru": "🗺 Указать ссылку на карту", "uz": "🗺 Xaritaga havola ko'rsatish"},

    # ── Validation ──
    "invalid_number": {
        "ru": "❌ Введите число.",
        "uz": "❌ Raqam kiriting.",
    },
    "invalid_year": {
        "ru": "❌ Введите корректный год рождения (например: 1998).",
        "uz": "❌ To'g'ri tug'ilgan yilni kiriting (masalan: 1998).",
    },
    "invalid_phone": {
        "ru": "❌ Введите номер в формате +998XXXXXXXXX",
        "uz": "❌ Raqamni +998XXXXXXXXX formatda kiriting",
    },

    # child labels (genitive)
    "son": {"ru": "сына", "uz": "O'g'lingiz"},
    "daughter": {"ru": "дочери", "uz": "Qizingiz"},
    # child labels (nominative)
    "son_nom": {"ru": "сын", "uz": "o'g'il"},
    "daughter_nom": {"ru": "дочь", "uz": "qiz"},
    # gender-specific verbs/adjectives
    "works_m": {"ru": "работает", "uz": "ishlaydi"},
    "works_f": {"ru": "работает", "uz": "ishlaydi"},
    "q6_choice_son": {
        "ru": "💼 <b>Вопрос 6</b>\n\nГде работает / чем занимается ваш сын:",
        "uz": "💼 <b>6-savol</b>\n\nO'g'lingiz qayerda ishlaydi / nima bilan shug'ullanadi:",
    },
    "q6_choice_daughter": {
        "ru": "💼 <b>Вопрос 6</b>\n\nГде работает / чем занимается ваша дочь:",
        "uz": "💼 <b>6-savol</b>\n\nQizingiz qayerda ishlaydi / nima bilan shug'ullanadi:",
    },
}


def t(key: str, lang: str = "ru", **kwargs) -> str:
    entry = T.get(key, {})
    text = entry.get(lang, entry.get("ru", f"[{key}]"))
    if kwargs:
        text = text.format(**kwargs)
    return text
