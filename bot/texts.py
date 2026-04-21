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
        "ru": "Tilni tanlang / Выберите язык:",
        "uz": "Tilni tanlang / Выберите язык:",
    },

    # ── Step 2: Main menu ──
    "main_menu": {
        "ru": "Что хотите сделать?",
        "uz": "Nima qilmoqchisiz?",
    },
    "btn_search_bride": {"ru": "👩 Невесту сыну", "uz": "👩 O'g'ilga kelin"},
    "btn_search_groom": {"ru": "👨 Жениха дочке", "uz": "👨 Qizga kuyov"},
    "btn_search_candidate": {"ru": "💫 Найти кандидата", "uz": "💫 Nomzod qidirish"},
    "btn_create_profile": {"ru": "🤲 Создать анкету", "uz": "🤲 Anketa yaratish"},
    "btn_profile_son": {"ru": "👨 Мужская анкета", "uz": "👨 Yigitning anketasi"},
    "btn_profile_daughter": {"ru": "👩 Женская анкета", "uz": "👩 Qizning anketasi"},
    "btn_my_applications": {"ru": "👤 Моя страница", "uz": "👤 Mening sahifam"},
    "btn_contact_moderator": {"ru": "💁‍♀️ Модератор", "uz": "💁‍♀️ Moderator"},
    "btn_about": {"ru": "ℹ️ О платформе", "uz": "ℹ️ Platforma haqida"},
    "submenu_search": {
        "ru": "Кого ищете?",
        "uz": "Kimni qidiryapsiz?",
    },
    "submenu_create": {
        "ru": "Чью анкету хотите создать?",
        "uz": "Kimning anketasini yaratmoqchisiz?",
    },
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
            "Выберите модератора по вашему региону.\n"
            "Все имеют одинаковые полномочия и помогут вам."
        ),
        "uz": (
            "💬 <b>Moderator tanlang</b>\n\n"
            "O'z hududingiz bo'yicha moderatorni tanlang.\n"
            "Hammasi teng huquqli va yordam bera oladi."
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
            "✅ Контакт — по взаимному согласию\n"
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
            "📢 @Rishta_channel"
        ),
        "uz": (
            "ℹ️ <b>RISHTA HAQIDA</b>\n\n"
            "Rishta — O'zbekistondagi birinchi raqamli sovchilik platformasi.\n\n"
            "Biz tajribali sovchi kabi ishlaymiz — faqat butun mamlakatni qamrab olamiz 🇺🇿\n\n"
            "✅ Har bir anketa shaxsan tekshiriladi\n"
            "✅ To'liq maxfiylik\n"
            "✅ Kontakt — o'zaro rozilik asosida\n"
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
            "📢 @Rishta_channel"
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
            "📝 <b>РАЗМЕЩЕНИЕ АНКЕТЫ</b>\n\n"
            "Анкета будет проверена модератором перед публикацией.\n\n"
            "✅ Анкета видна всем пользователям\n"
            "✅ Контакт и адрес — по взаимному согласию\n"
            "📵 Фото защищены от скриншотов 🔒"
        ),
        "uz": (
            "📝 <b>ANKETA JOYLASHTIRISH</b>\n\n"
            "Anketa nashr etilishdan oldin moderator tomonidan tekshiriladi.\n\n"
            "✅ Anketa barcha foydalanuvchilarga ko'rinadi\n"
            "✅ Kontakt va manzil — rozilik asosida beriladi\n"
            "📵 Fotosuratlar skrinshotdan himoyalangan 🔒"
        ),
    },
    "quest_daughter_intro": {
        "ru": (
            "📝 <b>РАЗМЕЩЕНИЕ АНКЕТЫ</b>\n\n"
            "Анкета будет проверена модератором перед публикацией.\n\n"
            "✅ Анкета видна всем пользователям\n"
            "✅ Контакт и адрес — по взаимному согласию\n"
            "📵 Фото защищены от скриншотов 🔒"
        ),
        "uz": (
            "📝 <b>ANKETA JOYLASHTIRISH</b>\n\n"
            "Anketa nashr etilishdan oldin moderator tomonidan tekshiriladi.\n\n"
            "✅ Anketa barcha foydalanuvchilarga ko'rinadi\n"
            "✅ Kontakt va manzil — rozilik asosida beriladi\n"
            "📵 Fotosuratlar skrinshotdan himoyalangan 🔒"
        ),
    },

    # ── Questions (Stage 1 — 10 questions with progress bar) ──
    "q1": {
        "ru": "🪪 Вопрос 1/14\n{bar}\n\nИмя (можно вымышленное):",
        "uz": "🪪 1/14-savol\n{bar}\n\nIsm (taxallus bo'lishi mumkin):",
    },
    "q2": {
        "ru": "🎂📏 Вопрос 2/14\n{bar}\n\nГод рождения (например: 1998):",
        "uz": "🎂📏 2/14-savol\n{bar}\n\nTug'ilgan yil (masalan: 1998):",
    },
    "q2_confirm": {
        "ru": "Вопрос 2/14\n{bar}\n\nВозраст: {age} — верно?",
        "uz": "2/14-savol\n{bar}\n\nYoshi: {age} — to'g'rimi?",
    },
    "q2_height": {
        "ru": "🎂📏 Вопрос 2/14\n{bar}\n\nРост в см (например: 175):",
        "uz": "🎂📏 2/14-savol\n{bar}\n\nBo'yingiz (sm, masalan: 175):",
    },
    "q3_photo": {
        "ru": (
            "🖼 Вопрос 3/14\n{bar}\n\n"
            "Фото\n\n"
            "💡 Анкеты с фото получают\n"
            "в 3 раза больше просмотров!\n\n"
            "Как хотите разместить фото?"
        ),
        "uz": (
            "🖼 3/14-savol\n{bar}\n\n"
            "Fotosurat\n\n"
            "💡 Fotoli anketalar 3 marta\n"
            "ko'proq e'tibor tortadi!\n\n"
            "Qanday joylashtirasiz?"
        ),
    },
    "q4_body_type": {
        "ru": "⚡ Вопрос 4/14\n{bar}\n\nТелосложение:",
        "uz": "⚡ 4/14-savol\n{bar}\n\nTana tuzilishi:",
    },
    "q5_nationality": {
        "ru": "🌍 Вопрос 5/14\n{bar}\n\nНациональность:",
        "uz": "🌍 5/14-savol\n{bar}\n\nMillati:",
    },
    "q6_city": {
        "ru": "🏡 Вопрос 6/14\n{bar}\n\nГде вы проживаете?\n(для Узбекистана далее выберете регион)",
        "uz": "🏡 6/14-savol\n{bar}\n\nQayerda yashaysiz?\n(O'zbekiston uchun keyin viloyatni tanlaysiz)",
    },
    "q7_education": {
        "ru": "Вопрос 7/14\n{bar}\n\nОбразование:",
        "uz": "7/14-savol\n{bar}\n\nMa'lumoti:",
    },
    "q8_occupation": {
        "ru": "💼 Вопрос 8/14\n{bar}\n\nЗанятость:",
        "uz": "💼 8/14-savol\n{bar}\n\nBandligi:",
    },
    "q8_occupation_detail": {
        "ru": "Вопрос 8/14\n{bar}\n\nГде и кем работает:",
        "uz": "8/14-savol\n{bar}\n\nQayerda va kim bo'lib ishlaydi:",
    },
    "q9_religion": {
        "ru": "Вопрос 9/14\n{bar}\n\nРелигиозность:",
        "uz": "9/14-savol\n{bar}\n\nDindorligi:",
    },
    "q10_marital": {
        "ru": "Вопрос 10/14\n{bar}\n\nСемейное положение:",
        "uz": "10/14-savol\n{bar}\n\nOilaviy holati:",
    },
    "stage1_complete": {
        "ru": (
            "✅ Анкета заполнена!\n\n"
            "👤 {name} · {age} лет\n\n"
            "Что делаем дальше?"
        ),
        "uz": (
            "✅ Anketa to'ldirildi!\n\n"
            "👤 {name} · {age} yosh\n\n"
            "Keyingi qadam:"
        ),
    },
    # ── Legacy keys (kept for back-compat) ──
    "q3": {
        "ru": "Вопрос 2/14\n{bar}\n\nРост в см (например: 175):",
        "uz": "2/14-savol\n{bar}\n\nBo'yingiz (sm, masalan: 175):",
    },
    "q4": {
        "ru": "Вопрос 4/14\n{bar}\n\nТелосложение:",
        "uz": "4/14-savol\n{bar}\n\nTana tuzilishi:",
    },
    "q5": {
        "ru": "🎓 Вопрос 7/14\n{bar}\n\nОбразование:",
        "uz": "🎓 7/14-savol\n{bar}\n\nMa'lumoti:",
    },
    "q5_university": {
        "ru": "Укажите название вуза и курс:",
        "uz": "OTM nomi va kursini kiriting:",
    },
    "q6_choice": {
        "ru": "Вопрос 8/14\n{bar}\n\nЗанятость:",
        "uz": "8/14-savol\n{bar}\n\nBandligi:",
    },
    "q6": {
        "ru": "Укажите место работы / род деятельности:",
        "uz": "Ish joyini / faoliyat turini ko'rsating:",
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
        "ru": "Вопрос 6/14\n{bar}\n\nГород проживания:",
        "uz": "6/14-savol\n{bar}\n\nYashash shahri:",
    },
    "q9_address": {
        "ru": "🏠 <b>Вопрос 10</b>\n\nАдрес (улица/махалля):\n\n🔒 Адрес не виден в анкете — вы решаете, кому его открыть",
        "uz": "🏠 <b>10-savol</b>\n\nManzil (ko'cha/mahalla):\n\n🔒 Manzil anketada ko'rinmaydi — kimga ochishni o'zingiz hal qilasiz",
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
        "ru": "🌍 Вопрос 5/14\n{bar}\n\nНациональность:",
        "uz": "🌍 5/14-savol\n{bar}\n\nMillati:",
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
        "ru": "🕌 Вопрос 9/14\n{bar}\n\nРелигиозность:",
        "uz": "🕌 9/14-savol\n{bar}\n\nDindorligi:",
    },
    "q_marital_status": {
        "ru": "💍 Вопрос 10/14\n{bar}\n\nСемейное положение:",
        "uz": "💍 10/14-savol\n{bar}\n\nOilaviy holati:",
    },
    "q_children": {
        "ru": "Есть ли дети?",
        "uz": "Farzandlaringiz bormi?",
    },
    "q_parent_phone": {
        "ru": (
            "📞 Вопрос 11/14\n{bar}\n\n"
            "Контактные данные\n\n"
            "Ваши контакты будут переданы\n"
            "только с вашего одобрения.\n"
            "Модератор сначала свяжется\n"
            "с вами и спросит разрешения. 🤝\n\n"
            "Телефон родителей:\n\n"
            "🇺🇿 Узбекистан: +998 90 123 45 67 или 901234567\n"
            "🌍 Другие страны: с кодом и знаком «+»\n"
            "   Пример: +1 213 555 0123 (США)"
        ),
        "uz": (
            "📞 11/14-savol\n{bar}\n\n"
            "Kontaktlar\n\n"
            "Kontaktlaringiz faqat sizning\n"
            "roziligingiz bilan beriladi.\n"
            "Moderator avval siz bilan\n"
            "bog'lanib ruxsat so'raydi. 🤝\n\n"
            "Ota-onalar telefoni:\n\n"
            "🇺🇿 O'zbekiston: +998 90 123 45 67 yoki 901234567\n"
            "🌍 Boshqa davlatlar: kod va «+» bilan\n"
            "   Masalan: +1 213 555 0123 (AQSh)"
        ),
    },
    "q_parent_telegram": {
        "ru": "📱 Вопрос 12/14\n{bar}\n\nTelegram родителей:\n(@username)",
        "uz": "📱 12/14-savol\n{bar}\n\nOta-onalar Telegram:\n(@username)",
    },
    "q_candidate_telegram": {
        "ru": "💬 Вопрос 13/14\n{bar}\n\nTelegram кандидата:\n(@username)",
        "uz": "💬 13/14-savol\n{bar}\n\nNomzod Telegram:\n(@username)",
    },
    "q_tg_at_least_one_required": {
        "ru": "Укажите хотя бы один Telegram — родителей или кандидата.",
        "uz": "Kamida bitta Telegram ko'rsating — ota-onaning yoki nomzodning.",
    },
    "q_at_least_one_contact": {
        "ru": "Укажите хотя бы один контакт — телефон или Telegram.",
        "uz": "Kamida bitta kontakt ko'rsating — telefon yoki Telegram.",
    },
    "q_phone_invalid": {
        "ru": (
            "⚠️ Неверный формат.\n\n"
            "🇺🇿 Узбекистан: +998 90 123 45 67 или 901234567\n"
            "🌍 Международный: с «+» (например +1, +7, +44)"
        ),
        "uz": (
            "⚠️ Format noto'g'ri.\n\n"
            "🇺🇿 O'zbekiston: +998 90 123 45 67 yoki 901234567\n"
            "🌍 Xalqaro: «+» bilan (masalan +1, +7, +44)"
        ),
    },
    "q_photo_optional": {
        "ru": "Фото (необязательно)\n\n🔒 Защищено от скриншотов",
        "uz": "Fotosurat (ixtiyoriy)\n\n🔒 Skrinshotdan himoyalangan",
    },
    "q_phone_optional": {
        "ru": "Телефон родителей (необязательно):",
        "uz": "Ota-onalar telefoni (ixtiyoriy):",
    },
    "extend_invite": {
        "ru": (
            "🌟 <b>Привлеките больше внимания!</b>\n\n"
            "🔖 {display_id}\n\n"
            "Анкета опубликована ✅\n\n"
            "Если добавите подробности:\n"
            "• Больше семей увидят вас 👀\n"
            "• Выше доверие к анкете ⭐\n"
            "• Быстрее найдёте пару 💍\n\n"
            "Займёт всего 5 минут!"
        ),
        "uz": (
            "🌟 <b>Ko'proq e'tibor torting!</b>\n\n"
            "🔖 {display_id}\n\n"
            "Anketangiz nashr etildi ✅\n\n"
            "Batafsil ma'lumot qo'shsangiz:\n"
            "• Ko'proq oilalar ko'radi 👀\n"
            "• Ishonch darajasi oshadi ⭐\n"
            "• Tezroq juft topasiz 💍\n\n"
            "Atigi 5 daqiqa vaqt oladi!"
        ),
    },
    # ── Stage 2: Extended Profile ──
    "ext_housing": {
        "ru": "<b>Дополнение 1/14</b>\nЖилищные условия:",
        "uz": "<b>Qo'shimcha 1/14</b>\nYashash sharoiti:",
    },
    "ext_housing_parent": {
        "ru": "Уточните тип жилья родителей:",
        "uz": "Ota-onaning uy turini aniqlashtiring:",
    },
    "ext_car": {
        "ru": "<b>Дополнение 2/14</b>\nНаличие автомобиля:",
        "uz": "<b>Qo'shimcha 2/14</b>\nAvtomobil mavjudligi:",
    },
    "ext_address": {
        "ru": "<b>Дополнение 3/14</b>\nАдрес (улица/махалля):",
        "uz": "<b>Qo'shimcha 3/14</b>\nManzil (ko'cha/mahalla):",
    },
    "ext_family_region": {
        "ru": "<b>Дополнение 4/14</b>\nРегион происхождения семьи:\n(например: Ташкент, Самарканд)",
        "uz": "<b>Qo'shimcha 4/14</b>\nOila kelib chiqqan hudud:\n(masalan: Toshkent, Samarqand)",
    },
    "ext_father": {
        "ru": "<b>Дополнение 5/14</b>\nОтец — чем занимается:",
        "uz": "<b>Qo'shimcha 5/14</b>\nOtasi — nima bilan shug'ullanadi:",
    },
    "ext_mother": {
        "ru": "<b>Дополнение 6/14</b>\nМать — чем занимается:",
        "uz": "<b>Qo'shimcha 6/14</b>\nOnasi — nima bilan shug'ullanadi:",
    },
    "ext_brothers": {
        "ru": "<b>Дополнение 7/14</b>\nКоличество братьев (0 если нет):",
        "uz": "<b>Qo'shimcha 7/14</b>\nAkalar/ukalar soni (0 bo'lsa yo'q):",
    },
    "ext_sisters": {
        "ru": "Количество сестёр (0 если нет):",
        "uz": "Opalar/singillar soni (0 bo'lsa yo'q):",
    },
    "ext_position": {
        "ru": "<b>Дополнение 8/14</b>\nМесто в семье:",
        "uz": "<b>Qo'shimcha 8/14</b>\nOiladagi o'rni:",
    },
    "ext_health": {
        "ru": "<b>Дополнение 9/14</b>\nОсобенности здоровья (деликатно, если важно):",
        "uz": "<b>Qo'shimcha 9/14</b>\nSog'lig'ining xususiyatlari (biron bir nuqsoni agar bo'lsa):",
    },
    "ext_character": {
        "ru": "<b>Дополнение 10/14</b>\nХарактер и увлечения (пара слов):",
        "uz": "<b>Qo'shimcha 10/14</b>\nXarakter va qiziqishlar (bir necha so'z):",
    },
    "ext_ideal_family": {
        "ru": "<b>Дополнение 11/14</b>\nКак вы представляете идеальную семейную жизнь?",
        "uz": "<b>Qo'shimcha 11/14</b>\nIdeal oilaviy hayotni qanday tasavvur qilasiz?",
    },
    "ext_qualities": {
        "ru": "<b>Дополнение 12/14</b>\nКакие качества в партнёре для вас самые важные?",
        "uz": "<b>Qo'shimcha 12/14</b>\nNomzodning qanday fazilatlari siz uchun eng muhim?",
    },
    "ext_plans": {
        "ru": "<b>Дополнение 13/14</b>\nПланы на ближайшие 5 лет?",
        "uz": "<b>Qo'shimcha 13/14</b>\nYaqin 5 yilga rejalaringiz?",
    },
    "ext_parent_telegram": {
        "ru": "<b>Дополнение 14/14</b>\nTelegram родителей:\n→ @__________",
        "uz": "<b>Qo'shimcha 14/14</b>\nOta-onaning Telegrami:\n→ @__________",
    },
    "ext_candidate_telegram": {
        "ru": "Telegram {child}:\n→ @__________ (или Пропустить)",
        "uz": "{child}ning Telegrami:\n→ @__________ (yoki O'tkazib yuborish)",
    },
    "ext_confirm": {
        "ru": (
            "<b>Готово!</b>\n\n"
            "Все дополнительные данные заполнены.\n"
            "Сохранить в анкету?"
        ),
        "uz": (
            "<b>Tayyor!</b>\n\n"
            "Barcha qo'shimcha ma'lumotlar to'ldirildi.\n"
            "Anketaga saqlashni xohlaysizmi?"
        ),
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
            "🔒 Фото скрыты от скриншотов — вы решаете, кому их показать"
        ),
        "uz": (
            "📸 <b>22-savol — Fotosurat</b>\n\n"
            "Fotosuratni qanday joylashtirmoqchisiz?\n\n"
            "🔒 Foto skrinshotlardan himoyalangan — kimga ko'rsatishni o'zingiz hal qilasiz"
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
            "⭐ VIP анкета — 100 000 сум/мес\n"
            "   • Показывается первой в поиске\n"
            "   • Выделена значком ⭐\n"
            "   • Больше просмотров и обращений\n\n"
            "📋 Обычная анкета — бесплатно\n"
            "   • Стандартное размещение"
        ),
        "uz": (
            "⭐ <b>Joylashtirish turi</b>\n\nTarifni tanlang:\n\n"
            "⭐ VIP anketa — 100 000 so'm/oy\n"
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
            "Анкета отправлена на проверку.\n"
            "Номер: <b>{display_id}</b>\n\n"
            "Модератор проверит в течение 24 часов."
        ),
        "uz": (
            "Anketa tekshiruvga yuborildi.\n"
            "Raqam: <b>{display_id}</b>\n\n"
            "Moderator 24 soat ichida tekshiradi."
        ),
    },

    # ── Step 9: Moderator ──
    "mod_new_profile": {
        "ru": (
            "💁‍♀️ <b>НОВАЯ АНКЕТА НА ПРОВЕРКУ</b>\n\n"
            "🔖 {display_id}\n"
            "{icon} {name} · {age}\n"
            "📍 {city}, {district}\n"
            "📞 {phone}\n"
            "VIP: {vip}\n"
            "📸 Фото: {photo}"
        ),
        "uz": (
            "💁‍♀️ <b>YANGI ANKETA TEKSHIRUVGA</b>\n\n"
            "🔖 {display_id}\n"
            "{icon} {name} · {age}\n"
            "📍 {city}, {district}\n"
            "📞 {phone}\n"
            "VIP: {vip}\n"
            "📸 Fotosurat: {photo}"
        ),
    },
    "mod_profile_published": {
        "ru": (
            "✅ <b>Ваша анкета опубликована!</b>\n\n"
            "🔖 {display_id}\n\n"
            "Теперь тысячи семей могут\n"
            "увидеть вашу анкету.\n\n"
            "Желаем вам счастья и доброй судьбы! 🤲"
        ),
        "uz": (
            "✅ <b>Anketangiz nashr etildi!</b>\n\n"
            "🔖 {display_id}\n\n"
            "Endi minglab oilalar\n"
            "anketangizni ko'rishi mumkin.\n\n"
            "Sizga baxt va xayrli nasib tilaymiz! 🤲"
        ),
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
    "payment_confirmed": {
        "ru": (
            "✅ <b>Оплата подтверждена!</b>\n\n"
            "🔖 {display_id}\n\n"
            "Контакты семьи:\n"
            "{contacts}\n\n"
            "Пусть эта встреча станет\n"
            "началом счастья! 🤲"
        ),
        "uz": (
            "✅ <b>To'lov tasdiqlandi!</b>\n\n"
            "🔖 {display_id}\n\n"
            "Oila kontaktlari:\n"
            "{contacts}\n\n"
            "Bu uchrashuv baxtning\n"
            "boshlanishi bo'lsin! 🤲"
        ),
    },
    "screenshot_received": {
        "ru": (
            "✅ Скриншот получен!\n\n"
            "Модератор проверит оплату\n"
            "и передаст контакт в\n"
            "ближайшее время. 🤝\n\n"
            "Обычно в течение 1-2 часов."
        ),
        "uz": (
            "✅ Skrinshot qabul qilindi!\n\n"
            "Moderator to'lovni tekshirib,\n"
            "ma'lumotlarni yaqin orada yuboradi. 🤝\n\n"
            "Odatda 1-2 soat ichida."
        ),
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
        "ru": "Фильтры поиска:",
        "uz": "Qidiruv filtrlari:",
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

    # ── Step 11: Notification to profile owner ──
    "notify_interest": {
        "ru": (
            "🔔 <b>Новый интерес к вашей анкете!</b>\n"
            "🔖 {display_id}\n\n"
            "Семья из {city} заинтересовалась вашей анкетой.\n\n"
            "О кандидате:\n"
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
            "{city}dan oila sizning anketangizga qiziqish bildirdi.\n\n"
            "Nomzod haqida:\n"
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
            "💰 Стоимость: 30 000 сум"
        ),
        "uz": (
            "💳 <b>Kontakt va manzil olish</b>\n\n"
            "Anketa: {display_id}\n\n"
            "💰 Narxi: 30 000 so'm"
        ),
    },
    "payment_cis": {
        "ru": "💳 <b>Получить контакт и адрес</b>\n\nАнкета: {display_id}\n\n💰 Стоимость: 30 000 сум",
        "uz": "💳 <b>Kontakt va manzil olish</b>\n\nAnketa: {display_id}\n\n💰 Narxi: 30 000 so'm",
    },
    "payment_intl": {
        "ru": "💳 <b>Получить контакт и адрес</b>\n\nАнкета: {display_id}\n\n💰 Стоимость: $15",
        "uz": "💳 <b>Kontakt va manzil olish</b>\n\nAnketa: {display_id}\n\n💰 Narxi: $15",
    },
    "payment_card_transfer": {
        "ru": (
            "Переведите 30 000 сум на карту:\n\n"
            "<code>5614 6887 0899 8959</code>\n"
            "SHODIYEVA NASIBA\n\n"
            "После оплаты отправьте скриншот."
        ),
        "uz": (
            "30 000 so'm kartaga o'tkazing:\n\n"
            "<code>5614 6887 0899 8959</code>\n"
            "SHODIYEVA NASIBA\n\n"
            "To'lovdan so'ng skrinshot yuboring."
        ),
    },
    "op_payment_requisites": {
        "ru": (
            "💁‍♀️ <b>Сообщение от оператора:</b>\n\n"
            "📋 #{req_number}\n\n"
            "Чтобы продолжить, оформите заявку\n"
            "переводом 30 000 сум:\n\n"
            "💳 <code>5614 6887 0899 8959</code>\n"
            "👤 SHODIYEVA NASIBA\n\n"
            "После оформления вам откроются:\n"
            "📞 Телефон семьи\n"
            "📱 Telegram родителей и кандидата\n"
            "🏠 Адрес и геолокация\n"
            "📸 Фото из анкеты\n\n"
            "Пришлите скриншот перевода 👇"
        ),
        "uz": (
            "💁‍♀️ <b>Operatordan xabar:</b>\n\n"
            "📋 #{req_number}\n\n"
            "Davom etish uchun 30 000 so'm\n"
            "to'lovini amalga oshiring:\n\n"
            "💳 <code>5614 6887 0899 8959</code>\n"
            "👤 SHODIYEVA NASIBA\n\n"
            "Rasmiylashtirishdan so'ng sizga ochiladi:\n"
            "📞 Oila telefon raqami\n"
            "📱 Ota-ona va nomzodning Telegram\n"
            "🏠 Manzil va geolokatsiya\n"
            "📸 Anketa surati\n\n"
            "O'tkazma skrinshotini yuboring 👇"
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
            "🔔 <b>Rishta напоминает!</b>\n\n"
            "🔖 {display_id}\n\n"
            "Анкета активна уже 30 дней.\n"
            "Хорошие новости — её уже\n"
            "просмотрели много семей! 👀\n\n"
            "Всё ещё актуально?"
        ),
        "uz": (
            "🔔 <b>Rishta eslatmoqda!</b>\n\n"
            "🔖 {display_id}\n\n"
            "Anketangiz 30 kundan beri faol.\n"
            "Yaxshi xabar — uni allaqachon\n"
            "ko'p oilalar ko'rdi! 👀\n\n"
            "Hali ham dolzarbmi?"
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
    "btn_back": {"ru": "🔙 Назад", "uz": "🔙 Orqaga"},
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
        "ru": "Введите число.",
        "uz": "Raqam kiriting.",
    },
    "invalid_year": {
        "ru": "Введите корректный год рождения (например: 1998).",
        "uz": "To'g'ri tug'ilgan yilni kiriting (masalan: 1998).",
    },
    "invalid_phone": {
        "ru": (
            "⚠️ Неверный формат.\n\n"
            "🇺🇿 Узбекистан: +998 90 123 45 67 или 901234567\n"
            "🌍 Международный: с «+» (например +1, +7, +44)"
        ),
        "uz": (
            "⚠️ Format noto'g'ri.\n\n"
            "🇺🇿 O'zbekiston: +998 90 123 45 67 yoki 901234567\n"
            "🌍 Xalqaro: «+» bilan (masalan +1, +7, +44)"
        ),
    },

    # ── Edit profile ──
    "edit_menu_title": {
        "ru": "<b>Редактирование анкеты</b>\nВыберите что изменить:",
        "uz": "<b>Anketani tahrirlash</b>\nNimani o'zgartirmoqchisiz:",
    },
    "edit_name_prompt": {
        "ru": "Введите новое имя:",
        "uz": "Yangi ismni kiriting:",
    },
    "edit_birth_year_prompt": {
        "ru": "Введите год рождения (например: 1998):",
        "uz": "Yangi tug'ilgan yilni kiriting (masalan: 1998):",
    },
    "edit_height_weight_prompt": {
        "ru": "Введите рост и вес через пробел (например: 175 70):",
        "uz": "Bo'yi va vaznini bo'sh joy bilan kiriting (masalan: 175 70):",
    },
    "edit_city_prompt": {
        "ru": "Город и район (например: Ташкент, Юнусабад):",
        "uz": "Shahar va tumanni kiriting (masalan: Toshkent, Yunusobod):",
    },
    "edit_occupation_prompt": {
        "ru": "Место работы / род деятельности:",
        "uz": "Ish joyi / faoliyat turini kiriting:",
    },
    "edit_photo_prompt": {
        "ru": "Отправьте новое фото:",
        "uz": "Yangi fotosuratni yuboring:",
    },
    "edit_phone_prompt": {
        "ru": "Введите новый номер телефона:",
        "uz": "Yangi telefon raqamini kiriting:",
    },
    "edit_parent_telegram_prompt": {
        "ru": "Введите Telegram родителей (@username):",
        "uz": "Ota-onalar Telegramini kiriting (@username):",
    },
    "edit_candidate_telegram_prompt": {
        "ru": "Введите Telegram кандидата (@username):",
        "uz": "Nomzod Telegramini kiriting (@username):",
    },
    "edit_father_prompt": {
        "ru": "Чем занимается отец:",
        "uz": "Otasi nima bilan shug'ullanadi:",
    },
    "edit_mother_prompt": {
        "ru": "Чем занимается мать:",
        "uz": "Onasi nima bilan shug'ullanadi:",
    },
    "edit_siblings_brothers_prompt": {
        "ru": "Сколько братьев?",
        "uz": "Nechta aka-uka?",
    },
    "edit_siblings_sisters_prompt": {
        "ru": "Сколько сестёр?",
        "uz": "Nechta opa-singil?",
    },
    "edit_siblings_position_prompt": {
        "ru": "Место в семье:",
        "uz": "Oiladagi o'rni:",
    },
    "edit_character_prompt": {
        "ru": "Характер и увлечения (до 500 символов):",
        "uz": "Xarakter va qiziqishlar (500 belgigacha):",
    },
    "edit_health_prompt": {
        "ru": "Особенности здоровья (до 500 символов):",
        "uz": "Sog'lig'ining xususiyatlari (500 belgigacha):",
    },
    "edit_about_prompt": {
        "ru": "О себе и ожиданиях (до 500 символов):",
        "uz": "O'zingiz va kutganlaringiz haqida (500 belgigacha):",
    },
    "edit_body_type_prompt": {
        "ru": "Телосложение:",
        "uz": "Bo'y-bast:",
    },
    "edit_housing_prompt": {
        "ru": "Жильё:",
        "uz": "Turar joy:",
    },
    "edit_housing_parent_prompt": {
        "ru": "Тип жилья родителей:",
        "uz": "Ota-ona uyining turi:",
    },
    "edit_car_prompt": {
        "ru": "Автомобиль:",
        "uz": "Avtomobil:",
    },
    "edit_address_prompt": {
        "ru": "Адрес или геолокация:",
        "uz": "Manzil yoki geolokatsiya:",
    },
    # ── Хаб редактирования (2 раздела) ──
    "edit_hub_title": {
        "ru": "Редактирование анкеты",
        "uz": "Anketani tahrirlash",
    },
    "edit_hub_subtitle": {
        "ru": "Выберите раздел:",
        "uz": "Bo'limni tanlang:",
    },
    "edit_hub_candidate": {
        "ru": "👤 О кандидате",
        "uz": "👤 Nomzod haqida",
    },
    "edit_hub_candidate_desc": {
        "ru": "Имя, фото, контакты, адрес",
        "uz": "Ism, foto, kontakt, manzil",
    },
    "edit_hub_family": {
        "ru": "👨‍👩‍👧 О семье",
        "uz": "👨‍👩‍👧 Oila haqida",
    },
    "edit_hub_family_desc": {
        "ru": "Родители, жильё, характер",
        "uz": "Ota-ona, turar joy, xarakter",
    },
    "edit_section_candidate_title": {
        "ru": "👤 О кандидате",
        "uz": "👤 Nomzod haqida",
    },
    "edit_section_family_title": {
        "ru": "👨‍👩‍👧 О семье",
        "uz": "👨‍👩‍👧 Oila haqida",
    },
    "my_profiles_list_title": {
        "ru": "📋 <b>Мои анкеты:</b>",
        "uz": "📋 <b>Anketalarim:</b>",
    },
    "edit_not_specified": {
        "ru": "—",
        "uz": "—",
    },
    "edit_filled": {
        "ru": "Заполнено",
        "uz": "To'ldirilgan",
    },
    "edit_not_filled": {
        "ru": "Не указано",
        "uz": "Ko'rsatilmagan",
    },
    "edit_photo_uploaded": {
        "ru": "Загружено",
        "uz": "Yuklangan",
    },
    "edit_photo_not_uploaded": {
        "ru": "Не указано",
        "uz": "Ko'rsatilmagan",
    },
    "edit_saved": {
        "ru": "Сохранено.",
        "uz": "Saqlandi.",
    },

    # child labels (genitive) — используются в questionnaire._child_label
    "son": {"ru": "сына", "uz": "O'g'lingiz"},
    "daughter": {"ru": "дочери", "uz": "Qizingiz"},
    "q6_choice_son": {
        "ru": "Вопрос 8/14\n{bar}\n\nЗанятость:",
        "uz": "8/14-savol\n{bar}\n\nBandligi:",
    },
    "q6_choice_daughter": {
        "ru": "Вопрос 8/14\n{bar}\n\nЗанятость:",
        "uz": "8/14-savol\n{bar}\n\nBandligi:",
    },

    # ── VIP flow ──
    "vip_choose_duration": {
        "ru": (
            "⭐ <b>Сделать анкету VIP</b>\n\n"
            "Преимущества:\n"
            "• Показывается первой в поиске\n"
            "• Выделена значком ⭐\n"
            "• Больше внимания от семей\n\n"
            "Выберите срок:"
        ),
        "uz": (
            "⭐ <b>Anketani VIP qilish</b>\n\n"
            "Afzalliklar:\n"
            "• Qidirishda birinchi ko'rinadi\n"
            "• ⭐ belgisi bilan ajratiladi\n"
            "• Oilalardan ko'proq e'tibor\n\n"
            "Muddatni tanlang:"
        ),
    },
    "vip_skip_for_now": {
        "ru": "❌ Без VIP пока",
        "uz": "❌ VIP siz davom etish",
    },
    "vip_skip_message": {
        "ru": (
            "✅ Анкета отправлена на модерацию.\n\n"
            "VIP можно оформить позже:\n"
            "Мои заявки → Моя анкета → Перейти на VIP"
        ),
        "uz": (
            "✅ Anketa tekshiruvga yuborildi.\n\n"
            "VIP keyinroq ham rasmiylashtirishingiz mumkin:\n"
            "Mening arizalarim → Mening anketam → VIPga o'tish"
        ),
    },
    "vip_choose_method": {
        "ru": (
            "⭐ <b>VIP — {days_label}</b>\n"
            "💰 Стоимость: <b>{price}</b>\n\n"
            "Как оплатить?"
        ),
        "uz": (
            "⭐ <b>VIP — {days_label}</b>\n"
            "💰 Narxi: <b>{price}</b>\n\n"
            "Qanday to'laysiz?"
        ),
    },
    "btn_vip_pay_self": {
        "ru": "💳 Оплатить сейчас",
        "uz": "💳 Hozir to'lash",
    },
    "btn_vip_pay_moderator": {
        "ru": "💁‍♀️ Связаться с модератором",
        "uz": "💁‍♀️ Moderator bilan bog'lanish",
    },
    "vip_pay_card_text": {
        "ru": (
            "💳 <b>Реквизиты для оплаты</b>\n\n"
            "Карта: <code>5614 6887 0899 8959</code>\n"
            "Получатель: SHODIYEVA NASIBA\n"
            "Сумма: <b>{price}</b>\n\n"
            "После оплаты нажмите «📤 Отправить скриншот»."
        ),
        "uz": (
            "💳 <b>To'lov rekvizitlari</b>\n\n"
            "Karta: <code>5614 6887 0899 8959</code>\n"
            "Qabul qiluvchi: SHODIYEVA NASIBA\n"
            "Summa: <b>{price}</b>\n\n"
            "To'lovdan so'ng «📤 Skrinshot yuborish» tugmasini bosing."
        ),
    },
    "btn_vip_send_screenshot": {
        "ru": "📤 Отправить скриншот",
        "uz": "📤 Skrinshot yuborish",
    },
    "vip_pay_card_prompt": {
        "ru": "📸 Пришлите скриншот оплаты фотографией.",
        "uz": "📸 To'lov skrinshotini rasm ko'rinishida yuboring.",
    },
    "vip_pay_moderator_text": {
        "ru": (
            "💁‍♀️ <b>Оплата через модератора</b>\n\n"
            "Сумма: <b>{price}</b>\n"
            "Модератор: {moderator}\n\n"
            "Свяжитесь с модератором и укажите номер анкеты {display_id}.\n"
            "После получения оплаты модератор активирует VIP."
        ),
        "uz": (
            "💁‍♀️ <b>Moderator orqali to'lov</b>\n\n"
            "Summa: <b>{price}</b>\n"
            "Moderator: {moderator}\n\n"
            "Moderator bilan bog'lanib, anketa raqamini ko'rsating: {display_id}.\n"
            "To'lovni qabul qilgach, moderator VIP ni faollashtiradi."
        ),
    },
    "vip_request_sent": {
        "ru": (
            "✅ Заявка <b>{display_id}</b> отправлена.\n\n"
            "Модератор проверит оплату и активирует VIP.\n"
            "Обычно это занимает несколько часов."
        ),
        "uz": (
            "✅ Ariza <b>{display_id}</b> yuborildi.\n\n"
            "Moderator to'lovni tekshirib, VIP ni faollashtiradi.\n"
            "Odatda bu bir necha soat vaqt oladi."
        ),
    },
    "vip_confirmed_user": {
        "ru": (
            "🎉 <b>VIP активирован!</b>\n\n"
            "🔖 Анкета: {display_id}\n"
            "📅 Действует до: <b>{expires_at}</b>\n\n"
            "Анкета опубликована и получает приоритет в поиске."
        ),
        "uz": (
            "🎉 <b>VIP faollashtirildi!</b>\n\n"
            "🔖 Anketa: {display_id}\n"
            "📅 Amal qiladi: <b>{expires_at}</b>\n\n"
            "Anketa chop etildi va qidirishda birinchi o'rinda ko'rinadi."
        ),
    },
    "vip_rejected_user": {
        "ru": (
            "⚠️ Оплата VIP не подтверждена.\n"
            "🔖 Заявка: {display_id}\n\n"
            "Свяжитесь с модератором {moderator} для уточнения."
        ),
        "uz": (
            "⚠️ VIP to'lovi tasdiqlanmadi.\n"
            "🔖 Ariza: {display_id}\n\n"
            "Aniqlik uchun moderator bilan bog'laning: {moderator}."
        ),
    },
    "vip_new_request_mod": {
        "ru": (
            "⭐ <b>НОВАЯ VIP-ЗАЯВКА {display_id}</b>\n\n"
            "👤 Пользователь: {username_or_id}\n"
            "🔖 Анкета: {profile_display_id}\n"
            "📅 Срок: {days_label}\n"
            "💰 Сумма: {price}\n"
            "💳 Способ: {method_label}"
        ),
    },
    "vip_method_self_label": {"ru": "Оплата самостоятельно (скриншот)"},
    "vip_method_moderator_label": {"ru": "Через модератора (напрямую)"},

    # ── Disclaimer при выдаче контакта ──
    "contact_disclaimer": {
        "ru": (
            "⚠️ Информация заполнена со слов семьи.\n"
            "Уточняйте детали при встрече.\n"
            "Rishta не отвечает за достоверность\n"
            "данных и результаты знакомства."
        ),
        "uz": (
            "⚠️ Ma'lumotlar — oila so'zlari asosida to'ldirilgan.\n"
            "Tafsilotlarni uchrashuvda aniqlang.\n"
            "Rishta ma'lumotlar va tanishuv natijalari\n"
            "uchun javobgar emas."
        ),
    },

    # ── Фото из анкеты (после передачи контакта) ──
    "contact_photo_regular": {
        "ru": "📸 Фото из анкеты",
        "uz": "📸 Anketa surati",
    },
    "contact_photo_closed": {
        "ru": "📸 Фото из анкеты — лицо закрыто по желанию семьи",
        "uz": "📸 Anketa surati — yuz oila xohishiga ko'ra yopilgan",
    },
    "contact_photo_silhouette": {
        "ru": "📸 Силуэт из анкеты — полное фото по дополнительному согласию",
        "uz": "📸 Anketa siluet — to'liq surat qo'shimcha rozilik asosida",
    },

    # ── Путь Б (диалог с модератором) ──
    "vip_moderator_intro": {
        "ru": (
            "💁‍♀️ <b>Связь с модератором</b>\n\n"
            "Реквизиты для оплаты:\n"
            "Карта: <code>5614 6887 0899 8959</code>\n"
            "Получатель: SHODIYEVA NASIBA\n"
            "Сумма: <b>{price}</b>\n\n"
            "Если нужна помощь — задайте вопрос модератору\n"
            "или пришлите скриншот оплаты."
        ),
        "uz": (
            "💁‍♀️ <b>Moderator bilan aloqa</b>\n\n"
            "To'lov rekvizitlari:\n"
            "Karta: <code>5614 6887 0899 8959</code>\n"
            "Qabul qiluvchi: SHODIYEVA NASIBA\n"
            "Summa: <b>{price}</b>\n\n"
            "Yordam kerak bo'lsa — moderatorga savol bering\n"
            "yoki to'lov skrinshotini yuboring."
        ),
    },
    "vip_ask_prompt": {
        "ru": "✍️ Напишите ваш вопрос модератору одним сообщением.",
        "uz": "✍️ Savolingizni moderatorga bitta xabarda yozing.",
    },
    "vip_question_sent": {
        "ru": (
            "✅ Вопрос отправлен (<b>{display_id}</b>).\n"
            "Модератор ответит в ближайшее время."
        ),
        "uz": (
            "✅ Savol yuborildi (<b>{display_id}</b>).\n"
            "Moderator tez orada javob beradi."
        ),
    },
    "vip_reply_received": {
        "ru": (
            "💁‍♀️ <b>Ответ модератора:</b>\n"
            "🔖 {display_id}\n\n"
            "{text}"
        ),
        "uz": (
            "💁‍♀️ <b>Moderator javobi:</b>\n"
            "🔖 {display_id}\n\n"
            "{text}"
        ),
    },
    "btn_vip_ask_question": {
        "ru": "💬 Задать вопрос",
        "uz": "💬 Savol berish",
    },
    "btn_vip_ask_more": {
        "ru": "💬 Задать ещё",
        "uz": "💬 Yana savol",
    },
    "btn_vip_home": {
        "ru": "🏠 В меню",
        "uz": "🏠 Menyuga",
    },
    "vip_new_question_mod": {
        "ru": (
            "⭐ <b>VIP-ВОПРОС {display_id}</b>\n\n"
            "👤 {username_or_id}\n"
            "🔖 Анкета: {profile_display_id}\n"
            "📅 Срок: {days_label}\n"
            "💰 Сумма: {price}\n\n"
            "❓ Вопрос:\n{question}"
        ),
    },
}


def t(key: str, lang: str = "ru", **kwargs) -> str:
    entry = T.get(key, {})
    text = entry.get(lang, entry.get("ru", f"[{key}]"))
    if kwargs:
        text = text.format(**kwargs)
    return text
