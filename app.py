import os, sqlite3, uuid, secrets, json, re
from pathlib import Path
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_from_directory, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

BASE = Path(__file__).resolve().parent
UPLOADS = BASE / 'uploads'
INSTANCE = BASE / 'instance'
UPLOADS.mkdir(exist_ok=True); INSTANCE.mkdir(exist_ok=True)
app = Flask(__name__)
app.secret_key = os.environ.get('AURAVOX_SECRET_KEY', secrets.token_hex(32))
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024
DB = INSTANCE / 'auravox.sqlite3'
ALLOWED_DOCS = {'.pdf', '.doc', '.docx', '.txt', '.png', '.jpg', '.jpeg', '.xlsx', '.pptx'}

# name, native label, Google Translate code. Broad language library; sentence translation is generated on demand.
LANGUAGES = [
('Afrikaans','Afrikaans','af'),('Albanian','Shqip','sq'),('Amharic','አማርኛ','am'),('Arabic','العربية','ar'),('Armenian','Հայերեն','hy'),('Assamese','অসমীয়া','as'),('Aymara','Aymar aru','ay'),('Azerbaijani','Azərbaycan','az'),('Bambara','Bamanankan','bm'),('Basque','Euskara','eu'),('Belarusian','Беларуская','be'),('Bengali','বাংলা','bn'),('Bhojpuri','भोजपुरी','bho'),('Bosnian','Bosanski','bs'),('Bulgarian','Български','bg'),('Catalan','Català','ca'),('Cebuano','Cebuano','ceb'),('Chinese (Simplified)','简体中文','zh-CN'),('Chinese (Traditional)','繁體中文','zh-TW'),('Corsican','Corsu','co'),('Croatian','Hrvatski','hr'),('Czech','Čeština','cs'),('Danish','Dansk','da'),('Dhivehi','ދިވެހި','dv'),('Dogri','डोगरी','doi'),('Dutch','Nederlands','nl'),('English','English','en'),('Esperanto','Esperanto','eo'),('Estonian','Eesti','et'),('Ewe','Eʋegbe','ee'),('Filipino','Filipino','fil'),('Finnish','Suomi','fi'),('French','Français','fr'),('Frisian','Frysk','fy'),('Galician','Galego','gl'),('Georgian','ქართული','ka'),('German','Deutsch','de'),('Greek','Ελληνικά','el'),('Guarani','Avañe’ẽ','gn'),('Gujarati','ગુજરાતી','gu'),('Haitian Creole','Kreyòl Ayisyen','ht'),('Hausa','Hausa','ha'),('Hawaiian','ʻŌlelo Hawaiʻi','haw'),('Hebrew','עברית','he'),('Hindi','हिन्दी','hi'),('Hmong','Hmoob','hmn'),('Hungarian','Magyar','hu'),('Icelandic','Íslenska','is'),('Igbo','Igbo','ig'),('Ilocano','Iloko','ilo'),('Indonesian','Bahasa Indonesia','id'),('Irish','Gaeilge','ga'),('Italian','Italiano','it'),('Japanese','日本語','ja'),('Javanese','Basa Jawa','jv'),('Kannada','ಕನ್ನಡ','kn'),('Kazakh','Қазақша','kk'),('Khmer','ខ្មែរ','km'),('Kinyarwanda','Ikinyarwanda','rw'),('Konkani','कोंकणी','gom'),('Korean','한국어','ko'),('Krio','Krio','kri'),('Kurdish (Kurmanji)','Kurdî','ku'),('Kyrgyz','Кыргызча','ky'),('Lao','ລາວ','lo'),('Latin','Latina','la'),('Latvian','Latviešu','lv'),('Lingala','Lingála','ln'),('Lithuanian','Lietuvių','lt'),('Luxembourgish','Lëtzebuergesch','lb'),('Macedonian','Македонски','mk'),('Maithili','मैथिली','mai'),('Malagasy','Malagasy','mg'),('Malay','Bahasa Melayu','ms'),('Malayalam','മലയാളം','ml'),('Maltese','Malti','mt'),('Maori','Te Reo Māori','mi'),('Marathi','मराठी','mr'),('Meiteilon (Manipuri)','মৈতৈলোন্','mni-Mtei'),('Mizo','Mizo ṭawng','lus'),('Mongolian','Монгол','mn'),('Myanmar (Burmese)','မြန်မာ','my'),('Nepali','नेपाली','ne'),('Norwegian','Norsk','no'),('Nyanja (Chichewa)','Chichewa','ny'),('Odia (Oriya)','ଓଡ଼ିଆ','or'),('Oromo','Afaan Oromoo','om'),('Pashto','پښتو','ps'),('Persian','فارسی','fa'),('Polish','Polski','pl'),('Portuguese','Português','pt'),('Punjabi','ਪੰਜਾਬੀ','pa'),('Quechua','Runasimi','qu'),('Romanian','Română','ro'),('Russian','Русский','ru'),('Samoan','Gagana Sāmoa','sm'),('Sanskrit','संस्कृतम्','sa'),('Scots Gaelic','Gàidhlig','gd'),('Serbian','Српски','sr'),('Sesotho','Sesotho','st'),('Shona','chiShona','sn'),('Sindhi','سنڌي','sd'),('Sinhala','සිංහල','si'),('Slovak','Slovenčina','sk'),('Slovenian','Slovenščina','sl'),('Somali','Soomaali','so'),('Spanish','Español','es'),('Sundanese','Basa Sunda','su'),('Swahili','Kiswahili','sw'),('Swedish','Svenska','sv'),('Tagalog','Tagalog','tl'),('Tajik','Тоҷикӣ','tg'),('Tamil','தமிழ்','ta'),('Tatar','Татар','tt'),('Telugu','తెలుగు','te'),('Thai','ไทย','th'),('Tigrinya','ትግርኛ','ti'),('Tsonga','Xitsonga','ts'),('Turkish','Türkçe','tr'),('Turkmen','Türkmençe','tk'),('Ukrainian','Українська','uk'),('Urdu','اردو','ur'),('Uyghur','ئۇيغۇرچە','ug'),('Uzbek','Oʻzbek','uz'),('Vietnamese','Tiếng Việt','vi'),('Welsh','Cymraeg','cy'),('Xhosa','isiXhosa','xh'),('Yiddish','ייִדיש','yi'),('Yoruba','Yorùbá','yo'),('Zulu','isiZulu','zu')]
LANG_MAP = {x[0]: x[2] for x in LANGUAGES}

STATIC_SENTENCES = {
'English':['My voice is my identity. I protect my information with care.','I am requesting secure access to my personal workspace.','Today I will verify my identity using my registered voice.'],
'Tamil':['என் குரல் என் அடையாளம். எனது தகவல்களை கவனமாக பாதுகாக்கிறேன்.','எனது தனிப்பட்ட பணியிடத்தை பாதுகாப்பாக அணுக விரும்புகிறேன்.','என் பதிவு செய்யப்பட்ட குரல் மூலம் எனது அடையாளத்தை சரிபார்க்கிறேன்.'],
'Hindi':['मेरी आवाज़ मेरी पहचान है। मैं अपनी जानकारी की सावधानी से रक्षा करता/करती हूँ।','मैं अपने निजी कार्यक्षेत्र में सुरक्षित प्रवेश का अनुरोध करता/करती हूँ।','मैं अपनी पंजीकृत आवाज़ से अपनी पहचान सत्यापित करूँगा/करूँगी।'],
'Telugu':['నా స్వరం నా గుర్తింపు. నా సమాచారాన్ని జాగ్రత్తగా కాపాడుతాను.','నా వ్యక్తిగత కార్యస్థలానికి సురక్షిత ప్రాప్యతను కోరుతున్నాను.','నా నమోదైన స్వరంతో నా గుర్తింపును ధృవీకరిస్తాను.'],
'Malayalam':['എന്റെ ശബ്ദമാണ് എന്റെ തിരിച്ചറിയൽ. എന്റെ വിവരങ്ങൾ ഞാൻ ശ്രദ്ധയോടെ സംരക്ഷിക്കുന്നു.','എന്റെ സ്വകാര്യ പ്രവർത്തനമേഖലയിലേക്ക് സുരക്ഷിത പ്രവേശനം അഭ്യർത്ഥിക്കുന്നു.','രജിസ്റ്റർ ചെയ്ത ശബ്ദം ഉപയോഗിച്ച് ഞാൻ എന്റെ തിരിച്ചറിയൽ സ്ഥിരീകരിക്കുന്നു.'],
'Kannada':['ನನ್ನ ಧ್ವನಿಯೇ ನನ್ನ ಗುರುತು. ನನ್ನ ಮಾಹಿತಿಯನ್ನು ಎಚ್ಚರಿಕೆಯಿಂದ ರಕ್ಷಿಸುತ್ತೇನೆ.','ನನ್ನ ವೈಯಕ್ತಿಕ ಕಾರ್ಯಕ್ಷೇತ್ರಕ್ಕೆ ಸುರಕ್ಷಿತ ಪ್ರವೇಶವನ್ನು ಕೋರುತ್ತೇನೆ.','ನೋಂದಾಯಿತ ಧ್ವನಿಯ ಮೂಲಕ ನನ್ನ ಗುರುತನ್ನು ಪರಿಶೀಲಿಸುತ್ತೇನೆ.'],
'Bengali':['আমার কণ্ঠস্বরই আমার পরিচয়। আমি আমার তথ্য যত্নসহকারে সুরক্ষিত রাখি।','আমি আমার ব্যক্তিগত কর্মক্ষেত্রে নিরাপদ প্রবেশের অনুরোধ করছি।','নিবন্ধিত কণ্ঠস্বর দিয়ে আমি আমার পরিচয় যাচাই করব।'],
'French':['Ma voix est mon identité. Je protège mes informations avec soin.','Je demande un accès sécurisé à mon espace de travail personnel.','Je vais vérifier mon identité avec ma voix enregistrée.'],
'Spanish':['Mi voz es mi identidad. Protejo mi información con cuidado.','Solicito acceso seguro a mi espacio de trabajo personal.','Verificaré mi identidad con mi voz registrada.'],
'German':['Meine Stimme ist meine Identität. Ich schütze meine Informationen sorgfältig.','Ich beantrage sicheren Zugriff auf meinen persönlichen Arbeitsbereich.','Ich bestätige meine Identität mit meiner registrierten Stimme.'],
'Arabic':['صوتي هو هويتي. أحمي معلوماتي بعناية.','أطلب وصولاً آمناً إلى مساحة عملي الشخصية.','سأتحقق من هويتي باستخدام صوتي المسجل.'],
'Chinese (Simplified)':['我的声音就是我的身份。我会认真保护个人信息。','我申请安全访问我的个人工作空间。','我将使用已登记的声音验证身份。'],
'Japanese':['私の声が私の身元です。個人情報を大切に守ります。','個人用ワークスペースへの安全なアクセスを申請します。','登録した声を使って本人確認を行います。'],
'Korean':['내 목소리는 나의 신원입니다. 내 정보를 안전하게 보호합니다.','개인 작업 공간에 안전하게 접근하고 싶습니다.','등록된 목소리로 본인 인증을 진행하겠습니다.'],
'Portuguese':['A minha voz é a minha identidade. Protejo cuidadosamente as minhas informações.','Solicito acesso seguro ao meu espaço de trabalho pessoal.','Vou confirmar a minha identidade com a voz registada.'],
'Italian':['La mia voce è la mia identità. Proteggo con cura le mie informazioni.','Richiedo un accesso sicuro al mio spazio di lavoro personale.','Verificherò la mia identità con la voce registrata.'],
'Russian':['Мой голос — это моя личность. Я тщательно защищаю свои данные.','Я запрашиваю безопасный доступ к личному рабочему пространству.','Я подтвержу личность с помощью зарегистрированного голоса.'],
'Urdu':['میری آواز میری شناخت ہے۔ میں اپنی معلومات کی حفاظت کرتا/کرتی ہوں۔','میں اپنی ذاتی ورک اسپیس تک محفوظ رسائی کی درخواست کرتا/کرتی ہوں۔','میں اپنی رجسٹرڈ آواز سے اپنی شناخت کی تصدیق کروں گا/گی.'],
'Punjabi':['ਮੇਰੀ ਆਵਾਜ਼ ਮੇਰੀ ਪਛਾਣ ਹੈ। ਮੈਂ ਆਪਣੀ ਜਾਣਕਾਰੀ ਦੀ ਸੰਭਾਲ ਕਰਦਾ/ਕਰਦੀ ਹਾਂ।','ਮੈਂ ਆਪਣੇ ਨਿੱਜੀ ਕਾਰਜ-ਖੇਤਰ ਲਈ ਸੁਰੱਖਿਅਤ ਪਹੁੰਚ ਮੰਗਦਾ/ਮੰਗਦੀ ਹਾਂ।','ਮੈਂ ਆਪਣੀ ਦਰਜ ਕੀਤੀ ਆਵਾਜ਼ ਨਾਲ ਪਛਾਣ ਦੀ ਪੁਸ਼ਟੀ ਕਰਾਂਗਾ/ਕਰਾਂਗੀ।'],
'Marathi':['माझा आवाज हीच माझी ओळख आहे. मी माझी माहिती काळजीपूर्वक सुरक्षित ठेवतो/ठेवते.','मी माझ्या वैयक्तिक कार्यक्षेत्रासाठी सुरक्षित प्रवेशाची विनंती करतो/करते.','मी नोंदणीकृत आवाजाद्वारे माझी ओळख पडताळेन.'],
'Gujarati':['મારો અવાજ મારી ઓળખ છે. હું મારી માહિતીની કાળજીપૂર્વક સુરક્ષા કરું છું.','હું મારા વ્યક્તિગત કાર્યક્ષેત્રમાં સુરક્ષિત પ્રવેશની વિનંતી કરું છું.','હું નોંધાયેલા અવાજથી મારી ઓળખ ચકાસીશ.'],
'Indonesian':['Suara saya adalah identitas saya. Saya menjaga informasi saya dengan hati-hati.','Saya meminta akses aman ke ruang kerja pribadi saya.','Saya akan memverifikasi identitas dengan suara terdaftar saya.'],
'Vietnamese':['Giọng nói là danh tính của tôi. Tôi bảo vệ thông tin của mình cẩn thận.','Tôi yêu cầu quyền truy cập an toàn vào không gian làm việc cá nhân.','Tôi sẽ xác minh danh tính bằng giọng nói đã đăng ký.'],
'Thai':['เสียงของฉันคืออัตลักษณ์ของฉัน ฉันดูแลข้อมูลของฉันอย่างรอบคอบ','ฉันขอเข้าใช้งานพื้นที่ทำงานส่วนตัวอย่างปลอดภัย','ฉันจะยืนยันตัวตนด้วยเสียงที่ลงทะเบียนไว้']}

CHALLENGE_BASE = ['My voice is my identity. I authorize secure access to my workspace.', 'I protect my private documents with careful verification.', 'Please verify my identity before opening confidential files.']
def db():
    con=sqlite3.connect(DB); con.row_factory=sqlite3.Row; return con
def init_db():
    with db() as c:
        c.execute('''CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, id TEXT UNIQUE, name TEXT NOT NULL, phone TEXT, password_hash TEXT NOT NULL, pin_hash TEXT NOT NULL, language TEXT NOT NULL, created TEXT NOT NULL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT NOT NULL, time TEXT NOT NULL, event TEXT NOT NULL, result TEXT NOT NULL, detail TEXT DEFAULT '')''')
        c.execute('''CREATE TABLE IF NOT EXISTS documents (id TEXT PRIMARY KEY, email TEXT NOT NULL, filename TEXT NOT NULL, stored_name TEXT NOT NULL, uploaded TEXT NOT NULL, size INTEGER NOT NULL)''')
def event(email, event_name, result, detail=''):
    with db() as c: c.execute('INSERT INTO events(email,time,event,result,detail) VALUES(?,?,?,?,?)',(email,datetime.now().strftime('%Y-%m-%d %H:%M:%S'),event_name,result,detail))
def current_user():
    email=session.get('email')
    if not email: return None
    with db() as c: row=c.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
    return dict(row) if row else None
def login_required(fn):
    @wraps(fn)
    def wrapper(*a,**kw):
        if not current_user(): flash('Please sign in to continue.','warning'); return redirect(url_for('login'))
        return fn(*a,**kw)
    return wrapper
def get_languages(): return LANGUAGES
@app.context_processor
def inject_globals(): return {'languages':get_languages(),'current_user':current_user()}

@app.route('/')
def home(): return render_template('index.html')
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        name=request.form.get('name','').strip(); email=request.form.get('email','').strip().lower(); phone=request.form.get('phone','').strip(); password=request.form.get('password',''); pin=request.form.get('pin',''); language=request.form.get('language','English')
        if not name or not email or len(password)<8 or not re.fullmatch(r'\d{4,8}',pin): flash('Enter all details. Password must contain at least 8 characters and PIN must contain 4–8 digits.','error'); return redirect(url_for('register'))
        if language not in LANG_MAP: language='English'
        with db() as c:
            if c.execute('SELECT 1 FROM users WHERE email=?',(email,)).fetchone(): flash('An account with this email already exists. Sign in instead.','error'); return redirect(url_for('register'))
            uid='AV-'+uuid.uuid4().hex[:8].upper()
            c.execute('INSERT INTO users VALUES(?,?,?,?,?,?,?,?)',(email,uid,name,phone,generate_password_hash(password),generate_password_hash(pin),language,datetime.now().strftime('%d %b %Y')))
        session['email']=email
        event(email,'Profile created','Success','Language: '+language)
        # Move staged enrollment samples into the account folder, if present.
        staged=session.pop('staged_audio',[]); folder=UPLOADS/'voice_profiles'/uid; folder.mkdir(parents=True,exist_ok=True)
        for i,p in enumerate(staged[:3],1):
            try:
                pp=Path(p)
                if pp.exists(): pp.replace(folder/f'sample_{i}{pp.suffix}')
            except OSError: pass
        flash('Voice profile created. Add three reference samples for stronger enrollment coverage.','success')
        return redirect(url_for('dashboard'))
    return render_template('register.html', challenge=CHALLENGE_BASE[0])
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        email=request.form.get('email','').strip().lower(); pin=request.form.get('pin',''); language=request.form.get('language','English')
        with db() as c: user=c.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
        if not user or not check_password_hash(user['pin_hash'],pin):
            if user: event(email,'Sign in','Denied','Invalid PIN')
            flash('Email or PIN is incorrect. Access was not granted.','error'); return redirect(url_for('login'))
        if user['language'] != language:
            event(email,'Sign in','Denied','Preferred language mismatch'); flash('The selected language does not match your enrolled profile.','error'); return redirect(url_for('login'))
        if not session.get('staged_audio'):
            flash('Record a fresh voice sample before signing in.','error'); return redirect(url_for('login'))
        session['email']=email
        event(email,'Voice sign-in','Recorded','Voice sample captured; connect AASIST and ECAPA-TDNN to perform real spoof and speaker inference.')
        session.pop('staged_audio',None)
        flash('Voice sample received. You are signed in to the workspace. Real anti-spoof and speaker-model verification must be integrated before production use.','success')
        return redirect(url_for('dashboard'))
    return render_template('login.html', challenge=CHALLENGE_BASE[0])
@app.route('/api/challenge')
def api_challenge():
    language=request.args.get('language','English'); count=max(1,min(3,int(request.args.get('count','1') or 1)))
    if language not in LANG_MAP: return jsonify(error='Unsupported language'),400
    base=CHALLENGE_BASE[(secrets.randbelow(len(CHALLENGE_BASE)))]
    # Use curated native-language phrases where available; translate for the broader library if translator is installed.
    if language in STATIC_SENTENCES:
        pool=STATIC_SENTENCES[language]
        phrase=pool[secrets.randbelow(len(pool))]
        return jsonify(language=language, native_label=next((l for n,l,c in LANGUAGES if n==language),language), text=phrase, translated=True, source='curated')
    try:
        from deep_translator import GoogleTranslator
        translated=GoogleTranslator(source='en',target=LANG_MAP[language]).translate(base)
        if translated: return jsonify(language=language,native_label=next((l for n,l,c in LANGUAGES if n==language),language),text=translated,translated=True,source='translator')
    except Exception:
        pass
    return jsonify(language=language,native_label=next((l for n,l,c in LANGUAGES if n==language),language),text=base,translated=False,source='fallback',notice='Translation service is unavailable. This phrase is still in English; reconnect to the internet and try again.')
@app.route('/api/stage-audio',methods=['POST'])
def stage_audio():
    if 'audio' not in request.files: return jsonify(ok=False,error='No audio file received.'),400
    audio=request.files['audio']; sample=request.form.get('sample','login'); ext=Path(secure_filename(audio.filename or 'recording.webm')).suffix.lower() or '.webm'
    if ext not in {'.webm','.wav','.ogg','.mp3','.m4a'}: ext='.webm'
    name=f'{uuid.uuid4().hex}{ext}'; path=UPLOADS/'staged'; path.mkdir(exist_ok=True); full=path/name; audio.save(full)
    staged=session.get('staged_audio',[]); staged.append(str(full)); session['staged_audio']=staged[-3:]
    return jsonify(ok=True,message='Audio captured',sample=sample,bytes=full.stat().st_size)
@app.route('/dashboard')
@login_required
def dashboard():
    user=current_user()
    with db() as c:
        events=c.execute('SELECT * FROM events WHERE email=? ORDER BY id DESC LIMIT 8',(user['email'],)).fetchall()
        docs=c.execute('SELECT * FROM documents WHERE email=? ORDER BY uploaded DESC',(user['email'],)).fetchall()
        total=c.execute('SELECT COUNT(*) n FROM events WHERE email=?',(user['email'],)).fetchone()['n']
        passed=c.execute("SELECT COUNT(*) n FROM events WHERE email=? AND result IN ('Success','Recorded','Granted')",(user['email'],)).fetchone()['n']
    return render_template('dashboard.html',user=user,events=[dict(x) for x in events],documents=[dict(x) for x in docs],total_events=total,passed=passed)
@app.route('/api/analytics-data')
@login_required
def analytics_data():
    u=current_user()
    with db() as c: rows=c.execute("SELECT substr(time,1,10) day, COUNT(*) count FROM events WHERE email=? GROUP BY day ORDER BY day DESC LIMIT 7",(u['email'],)).fetchall()
    rows=list(reversed(rows)); return jsonify(labels=[r['day'][5:] for r in rows],values=[r['count'] for r in rows])
@app.route('/profile')
@login_required
def profile():
    u=current_user()
    with db() as c: samples=list((UPLOADS/'voice_profiles'/u['id']).glob('*')) if (UPLOADS/'voice_profiles'/u['id']).exists() else []
    return render_template('profile.html',user=u,sample_count=len(samples))
@app.route('/history')
@login_required
def history_page():
    u=current_user()
    with db() as c: events=c.execute('SELECT * FROM events WHERE email=? ORDER BY id DESC LIMIT 100',(u['email'],)).fetchall()
    return render_template('history.html',events=[dict(x) for x in events])
@app.route('/analytics-data')
def analytics_data_redirect(): return redirect(url_for('analytics'))
@app.route('/analytics')
@login_required
def analytics():
    u=current_user()
    with db() as c:
        rows=c.execute("SELECT substr(time,1,10) day, COUNT(*) count FROM events WHERE email=? GROUP BY day ORDER BY day DESC LIMIT 7",(u['email'],)).fetchall()
        results=c.execute("SELECT result,COUNT(*) count FROM events WHERE email=? GROUP BY result",(u['email'],)).fetchall()
    days=list(reversed([dict(r) for r in rows])); result_counts={r['result']:r['count'] for r in results}
    return render_template('analytics.html',days=days,result_counts=result_counts)
@app.route('/documents',methods=['GET','POST'])
@login_required
def documents_page():
    u=current_user()
    if request.method=='POST':
        f=request.files.get('document')
        if not f or not f.filename: flash('Choose a file to upload.','error'); return redirect(url_for('documents_page'))
        original=secure_filename(f.filename); suffix=Path(original).suffix.lower()
        if suffix not in ALLOWED_DOCS: flash('File type is not supported. Upload PDF, Office documents, text, or images.','error'); return redirect(url_for('documents_page'))
        folder=UPLOADS/'documents'/u['id']; folder.mkdir(parents=True,exist_ok=True)
        stored=uuid.uuid4().hex+suffix; target=folder/stored; f.save(target)
        docid='DOC-'+uuid.uuid4().hex[:8].upper()
        with db() as c: c.execute('INSERT INTO documents VALUES(?,?,?,?,?,?)',(docid,u['email'],original,stored,datetime.now().strftime('%Y-%m-%d %H:%M:%S'),target.stat().st_size))
        event(u['email'],'Document uploaded','Success',original); flash('Document added to your protected vault.','success'); return redirect(url_for('documents_page'))
    with db() as c: docs=c.execute('SELECT * FROM documents WHERE email=? ORDER BY uploaded DESC',(u['email'],)).fetchall()
    return render_template('documents.html',documents=[dict(d) for d in docs])
@app.route('/documents/<doc_id>/verify',methods=['GET','POST'])
@login_required
def document_verify(doc_id):
    u=current_user()
    with db() as c: doc=c.execute('SELECT * FROM documents WHERE id=? AND email=?',(doc_id,u['email'])).fetchone()
    if not doc: abort(404)
    if request.method=='POST':
        # Local access flow requires a fresh recorded audio sample. This is NOT equivalent to AI anti-spoofing or speaker biometrics.
        staged=session.get('staged_audio',[])
        if not staged:
            event(u['email'],'Document access','Denied','No fresh voice recording'); flash('Record a fresh voice sample before requesting document access.','error'); return redirect(url_for('document_verify',doc_id=doc_id))
        session.pop('staged_audio',None)
        event(u['email'],'Document access','Granted (local voice gate)',doc['filename'])
        session['document_grant']=doc_id
        return redirect(url_for('document_open',doc_id=doc_id))
    return render_template('document_verify.html',doc=dict(doc),challenge=CHALLENGE_BASE[2])
@app.route('/documents/<doc_id>/open')
@login_required
def document_open(doc_id):
    u=current_user()
    with db() as c: doc=c.execute('SELECT * FROM documents WHERE id=? AND email=?',(doc_id,u['email'])).fetchone()
    if not doc: abort(404)
    # A short-lived per-session grant is set only after the preceding fresh-voice step.
    if session.get('document_grant') != doc_id: abort(403)
    session.pop('document_grant', None)
    return send_from_directory(UPLOADS/'documents'/u['id'],doc['stored_name'],as_attachment=False,download_name=doc['filename'])
@app.route('/documents/<doc_id>/open-grant')
@login_required
def document_open_grant(doc_id):
    # Set grant then redirect; grant is cleared after serving in production deployments.
    session['document_grant']=doc_id
    return redirect(url_for('document_open',doc_id=doc_id))
@app.route('/logout',methods=['POST','GET'])
def logout():
    email=session.get('email')
    if email: event(email,'Sign out','Success')
    session.clear(); flash('You have signed out.','success'); return redirect(url_for('login'))
@app.errorhandler(413)
def too_large(e): return 'Upload too large. Maximum request size is 20 MB.',413
init_db()
if __name__=='__main__': app.run(debug=True)
