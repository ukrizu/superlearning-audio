# Superlearning Audio Generator

## Overview

A Streamlit-based web application that generates spaced repetition audio files for language learning. The app supports multiple language pairs (Czech, Spanish, German), automatically translates between languages using OpenAI's API, and creates MP3 files with customizable playback speeds and pauses optimized for the superlearning method.

**Updated:** October 29, 2025 - Added multi-language support, independent speed controls, and renamed to Superlearning Audio Generator.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

### October 29, 2025 - Multi-Language Support & Enhanced Controls
1. **Language Selection**: Choose any combination of Czech, Spanish, and German
   - Native language (learning target, plays faster)
   - Foreign language (reference, customizable speed)
2. **Independent Speed Controls**:
   - Native language: 1.0-1.5x speed (default 1.15x)
   - Foreign language: 0.8-1.2x speed (default 1.0x)
3. **Renamed to "Superlearning Audio Generator"** - reflecting broader language support
4. **Language-agnostic translation** - supports any language pair combination

### October 29, 2025 - Enhanced Feature Set
1. **Multiple Delimiter Support**: Auto-detection of pipe (|), semicolon (;), comma (,), and tab delimiters
2. **Batch Processing**: Upload and process multiple files simultaneously
3. **Customizable Settings Sidebar**:
   - Adjustable pause duration (1000-5000ms, default: 3200ms)
   - Adjustable playback speeds for both languages
4. **Translation Preview & Editing**: View and edit translations before audio generation (first 20 pairs)
5. **Improved Session State Management**: Content-based hashing ensures fresh data on file changes

## System Architecture

### Frontend Framework
**Decision:** Streamlit  
**Rationale:** Provides rapid development of interactive web interfaces with minimal boilerplate code. Ideal for data-focused applications with built-in progress indicators and file handling.

**Features:**
- Two-column layout with file upload and format guide
- Settings sidebar for language selection and playback customization
- Expandable preview/edit section for translations
- Audio playback and download capabilities

**Pros:** Simple deployment, built-in UI components, reactive state management  
**Cons:** Less customization than traditional web frameworks

### Audio Processing Pipeline
**Decision:** gTTS (Google Text-to-Speech) + pydub for audio manipulation  
**Rationale:** gTTS provides free, reliable text-to-speech conversion for multiple languages. Pydub enables audio manipulation (speed adjustment, concatenation, silence insertion) with simple API.

**Architecture:**
1. Native language text generated at customizable speed (default 1.15×) using AudioSegment.speedup()
2. Foreign language text played at customizable speed (default 1.0×)
3. Customizable pause (default 3200ms) inserted between sentence pairs
4. All segments concatenated into single MP3 file

**Supported Languages:**
- Czech (cs)
- Spanish (es)
- German (de)

**Pros:** Free, no API quotas, cross-platform compatibility, multi-language support  
**Cons:** Requires ffmpeg dependency, limited voice customization

### Translation Service
**Decision:** OpenAI GPT-4o-mini API for multi-language translation  
**Rationale:** Provides high-quality contextual translations with simple API integration. Model selected for cost efficiency while maintaining translation quality.

**Implementation:**
- Dynamic prompt-based translation supporting any language pair
- Error handling with fallback messages
- Per-sentence translation with progress tracking
- Translation results are editable before audio generation

**Supported Translation Pairs:**
- Spanish ↔ Czech
- Spanish ↔ German
- Czech ↔ German
- Any combination of the supported languages

**Pros:** High translation quality, handles context and idioms well, supports multiple language pairs  
**Cons:** Requires API key and incurs costs, needs internet connectivity

### File Format Detection
**Decision:** Auto-detection with multi-delimiter support  
**Rationale:** Maximizes compatibility with various input formats while maintaining simplicity.

**Supported Formats:**
1. **Language pairs**: Any line containing tab, pipe, semicolon, or comma delimiter
   - Example: `Dobrý den|Buenos días` (Czech-Spanish)
   - Example: `Guten Tag;Dobrý den` (German-Czech)
2. **Foreign language only**: Lines without delimiters trigger automatic translation
   - Example: `Buenos días` (Spanish → will be translated to selected native language)

**Detection Logic:**
- Checks first line for presence of delimiters
- Validates that delimiter produces exactly 2 non-empty parts
- Falls back to foreign-language-only mode if no delimiter found
- First column is always native language, second is foreign language

### State Management
**Decision:** Content-based session state with MD5 hashing  
**Rationale:** Ensures UI reflects current uploaded files while preserving user edits between reruns.

**Implementation:**
- `content_hash`: MD5 of all_sentences detects content changes
- `current_sentences`: Stores parsed/translated sentence pairs
- `native_{i}`, `foreign_{i}`: Individual text input keys for editing (auto-cleared on new upload)
- Dynamic sentences_to_use construction from session state edits

**Features:**
- Progress bars for translation and audio generation phases
- Status text showing current processing step
- Automatic state refresh when files change
- Edit preservation during Streamlit reruns
- Language pair validation (prevents same language selection)

### Batch Processing
**Decision:** Multi-file upload with aggregation  
**Rationale:** Allows users to combine multiple files into single audio output.

**Implementation:**
- Accepts multiple .txt files via file_uploader
- Processes each file independently (parse → translate if needed)
- Aggregates all sentence pairs into single list
- Generates single MP3 containing all phrases

### File Handling
**Decision:** tempfile module for intermediate audio files  
**Rationale:** Ensures cleanup of temporary audio files during processing. Final output provided to user via Streamlit download button.

## External Dependencies

### Core Services
- **OpenAI API** - GPT-4o-mini model for multi-language translation
  - Requires: OPENAI_API_KEY environment variable
  - Usage: Chat completions endpoint for translation requests

### Python Libraries
- **streamlit** - Web application framework and UI components
- **gtts** (Google Text-to-Speech) - Speech synthesis for Czech, Spanish, and German
- **pydub** - Audio manipulation (speed control, concatenation, silence generation)
  - Requires: ffmpeg system dependency
- **openai** - Official OpenAI Python client library
- **hashlib** (built-in) - Content hashing for session state management

### System Dependencies
- **ffmpeg** - Required by pydub for audio format conversion and manipulation
- Temporary file system access for intermediate audio storage

### Configuration
- Environment variables: `OPENAI_API_KEY` (required for translation functionality)
- Configurable settings (via sidebar):
  - Native language selection (Czech, Spanish, German)
  - Foreign language selection (Czech, Spanish, German)
  - Native language speed: 1.0-1.5x (default: 1.15x)
  - Foreign language speed: 0.8-1.2x (default: 1.0x)
  - Pause duration: 1000-5000ms (default: 3200ms)

## Feature Documentation

### Language Selection
- Choose native language (the language you're learning)
- Choose foreign language (the language you already know as reference)
- System prevents selecting the same language for both
- All UI elements update dynamically based on language selection

### File Upload
- Accepts .txt files with UTF-8 encoding
- Supports single or multiple file upload
- Auto-detects format on a per-file basis
- Format guide shows examples for selected language pair

### Translation Editing
- First 20 phrase pairs are editable in the UI
- Remaining pairs (if > 20) are included in audio but not directly editable
- Edits are preserved across Streamlit reruns until new files are uploaded
- Translation applies to any supported language pair

### Audio Generation
- Creates MP3 with format: Native language (customizable speed) → Foreign language (customizable speed) → Pause
- Settings applied from sidebar at generation time
- Progress indicator shows current phrase being processed
- Final audio includes embedded playback and download button
- Filename includes language pair and phrase count

## Superlearning Method

The app implements the spaced repetition principle commonly used in language learning:
1. **Native language first** (played faster) - challenges the learner to recognize the new language
2. **Foreign language second** (reference) - provides confirmation and context
3. **Pause** - allows time for mental processing and repetition

Speed adjustments help optimize the learning process:
- **Native language speed up** (1.15x default) - helps train faster recognition
- **Foreign language speed** (1.0x default) - maintains natural reference pacing
- **Configurable pause** - adaptable to individual learning pace
