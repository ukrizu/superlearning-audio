# Spanish-Czech Audio Generator

## Overview

A Streamlit-based web application that generates bilingual audio files combining Czech and Spanish speech. The app supports file uploads in multiple formats, automatically translates Spanish to Czech using OpenAI's API, and creates MP3 files with alternating Czech-Spanish audio pairs with configurable pauses and speed settings.

**Updated:** October 29, 2025 - Added batch processing, customizable settings, translation editing, and multi-delimiter support.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

### October 29, 2025 - Enhanced Feature Set
1. **Multiple Delimiter Support**: Auto-detection of pipe (|), semicolon (;), comma (,), and tab delimiters
2. **Batch Processing**: Upload and process multiple files simultaneously
3. **Customizable Settings Sidebar**:
   - Adjustable pause duration (1000-5000ms, default: 3200ms)
   - Adjustable Czech playback speed (1.0-1.5x, default: 1.15x)
4. **Translation Preview & Editing**: View and edit Czech translations before audio generation (first 20 pairs)
5. **Improved Session State Management**: Content-based hashing ensures fresh data on file changes

## System Architecture

### Frontend Framework
**Decision:** Streamlit  
**Rationale:** Provides rapid development of interactive web interfaces with minimal boilerplate code. Ideal for data-focused applications with built-in progress indicators and file handling.

**Features:**
- Two-column layout with file upload and format guide
- Settings sidebar for real-time parameter adjustment
- Expandable preview/edit section for translations
- Audio playback and download capabilities

**Pros:** Simple deployment, built-in UI components, reactive state management  
**Cons:** Less customization than traditional web frameworks

### Audio Processing Pipeline
**Decision:** gTTS (Google Text-to-Speech) + pydub for audio manipulation  
**Rationale:** gTTS provides free, reliable text-to-speech conversion for multiple languages. Pydub enables audio manipulation (speed adjustment, concatenation, silence insertion) with simple API.

**Architecture:**
1. Czech text generated at customizable speed (default 1.15×) using AudioSegment.speedup()
2. Spanish text played at normal speed
3. Customizable pause (default 3200ms) inserted between sentence pairs
4. All segments concatenated into single MP3 file

**Pros:** Free, no API quotas, cross-platform compatibility  
**Cons:** Requires ffmpeg dependency, limited voice customization

### Translation Service
**Decision:** OpenAI GPT-4o-mini API for Spanish-to-Czech translation  
**Rationale:** Provides high-quality contextual translations with simple API integration. Model selected for cost efficiency while maintaining translation quality.

**Implementation:**
- Prompt-based translation with system role specifying output format
- Error handling with fallback messages
- Per-sentence translation with progress tracking
- Translation results are editable before audio generation

**Pros:** High translation quality, handles context and idioms well  
**Cons:** Requires API key and incurs costs, needs internet connectivity

### File Format Detection
**Decision:** Auto-detection with multi-delimiter support  
**Rationale:** Maximizes compatibility with various input formats while maintaining simplicity.

**Supported Formats:**
1. **Czech-Spanish pairs**: Any line containing tab, pipe, semicolon, or comma delimiter
   - Example: `Dobrý den|Buenos días`
2. **Spanish-only**: Lines without delimiters trigger automatic translation
   - Example: `Buenos días`

**Detection Logic:**
- Checks first line for presence of delimiters
- Validates that delimiter produces exactly 2 non-empty parts
- Falls back to Spanish-only mode if no delimiter found

### State Management
**Decision:** Content-based session state with MD5 hashing  
**Rationale:** Ensures UI reflects current uploaded files while preserving user edits between reruns.

**Implementation:**
- `content_hash`: MD5 of all_sentences detects content changes
- `current_sentences`: Stores parsed/translated sentence pairs
- `cz_{i}`, `es_{i}`: Individual text input keys for editing (auto-cleared on new upload)
- Dynamic sentences_to_use construction from session state edits

**Features:**
- Progress bars for translation and audio generation phases
- Status text showing current processing step
- Automatic state refresh when files change
- Edit preservation during Streamlit reruns

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
**Rationale:** Ensures cleanup of temporary Czech/Spanish MP3 files during processing. Final output provided to user via Streamlit download button.

## External Dependencies

### Core Services
- **OpenAI API** - GPT-4o-mini model for Spanish-to-Czech translation
  - Requires: OPENAI_API_KEY environment variable
  - Usage: Chat completions endpoint for translation requests

### Python Libraries
- **streamlit** - Web application framework and UI components
- **gtts** (Google Text-to-Speech) - Speech synthesis for Czech and Spanish
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
  - Pause duration: 1000-5000ms (default: 3200ms)
  - Czech speedup: 1.0-1.5x (default: 1.15x)

## Feature Documentation

### File Upload
- Accepts .txt files with UTF-8 encoding
- Supports single or multiple file upload
- Auto-detects format on a per-file basis

### Translation Editing
- First 20 phrase pairs are editable in the UI
- Remaining pairs (if > 20) are included in audio but not directly editable
- Edits are preserved across Streamlit reruns until new files are uploaded

### Audio Generation
- Creates MP3 with format: Czech (sped up) → Spanish (normal) → Pause
- Settings applied from sidebar at generation time
- Progress indicator shows current phrase being processed
- Final audio includes embedded playback and download button
