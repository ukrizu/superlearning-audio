import streamlit as st

from gtts import gTTS

import os
import tempfile
from openai import OpenAI
import hashlib
import base64
import time

from dotenv import load_dotenv
load_dotenv()

os.environ["STREAMLIT_DISABLE_WATCHDOG_WARNING"] = "true"

from pydub import AudioSegment

st.set_page_config(page_title="Superlearning Audio Generator", page_icon="🎧", layout="wide")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Authentication
def check_authentication():
    """Check if user is authenticated"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.title("🔐 Přihlášení / Login")
        
        with st.form("login_form"):
            username = st.text_input("Uživatelské jméno / Username")
            password = st.text_input("Heslo / Password", type="password")
            submit = st.form_submit_button("Přihlásit se / Login")
            
            if submit:
                correct_username = os.environ.get("AUTH_USERNAME", "")
                correct_password = os.environ.get("AUTH_PASSWORD", "")
                
                if username == correct_username and password == correct_password:
                    st.session_state.authenticated = True
                    st.success("✅ Přihlášení úspěšné! / Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Nesprávné přihlašovací údaje / Incorrect credentials")
        
        st.stop()

# Check authentication before showing the main app
check_authentication()
def get_flag_img(code, size=40):
    """Get base64 encoded flag image for inline display"""
    flag_path = f"static/flags/{code}.png"
    if os.path.exists(flag_path):
        with open(flag_path, "rb") as f:
            img_bytes = f.read()
            img_b64 = base64.b64encode(img_bytes).decode()
            return f'<img src="data:image/png;base64,{img_b64}" height="{size}" style="vertical-align: middle; margin-left: 10px;">'
    return ""

NATIVE_LANGUAGES = {
    "Čeština": {"code": "cs"},
    "English": {"code": "en"}
}

FOREIGN_LANGUAGES = {
    "de": {
        "code": "de",
        "flag": "de",
        "names": {
            "Čeština": "Němčina",
            "English": "German"
        }
    },
    "es": {
        "code": "es",
        "flag": "es",
        "names": {
            "Čeština": "Španělština",
            "English": "Spanish"
        }
    },
    "fr": {
        "code": "fr",
        "flag": "fr",
        "names": {
            "Čeština": "Francouzština",
            "English": "French"
        }
    },
    "en": {
        "code": "en",
        "flag": "gb",
        "names": {
            "Čeština": "Angličtina",
            "English": "English"
        }
    }
}

# Translations for the entire UI
TRANSLATIONS = {
    "Čeština": {
        "title": "🎧 Generátor nahrávek pro superlearning",
        "subtitle": "Nahrajte textové soubory pro vytvoření audio s rozloženým opakováním pro výuku jazyků.",
        "settings": "⚙️ Nastavení",
        "languages": "🌍 Jazyky",
        "native_lang_label": "Rodný jazyk",
        "native_lang_help": "Jazyk, který již znáte",
        "foreign_lang_label": "Cizí jazyk",
        "foreign_lang_help": "Jazyk, který se učíte",
        "playback_speed": "🎚️ Rychlost přehrávání",
        "native_speed_label": "",
        "native_speed_help": "Násobitel rychlosti pro audio v jazyce {} (1.0 = normální rychlost)",
        "foreign_speed_label": "",
        "foreign_speed_help": "Násobitel rychlosti pro audio v jazyce {} (1.0 = normální rychlost)",
        "timing": "⏸️ Časování",
        "pause_label": "Pauza mezi dvojicemi (ms)",
        "pause_help": "Délka ticha mezi jazykovými dvojicemi",
        "tip": "💡 Tip: Upravte nastavení před generováním audia",
        "file_format": "📄 Formát souboru",
        "pairs_format": "**Jazykové dvojice** (použijte `|` nebo `;`):",
        "foreign_only_format": "**Pouze cizí jazyk** (automatický překlad):",
        "supported_delimiters": "Podporované oddělovače: | nebo ;",
        "delimiter_warning": "⚠️ Používejte pouze jeden typ oddělovače na soubor",
        "format_info": "ℹ️ **DŮLEŽITÉ:** První sloupec = {} (rodný jazyk), Druhý sloupec = {} (cizí jazyk)",
        "language_warning": "⚠️ **POZOR:** Ujistěte se, že vybraný cizí jazyk v nastavení odpovídá jazyku ve druhém sloupci vašeho souboru!",
        "upload_label": "Nahrajte soubor(y) s frázemi (.txt)",
        "batch_processing": "📦 Zpracování {} souborů v dávkovém režimu",
        "translating": "Překlad {} frází z jazyka {} do jazyka {}...",
        "total_ready": "✅ Celkem: {} dvojic frází připraveno",
        "preview_title": "📝 Náhled a úprava překladů",
        "preview_subtitle": "Můžete upravit překlady před generováním audia:",
        "showing_first": "Zobrazení prvních 20 z {} dvojic. Všechny dvojice budou zahrnuty do audia.",
        "generate_button": "🎵 Generovat nahrávku",
        "generating": "Generování nahrávky...",
        "translating_progress": "Překlad {}/{}: {}...",
        "generating_progress": "Generování nahrávky {}/{}: {}...",
        "success": "🎉 Nahrávka úspěšně vygenerována!",
        "download_button": "⬇️ Stáhnout MP3",
        "download_text_button": "📄 Stáhnout textový soubor",
        "error_empty": "Soubor je prázdný",
        "error_multiple_delimiters": "Chyba: Nalezeno více oddělovačů (| a ;) na stejném řádku. Použijte prosím pouze jeden typ oddělovače.",
        "error_multiple_on_line": "Chyba: Nalezeno více oddělovačů na řádku: {}",
        "error_invalid_format": "Neplatný formát na řádku: {}",
        "detected_pairs": "Načteno {} dvojic {}-{}",
        "detected_phrases": "Načteno {} frází pouze v jazyce {}",
        "audio_format": "Formát audia: {} ({}x) → {} ({}x) → {} ms pauza",
        "translation_failed": "Překlad selhal pro: {}",
        "error_generating": "Chyba při generování nahrávky: {}"
    },
    "English": {
        "title": "🎧 Superlearning Audio Generator",
        "subtitle": "Upload text files to generate spaced repetition audio for language learning.",
        "settings": "⚙️ Settings",
        "languages": "🌍 Languages",
        "native_lang_label": "Native language",
        "native_lang_help": "The language you already know",
        "foreign_lang_label": "Foreign language",
        "foreign_lang_help": "The language you're learning",
        "playback_speed": "🎚️ Playback Speed",
        "native_speed_label": "",
        "native_speed_help": "Speed multiplier for {} audio (1.0 = normal speed)",
        "foreign_speed_label": "",
        "foreign_speed_help": "Speed multiplier for {} audio (1.0 = normal speed)",
        "timing": "⏸️ Timing",
        "pause_label": "Pause between pairs (ms)",
        "pause_help": "Duration of silence between language pairs",
        "tip": "💡 Tip: Adjust settings before generating audio",
        "file_format": "📄 File Format",
        "pairs_format": "**Language pairs** (use `|` or `;`):",
        "foreign_only_format": "**Foreign language only** (auto-translate):",
        "supported_delimiters": "Supported delimiters: `|` or `;` only",
        "delimiter_warning": "⚠️ Use only one delimiter type per file",
        "format_info": "ℹ️ **IMPORTANT:** First column = {} (native language), Second column = {} (foreign language)",
        "language_warning": "⚠️ **ATTENTION:** Make sure the selected foreign language in settings matches the language in the second column of your file!",
        "upload_label": "Upload your phrases file(s) (.txt)",
        "batch_processing": "📦 Processing {} files in batch mode",
        "translating": "Translating {} {} phrases to {}...",
        "total_ready": "✅ Total: {} phrase pairs ready",
        "preview_title": "📝 Preview & Edit Translations",
        "preview_subtitle": "You can edit the translations before generating audio:",
        "showing_first": "Showing first 20 of {} pairs. All pairs will be included in audio.",
        "generate_button": "🎵 Generate Audio",
        "generating": "Generating audio file...",
        "translating_progress": "Translating {}/{}: {}...",
        "generating_progress": "Generating audio {}/{}: {}...",
        "success": "🎉 Audio generated successfully!",
        "download_button": "⬇️ Download MP3",
        "download_text_button": "📄 Download text file",
        "error_empty": "File is empty",
        "error_multiple_delimiters": "Error: Multiple delimiters (| and ;) found on the same line. Please use only one delimiter type.",
        "error_multiple_on_line": "Error: Multiple delimiters found on line: {}",
        "error_invalid_format": "Invalid format in line: {}",
        "detected_pairs": "Loaded {} {}-{} pairs",
        "detected_phrases": "Loaded {} {}-only phrases",
        "audio_format": "Audio format: {} ({}x) → {} ({}x) → {}ms pause",
        "translation_failed": "Translation failed for: {}",
        "error_generating": "Error generating audio: {}"
    }
}

def t(key, *args):
    """Get translation for current language"""
    lang = st.session_state.get('ui_language', 'Čeština')
    text = TRANSLATIONS[lang].get(key, TRANSLATIONS['English'][key])
    if args:
        return text.format(*args)
    return text

def get_foreign_lang_name(lang_code):
    """Get foreign language name in current UI language"""
    ui_lang = st.session_state.get('ui_language', 'Čeština')
    return FOREIGN_LANGUAGES[lang_code]['names'][ui_lang]

# Initialize default language if not set
if 'ui_language' not in st.session_state:
    st.session_state.ui_language = 'Čeština'

with st.sidebar:
    st.header(t("settings"))
    
    st.subheader(t("languages"))
    
    # Native language selection
    native_lang = st.selectbox(
        t("native_lang_label"),
        options=list(NATIVE_LANGUAGES.keys()),
        index=list(NATIVE_LANGUAGES.keys()).index("Čeština"),
        help=t("native_lang_help"),
        key="native_lang_select"
    )
    
    # Update UI language when native language changes
    if 'ui_language' not in st.session_state or st.session_state.ui_language != native_lang:
        st.session_state.ui_language = native_lang
        st.rerun()
    
    # Foreign language selection
    foreign_lang_code = st.selectbox(
        t("foreign_lang_label"),
        options=list(FOREIGN_LANGUAGES.keys()),
        format_func=lambda x: get_foreign_lang_name(x),
        index=1,
        help=t("foreign_lang_help"),
        key="foreign_lang_select"
    )
    
    st.markdown("---")
    st.subheader(t("playback_speed"))
    
    # Native language speed slider
    native_speedup = st.slider(
        native_lang,
        min_value=1.0,
        max_value=1.5,
        value=1.15,
        step=0.05,
        help=t("native_speed_help", native_lang)
    )
    
    # Foreign language speed slider
    foreign_speedup = st.slider(
        get_foreign_lang_name(foreign_lang_code),
        min_value=0.8,
        max_value=1.2,
        value=1.0,
        step=0.05,
        help=t("foreign_speed_help", get_foreign_lang_name(foreign_lang_code))
    )
    
    st.markdown("---")
    st.subheader(t("timing"))
    
    pause_duration = st.slider(
        t("pause_label"),
        min_value=1000,
        max_value=5000,
        value=3200,
        step=100,
        help=t("pause_help")
    )
    
    st.markdown("---")
    st.caption(t("tip"))

def detect_delimiter(line):
    """Auto-detect delimiter in a line. Only supports | and ;"""
    delimiters = ['|', ';']
    
    # Check for multiple delimiters on the same line
    found_delimiters = [d for d in delimiters if d in line]
    if len(found_delimiters) > 1:
        return "ERROR_MULTIPLE"
    
    # Check for single delimiter
    for delimiter in delimiters:
        if delimiter in line:
            parts = [p.strip() for p in line.split(delimiter)]
            if len(parts) == 2 and parts[0] and parts[1]:
                return delimiter
    return None

def translate_text(texts, source_lang, target_lang):
    """Translate texts from source language to target language using OpenAI."""
    translated = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, text in enumerate(texts):
        status_text.text(t("translating_progress", i+1, len(texts), text[:50]))
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"Translate the following {source_lang} text to {target_lang}. Return only the translation."},
                    {"role": "user", "content": text}
                ],
            )
            translation = (resp.choices[0].message.content or "").strip()
        except Exception as e:
            translation = f"[Translation error: {e}]"
            st.warning(t("translation_failed", text))
        translated.append(translation)
        progress_bar.progress((i + 1) / len(texts))
    
    progress_bar.empty()
    status_text.empty()
    return translated

def generate_audio(sentences, output_path, pause_ms, native_speed, foreign_speed, native_code, foreign_code):
    """Generate combined MP3 from language pairs."""
    final_audio = AudioSegment.silent(0)

    progress_bar = st.progress(0)
    status_text = st.empty()

    # Fix for incorrect flag/lang mapping
    if foreign_code == "gb": 
        foreign_code = "en"

    for i, (native_text, foreign_text) in enumerate(sentences, 1):
        foreign_text = foreign_text.encode("utf-8", "ignore").decode("utf-8").strip()
        native_text = native_text.encode("utf-8", "ignore").decode("utf-8").strip()
        foreign_text = foreign_text.replace("¿", "").replace("¡", "")

        if not foreign_text:
            continue

        status_text.text(t("generating_progress", i, len(sentences), foreign_text[:50]))

        try:
            native_tts = gTTS(text=native_text, lang=native_code)
            native_path = os.path.join(tempfile.gettempdir(), f"native_{i}.mp3")
            native_tts.save(native_path)
            if not wait_for_file(native_path, timeout=5):
                st.warning(f"⚠️ Timeout: {native_path} was not created in time.")
                continue
            native_audio = AudioSegment.from_mp3(native_path)
            if native_audio.duration_seconds > 0.3 and native_speed != 1:
                native_audio = native_audio.speedup(playback_speed=native_speed)
        except Exception as e:
            st.warning(f"❗ Native audio failed for '{native_text[:50]}': {e}")
            continue

        try:
            foreign_tts = gTTS(text=foreign_text, lang=foreign_code)
            foreign_path = os.path.join(tempfile.gettempdir(), f"foreign_{i}.mp3")
            foreign_tts.save(foreign_path)
            if not wait_for_file(foreign_path, timeout=5):
                st.warning(f"⚠️ Timeout: {foreign_path} was not created in time.")
                continue
            foreign_audio = AudioSegment.from_mp3(foreign_path)
            if foreign_audio.duration_seconds > 0.3 and foreign_speed != 1:
                foreign_audio = foreign_audio.speedup(playback_speed=foreign_speed)
        except Exception as e:
            st.warning(f"❗ Foreign audio failed for '{foreign_text[:50]}': {e}")
            continue

        final_audio += native_audio + foreign_audio + AudioSegment.silent(pause_ms)

        progress_bar.progress(i / len(sentences))

        os.remove(native_path)
        os.remove(foreign_path)

    progress_bar.empty()
    status_text.empty()
    final_audio.export(output_path, format="mp3")

def wait_for_file(path: str, timeout: float = 5.0, interval: float = 0.05) -> bool:
    """
    Waits until file exists and is non-empty.
    Returns True if ready, False if timeout exceeded.
    """
    start = time.time()
    while time.time() - start < timeout:
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return True
        time.sleep(interval)
    return False

def parse_file(uploaded_file, native_lang, foreign_lang_name):
    """Parse uploaded file and detect format."""
    text = uploaded_file.read().decode("utf-8").strip()
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    
    if not lines:
        return None, t("error_empty"), None
    
    delimiter = detect_delimiter(lines[0])
    
    if delimiter == "ERROR_MULTIPLE":
        return None, t("error_multiple_delimiters"), None
    
    if delimiter:
        sentences = []
        for l in lines:
            # Check for multiple delimiters on each line
            line_delimiter = detect_delimiter(l)
            if line_delimiter == "ERROR_MULTIPLE":
                return None, t("error_multiple_on_line", l), None
            
            parts = [p.strip() for p in l.split(delimiter)]
            if len(parts) == 2 and parts[0] and parts[1]:
                native_text, foreign_text = parts
                sentences.append([native_text, foreign_text])
            else:
                return None, t("error_invalid_format", l), None
        return sentences, t("detected_pairs", len(sentences), native_lang, foreign_lang_name), False
    else:
        # Foreign language only - needs translation
        foreign_only = lines
        return foreign_only, t("detected_phrases", len(foreign_only), foreign_lang_name), True

# Title with foreign language flag
flag_html = get_flag_img(FOREIGN_LANGUAGES[foreign_lang_code]["flag"], size=30)
st.markdown(f"# {t('title')}{flag_html}", unsafe_allow_html=True)
st.write(t("subtitle"))

col1, col2 = st.columns([2, 1])

with col2:
    st.markdown(f"""
    ### {t("file_format")}
    
    {t("pairs_format")}
    ```
    Dobrý den|Buenos días
    Guten Tag;Buenos días
    Děkuji|Gracias
    ```
    
    {t("foreign_only_format")}
    ```
    Buenos días
    ¿Cómo estás?
    Gracias
    ```
    
    {t("supported_delimiters")}
    
    {t("delimiter_warning")}
    
    {t("format_info", native_lang, get_foreign_lang_name(foreign_lang_code))}
    
    {t("language_warning")}
    """)

with col1:
    uploaded_files = st.file_uploader(
        t("upload_label"), 
        type=["txt"],
        accept_multiple_files=True
    )

if uploaded_files:
    if len(uploaded_files) > 1:
        st.info(t("batch_processing", len(uploaded_files)))
    
    all_sentences = []
    needs_translation = False
    foreign_only_texts = []
    
    for uploaded_file in uploaded_files:
        st.subheader(f"📄 {uploaded_file.name}")
        
        result, message, is_foreign_only = parse_file(uploaded_file, native_lang, get_foreign_lang_name(foreign_lang_code))
        
        if result is None:
            st.error(f"{message}")
            continue
        
        st.success(message)
        
        if is_foreign_only:
            needs_translation = True
            foreign_only_texts.extend(result)
        else:
            all_sentences.extend(result)
    
    if needs_translation and foreign_only_texts:
        st.info(t("translating", len(foreign_only_texts), get_foreign_lang_name(foreign_lang_code), native_lang))
        native_translations = translate_text(foreign_only_texts, get_foreign_lang_name(foreign_lang_code), native_lang)
        translated_pairs = [[native, foreign] for native, foreign in zip(native_translations, foreign_only_texts)]
        all_sentences.extend(translated_pairs)
    
    if all_sentences:
        st.success(t("total_ready", len(all_sentences)))
        
        content_hash = hashlib.md5(str(all_sentences).encode()).hexdigest()
        
        if 'content_hash' not in st.session_state or st.session_state.content_hash != content_hash:
            st.session_state.content_hash = content_hash
            st.session_state.current_sentences = all_sentences.copy()
            # Clear old edits and generated audio when new files are uploaded
            for key in list(st.session_state.keys()):
                if isinstance(key, str) and (key.startswith('native_') or key.startswith('foreign_')):
                    del st.session_state[key]
            # Clear previously generated audio
            if 'generated_audio' in st.session_state:
                del st.session_state['generated_audio']
            if 'audio_filename' in st.session_state:
                del st.session_state['audio_filename']
        
        with st.expander(t("preview_title"), expanded=False):
            st.write(t("preview_subtitle"))
            
            for i, (native_text, foreign_text) in enumerate(st.session_state.current_sentences[:20], 1):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.text_input(
                        f"{native_lang} #{i}",
                        value=native_text,
                        key=f"native_{i}",
                        label_visibility="collapsed"
                    )
                with col_b:
                    st.text_input(
                        f"{get_foreign_lang_name(foreign_lang_code)} #{i}",
                        value=foreign_text,
                        key=f"foreign_{i}",
                        label_visibility="collapsed"
                    )
            
            if len(st.session_state.current_sentences) > 20:
                st.info(t("showing_first", len(st.session_state.current_sentences)))
        
        sentences_to_use = []
        for i, (native_text, foreign_text) in enumerate(st.session_state.current_sentences, 1):
            edited_native = st.session_state.get(f"native_{i}", native_text) if i <= 20 else native_text
            edited_foreign = st.session_state.get(f"foreign_{i}", foreign_text) if i <= 20 else foreign_text
            sentences_to_use.append([edited_native, edited_foreign])
        
        # Generate text file content with edited phrases
        text_content = "\n".join([f"{native}|{foreign}" for native, foreign in sentences_to_use])
        
        # Show buttons side by side
        col1, col2 = st.columns(2)
        
        with col1:
            generate_clicked = st.button(t("generate_button"), type="primary", use_container_width=True)
        
        with col2:
            st.download_button(
                label=t("download_text_button"),
                data=text_content.encode('utf-8'),
                file_name=f"edited_{NATIVE_LANGUAGES[native_lang]['code']}_{FOREIGN_LANGUAGES[foreign_lang_code]['code']}_{len(sentences_to_use)}_phrases.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        # Generate audio when button is clicked
        if generate_clicked:
            with st.spinner(t("generating")):
                output_path = os.path.join(tempfile.gettempdir(), "superlearning_audio.mp3")
                
                try:
                    generate_audio(
                        sentences_to_use, 
                        output_path, 
                        pause_duration, 
                        native_speedup,
                        foreign_speedup,
                        NATIVE_LANGUAGES[native_lang]["code"],
                        FOREIGN_LANGUAGES[foreign_lang_code]["code"]
                    )
                    
                    with open(output_path, "rb") as audio_file:
                        audio_bytes = audio_file.read()
                    
                    # Store audio in session state
                    st.session_state.generated_audio = audio_bytes
                    st.session_state.audio_filename = f"superlearning_{NATIVE_LANGUAGES[native_lang]['code']}_{FOREIGN_LANGUAGES[foreign_lang_code]['code']}_{len(sentences_to_use)}_phrases.mp3"
                    st.success(t("success"))
                    
                except Exception as e:
                    st.error(t("error_generating", e))
        
        # Display audio player and download button if audio has been generated
        if 'generated_audio' in st.session_state and st.session_state.generated_audio:
            st.audio(st.session_state.generated_audio, format="audio/mp3")
            
            st.download_button(
                label=t("download_button"),
                data=st.session_state.generated_audio,
                file_name=st.session_state.get('audio_filename', 'superlearning_audio.mp3'),
                mime="audio/mp3",
                use_container_width=True
            )

st.markdown("---")
st.caption(t("audio_format", native_lang, native_speedup, get_foreign_lang_name(foreign_lang_code), foreign_speedup, pause_duration))
